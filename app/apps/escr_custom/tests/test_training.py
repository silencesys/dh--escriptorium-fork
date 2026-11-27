"""
Run with our settings:

    DJANGO_SETTINGS_MODULE=apps.escr_custom.settings python manage.py test escr_custom
"""
from unittest import mock

from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from core import tasks
from core.models import VirtualCollection
from core.tests.factory import CoreFactoryTestCase
from escr_custom.training import hooks
from reporting.models import TaskGroup
from escr_custom.training.options import TrainingOptionsSerializer, split


class _Task:
    name = 'core.tasks.train_from_collection'


class _SegTask:
    name = 'core.tasks.segtrain_from_collection'


def validate(data, job='recognition', has_base_model=False):
    serializer = TrainingOptionsSerializer(
        data=data, context={'job': job, 'has_base_model': has_base_model})
    return serializer.is_valid(), serializer


class UpstreamSeamsTestCase(SimpleTestCase):
    """Fails when upstream renames what the hooks wrap: check hooks.py."""

    def test_seams_exist_and_are_wrapped(self):
        self.assertTrue(hooks.available())
        for name in hooks.SEAMS:
            self.assertTrue(hasattr(getattr(tasks, name), '__wrapped__'), name)

    def test_training_tasks_take_extra_kwargs(self):
        import inspect
        for name in ('train_from_collection', 'segtrain_from_collection'):
            params = inspect.signature(getattr(tasks, name).run).parameters.values()
            self.assertTrue(any(p.kind is p.VAR_KEYWORD for p in params), name)


class OptionsTestCase(SimpleTestCase):

    def test_empty_options_are_valid_and_change_nothing(self):
        ok, serializer = validate({})
        self.assertTrue(ok)
        parts = split(serializer.validated_data)
        self.assertEqual(parts['config'], {})
        self.assertEqual(parts['trainer'], {})
        self.assertIsNone(parts['architecture'])

    def test_server_settings_are_refused(self):
        for key in ('device', 'precision', 'num_workers'):
            ok, serializer = validate({'extra': {key: 1}})
            self.assertFalse(ok, key)

    @override_settings(KRAKEN_TRAINING_BATCH_SIZE_MAX=32)
    def test_batch_size(self):
        ok, serializer = validate({'batch_size': 8})
        self.assertTrue(ok, serializer.errors)
        self.assertEqual(split(serializer.validated_data)['batch_size'], 8)
        # ketos's spelling, among the other settings
        ok, serializer = validate({'extra': {'B': '16'}})
        self.assertTrue(ok, serializer.errors)
        self.assertEqual(serializer.validated_data['batch_size'], 16)
        # up to the server's limit, recognition only
        self.assertFalse(validate({'batch_size': 33})[0])
        self.assertFalse(validate({'batch_size': 0})[0])
        self.assertFalse(validate({'batch_size': 8}, job='segmentation')[0])

    def test_unknown_extra_is_refused(self):
        ok, _ = validate({'extra': {'not_a_setting': 1}})
        self.assertFalse(ok)

    def test_named_settings_typed_as_extra(self):
        ok, serializer = validate({'extra': {'rop_patience': '7', 'momentum': '0.5'}})
        self.assertTrue(ok, serializer.errors)
        self.assertEqual(serializer.validated_data, {'rop_patience': 7, 'momentum': 0.5})

    def test_ketos_options(self):
        ok, serializer = validate({'extra': {
            'sched-patience': '10', 'augment': '', 'arch': 'ppocrv6', 'variant': 'tiny', 'height': '64',
        }})
        self.assertTrue(ok, serializer.errors)
        self.assertEqual(serializer.validated_data, {
            'rop_patience': 10, 'augment': True, 'architecture': 'ppocrv6',
            'extra': {'variant': 'tiny', 'height': 64},
        })

    def test_extra_values_take_the_defaults_type(self):
        ok, serializer = validate({'extra': {'normalize_whitespace': 'false'}})
        self.assertTrue(ok, serializer.errors)
        self.assertEqual(serializer.validated_data['extra'], {'normalize_whitespace': False})

    def test_min_epochs_above_epochs_is_refused(self):
        ok, _ = validate({'epochs': 5, 'min_epochs': 10})
        self.assertFalse(ok)

    def test_recognition_only_options(self):
        self.assertFalse(validate({'architecture': 'ppocrv6'}, job='segmentation')[0])
        self.assertFalse(validate({'freeze_backbone': 10}, has_base_model=False)[0])
        self.assertTrue(validate({'freeze_backbone': 10}, has_base_model=True)[0])
        self.assertFalse(validate({'architecture': 'ppocrv6'}, has_base_model=True)[0])


class HooksTestCase(SimpleTestCase):

    def tearDown(self):
        hooks._end(task=_Task)

    def run_with(self, options, task=_Task):
        hooks._start(task=task, kwargs={hooks.OPTIONS_KWARG: options})

    def test_without_options_upstream_classes_are_returned(self):
        original = tasks.recognition_training_classes.__wrapped__(None)
        self.assertEqual(tasks.recognition_training_classes(None), original)

    def test_options_reach_the_configs(self):
        ok, serializer = validate({
            'epochs': 20, 'warmup': 100, 'schedule': 'reduceonplateau',
            'augment': True, 'extra': {'rop_patience': 3, 'normalize_whitespace': False},
        })
        self.assertTrue(ok, serializer.errors)
        self.run_with(serializer.validated_data)
        config_class, data_class, *_ = tasks.recognition_training_classes(None)
        config, data = config_class(), data_class()
        self.assertEqual((config.epochs, config.warmup, config.schedule, config.rop_patience),
                         (20, 100, 'reduceonplateau', 3))
        self.assertTrue(data.augment)
        self.assertFalse(data.normalize_whitespace)

    def test_extra_only_goes_to_configs_that_have_it(self):
        self.run_with({'architecture': 'ppocrv6', 'extra': {'variant': 'tiny', 'max_width': 1000}})
        config_class, data_class, *_ = tasks.recognition_training_classes(None)
        self.assertEqual(config_class().variant, 'tiny')
        self.assertEqual(data_class().max_width, 1000)
        self.assertFalse(hasattr(config_class(), 'max_width'))

    def test_options_win_over_the_tasks_own_arguments(self):
        # segmentation training passes quit='early' itself
        self.run_with({'quit': 'fixed'}, task=_SegTask)
        config_class = tasks.segmentation_training_classes(None)[0]
        self.assertEqual(config_class(quit='early').quit, 'fixed')
        hooks._end(task=_SegTask)

    def test_architecture_from_scratch(self):
        self.run_with({'architecture': 'ppocrv6'})
        config_class = tasks.recognition_training_classes(None)[0]
        self.assertEqual(type(config_class()).__name__, 'PPOCRv6RecognitionTrainingConfig')
        # a base model's own architecture is kept
        config_class = tasks.recognition_training_classes('TorchVGSLModel')[0]
        self.assertEqual(type(config_class()).__name__, 'VGSLRecognitionTrainingConfig')

    def test_trainer_gets_epochs_and_freezing(self):
        self.run_with({'epochs': 12, 'min_epochs': 2, 'freeze_backbone': 300})
        tasks.recognition_training_classes('TorchVGSLModel')
        trainer = mock.Mock()
        hooks._wrap_trainer(trainer)(accelerator='cpu')
        trainer.assert_called_once_with(accelerator='cpu', max_epochs=12, min_epochs=2, freeze_backbone=300)

    @override_settings(KRAKEN_TRAINING_BATCH_SIZE=1, KRAKEN_TRAINING_BATCH_SIZE_PPOCR=None,
                       KRAKEN_TRAINING_BATCH_SIZE_VGSL=None)
    def test_ppocr_keeps_its_own_batch_size(self):
        # the general setting is for VGSL; PP-OCR falls back to kraken's default
        self.assertEqual(tasks.recognition_batch_size('TorchVGSLModel'), 1)
        self.assertEqual(tasks.recognition_batch_size(None), 1)
        self.assertIsNone(tasks.recognition_batch_size('PPOCRv6Model'))
        config_class = tasks.recognition_training_classes('PPOCRv6Model')[0]
        self.assertEqual(config_class().batch_size, 64)
        # trained from scratch with the PP-OCR architecture
        self.run_with({'architecture': 'ppocrv6'})
        self.assertIsNone(tasks.recognition_batch_size(None))
        # its own setting still sizes it
        with self.settings(KRAKEN_TRAINING_BATCH_SIZE_PPOCR=16):
            self.assertEqual(tasks.recognition_batch_size('PPOCRv6Model'), 16)

    def test_chosen_batch_size_wins(self):
        self.run_with({'batch_size': 4})
        self.assertEqual(tasks.recognition_batch_size('TorchVGSLModel'), 4)
        self.assertEqual(tasks.recognition_batch_size('PPOCRv6Model'), 4)

    def test_vgsl_trains_in_batches_of_eight(self):
        # our settings' default, unless the variable sets another
        self.assertEqual(tasks.recognition_batch_size('TorchVGSLModel'), 8)
        self.assertEqual(tasks.recognition_batch_size(None), 8)
        with self.settings(KRAKEN_TRAINING_BATCH_SIZE_VGSL=4):
            self.assertEqual(tasks.recognition_batch_size(None), 4)

    def test_other_tasks_are_left_alone(self):
        class Other:
            name = 'core.tasks.transcribe'
        hooks._start(task=Other, kwargs={hooks.OPTIONS_KWARG: {'epochs': 3}})
        self.assertIsNone(hooks.current())


@override_settings(DISABLE_QUOTAS=True)
class ApiTestCase(CoreFactoryTestCase):

    def setUp(self):
        super().setUp()
        self.user = self.factory.make_user()
        self.user.is_superuser = True
        self.user.save()
        self.client.force_login(self.user)
        self.collection = VirtualCollection.objects.create(owner=self.user, name='c')
        self.url = reverse('custom-collection-train-recognizer', args=[self.collection.pk])

    def test_info(self):
        response = self.client.get(reverse('custom-training-info'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['available'])
        self.assertIn('vgsl', response.json()['defaults']['recognition'])
        self.assertEqual(response.json()['defaults']['recognition']['vgsl']['batch_size'], 8)
        self.assertEqual(response.json()['defaults']['recognition']['ppocrv6']['batch_size'], 64)
        self.assertGreaterEqual(response.json()['limits']['batch_size'], 8)

    def test_refused_options_create_nothing(self):
        response = self.client.post(self.url, {'model_name': 'm', 'options': {'epochs': 0}},
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(TaskGroup.objects.filter(collection=self.collection).exists())

    def test_options_travel_with_the_task(self):
        with mock.patch.object(tasks.train_from_collection, 'delay') as delay:
            response = self.client.post(self.url, {'model_name': 'm', 'options': {'epochs': 7}},
                                        content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(delay.call_args.kwargs[hooks.OPTIONS_KWARG], {'epochs': 7})

    def test_someone_elses_collection(self):
        other = self.factory.make_user()
        other.is_superuser = True
        other.save()
        self.client.force_login(other)
        response = self.client.post(self.url, {'model_name': 'm'}, content_type='application/json')
        self.assertEqual(response.status_code, 404)
