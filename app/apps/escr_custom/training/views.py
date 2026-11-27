"""
Training a model on a collection with options: upstream's collection
training endpoints (api/views.py, VirtualCollectionViewSet.train_recognizer
and train_segmenter), plus the options, which travel with upstream's own
task to the worker (see hooks.py).
"""
import inspect

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import CollectionRecognizeSerializer, CollectionSegmentSerializer
from core import tasks
from core.models import VirtualCollection
from core.permissions import user_can_train

from . import hooks
from .options import (
    ARCHITECTURES,
    NORMALIZATIONS,
    OPTIMIZERS,
    RECOGNITION,
    SCHEDULES,
    SEGMENTATION,
    TrainingOptionsSerializer,
    kraken_defaults,
)

JOBS = {
    RECOGNITION: (CollectionRecognizeSerializer, 'train_from_collection'),
    SEGMENTATION: (CollectionSegmentSerializer, 'segtrain_from_collection'),
}


def _trainer_defaults():
    trainer = getattr(tasks.KrakenTrainer, '__wrapped__', tasks.KrakenTrainer)
    params = inspect.signature(trainer.__init__).parameters
    return {name: params[name].default for name in ('min_epochs', 'max_epochs') if name in params}


def _effective_defaults(job, architecture=None):
    """What a training without options uses: kraken's defaults, with what
    upstream's tasks set themselves."""
    train, data = kraken_defaults(job, architecture)
    if job == RECOGNITION:
        # upstream gives the trainer no epoch limits: the trainer's own apply
        trainer = _trainer_defaults()
        epochs = trainer.get('max_epochs')
        min_epochs = trainer.get('min_epochs')
    else:
        # upstream passes the config's limits to the trainer, and stops early
        epochs, min_epochs = train['epochs'], train['min_epochs']
        train = {**train, 'quit': 'early'}
    return {
        **{k: v for k, v in train.items() if k != 'spec'},
        'epochs': epochs,
        'min_epochs': min_epochs,
        'augment': data.get('augment'),
        'normalization': data.get('normalization'),
    }


class TrainingInfoView(APIView):
    """What can be set, and the defaults a training without options uses."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'available': hooks.available(),
            'device': getattr(settings, 'KRAKEN_TRAINING_DEVICE', 'cpu'),
            'choices': {
                'schedule': SCHEDULES,
                'optimizer': OPTIMIZERS,
                'normalization': NORMALIZATIONS,
                'architecture': list(ARCHITECTURES),
            },
            'defaults': {
                RECOGNITION: {
                    name: _effective_defaults(RECOGNITION, arch)
                    for name, arch in ARCHITECTURES.items()
                },
                SEGMENTATION: {'blla': _effective_defaults(SEGMENTATION)},
            },
        })


class CollectionTrainingView(APIView):
    permission_classes = [IsAuthenticated]
    job = RECOGNITION

    def post(self, request, pk=None):
        if not user_can_train(request.user):
            raise PermissionDenied('You are not allowed to train models.')
        if not hooks.available():
            return Response({'options': ['Training options are not available on this server.']},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        collection = get_object_or_404(VirtualCollection.objects.filter(owner=request.user), pk=pk)
        data = {k: v for k, v in request.data.items() if k != 'options'}

        # the options first, so nothing is created for a refused request
        options = TrainingOptionsSerializer(
            data=request.data.get('options') or {},
            context={'job': self.job, 'has_base_model': bool(data.get('model'))},
        )
        if not options.is_valid():
            return Response({'options': options.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer_class, task_name = JOBS[self.job]
        serializer = serializer_class(data=data, context={'request': request, 'collection': collection})
        serializer.is_valid(raise_exception=True)
        serializer.process()
        getattr(tasks, task_name).delay(
            model_pk=serializer.model.pk,
            collection_pk=collection.pk,
            task_group_pk=serializer.task_group.pk,
            user_pk=request.user.pk,
            **{hooks.OPTIONS_KWARG: options.validated_data},
        )
        return Response({'status': 'training queued', 'model_id': serializer.model.pk})
