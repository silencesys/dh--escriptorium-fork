"""
Training settings a user may choose, on top of what upstream's training
tasks use (kraken's defaults, plus what the tasks set themselves).

Only what the user actually sets is passed on: anything left out keeps the
default of the architecture being trained (PP-OCR, for one, has defaults of
its own, such as a 1000 step warmup), so an empty set of options trains
exactly like upstream does.

Settings that size the job for the server (device, batch size, precision,
threads, data loading) stay with the administrator and are refused here.
"""
from rest_framework import serializers

RECOGNITION = 'recognition'
SEGMENTATION = 'segmentation'

SCHEDULES = ['constant', 'cosine', 'reduceonplateau', '1cycle', 'exponential', 'step']
OPTIMIZERS = ['AdamW', 'Adam', 'SGD', 'RMSprop']
NORMALIZATIONS = ['NFC', 'NFD', 'NFKC', 'NFKD']
# recognition architectures for a model trained from scratch (a base model
# brings its own); values are the names upstream's tasks use for them
ARCHITECTURES = {
    'vgsl': 'TorchVGSLModel',
    'ppocrv6': 'PPOCRv6Model',
}

# options for kraken's training config
CONFIG_FIELDS = [
    'epochs', 'min_epochs', 'quit', 'lag', 'min_delta',
    'optimizer', 'lrate', 'momentum', 'weight_decay', 'gradient_clip_val',
    'accumulate_grad_batches',
    'schedule', 'warmup', 'step_size', 'gamma', 'rop_factor', 'rop_patience',
    'cos_t_max', 'cos_min_lr',
]
# options for kraken's training data config
DATA_FIELDS = ['augment', 'normalization']

# ketos's names for config fields, so `ketos train` options can be pasted
KETOS_ALIASES = {
    'sched_patience': 'rop_patience',
    'cos_max': 'cos_t_max',
    'N': 'epochs',
    'r': 'lrate',
    'q': 'quit',
    'g': 'gamma',
    'pad': 'padding',
    'reorder': 'bidi_reordering',
    'arch': 'architecture',
}

# config fields "extra" may not set: they size the job for the server, or the
# training task sets them from the data
BLOCKED_EXTRA = {
    'accelerator', 'device', 'precision', 'batch_size', 'num_threads',
    'num_workers', 'compile_config', 'raise_on_error',
    'checkpoint_path', 'weights_format', 'completed_epochs', 'freq',
    'resize', 'topline', 'padding', 'legacy_polygons', 'linetype',
    'training_data', 'evaluation_data', 'test_data', 'format_type',
    'binary_dataset_split', 'partition', 'codec', 'bidi_reordering',
}


class TrainingOptionsSerializer(serializers.Serializer):
    """
    Validates the options of one training. The context carries `job`
    (RECOGNITION or SEGMENTATION) and `has_base_model`.
    """
    # how long
    epochs = serializers.IntegerField(required=False, min_value=1, max_value=1000)
    min_epochs = serializers.IntegerField(required=False, min_value=0, max_value=1000)
    quit = serializers.ChoiceField(required=False, choices=['early', 'fixed'])
    lag = serializers.IntegerField(required=False, min_value=1, max_value=200)
    min_delta = serializers.FloatField(required=False, min_value=0, max_value=1)
    # optimizer
    optimizer = serializers.ChoiceField(required=False, choices=OPTIMIZERS)
    lrate = serializers.FloatField(required=False, min_value=1e-8, max_value=1)
    momentum = serializers.FloatField(required=False, min_value=0, max_value=1)
    weight_decay = serializers.FloatField(required=False, min_value=0, max_value=1)
    gradient_clip_val = serializers.FloatField(required=False, min_value=0, max_value=100)
    accumulate_grad_batches = serializers.IntegerField(required=False, min_value=1, max_value=256)
    # learning rate schedule
    schedule = serializers.ChoiceField(required=False, choices=SCHEDULES)
    warmup = serializers.IntegerField(required=False, min_value=0, max_value=1_000_000)
    step_size = serializers.IntegerField(required=False, min_value=1, max_value=1000)
    gamma = serializers.FloatField(required=False, min_value=0, max_value=1)
    rop_factor = serializers.FloatField(required=False, min_value=0, max_value=1)
    rop_patience = serializers.IntegerField(required=False, min_value=1, max_value=200)
    cos_t_max = serializers.IntegerField(required=False, min_value=1, max_value=1000)
    cos_min_lr = serializers.FloatField(required=False, min_value=0, max_value=1)
    # data
    augment = serializers.BooleanField(required=False)
    normalization = serializers.ChoiceField(required=False, choices=NORMALIZATIONS)
    # recognition only
    freeze_backbone = serializers.IntegerField(required=False, min_value=0, max_value=1_000_000)
    architecture = serializers.ChoiceField(required=False, choices=list(ARCHITECTURES))
    # any other field of kraken's configs, as {name: value}
    extra = serializers.DictField(required=False)

    def to_internal_value(self, data):
        """Settings typed among the extra ones (in kraken's or ketos's
        spelling) that have a field of their own are validated as that field."""
        data = dict(data)
        extra = data.get('extra')
        if isinstance(extra, dict):
            rest = {}
            for key, value in extra.items():
                key = KETOS_ALIASES.get(key.replace('-', '_'), key.replace('-', '_'))
                if key.startswith('no_') and value in (True, '', 'true'):
                    key, value = key[3:], False
                elif value == '':
                    value = True  # a bare flag, such as --augment
                if key in self.fields and key != 'extra':
                    data.setdefault(key, value)
                else:
                    rest[key] = value
            data['extra'] = rest
        return super().to_internal_value(data)

    def validate(self, data):
        job = self.context.get('job', RECOGNITION)
        has_base_model = self.context.get('has_base_model', False)
        epochs, min_epochs = data.get('epochs'), data.get('min_epochs')
        if epochs is not None and min_epochs is not None and min_epochs > epochs:
            raise serializers.ValidationError(
                {'min_epochs': 'Must not be more than the maximum number of epochs.'})
        if job != RECOGNITION:
            for field in ('freeze_backbone', 'architecture'):
                if field in data:
                    raise serializers.ValidationError(
                        {field: 'Only for recognition training.'})
        if data.get('freeze_backbone') and not has_base_model:
            raise serializers.ValidationError(
                {'freeze_backbone': 'Only when fine-tuning a base model.'})
        if 'architecture' in data and has_base_model:
            raise serializers.ValidationError(
                {'architecture': 'A base model brings its own architecture: '
                                 'leave this out when fine-tuning.'})
        extra = self._validate_extra(data.pop('extra', None) or {})
        if extra:
            data['extra'] = extra
        return data

    def _validate_extra(self, extra):
        """Other settings of kraken's configs, typed like their defaults."""
        defaults = all_defaults(self.context.get('job', RECOGNITION))
        errors, cleaned = {}, {}
        for key, value in extra.items():
            if key in BLOCKED_EXTRA:
                errors[key] = 'Set by the server, not per training.'
            elif key not in defaults:
                errors[key] = 'Not a training setting of this model type.'
            else:
                try:
                    cleaned[key] = coerce(value, defaults[key])
                except (TypeError, ValueError):
                    errors[key] = f'Expected a value like {defaults[key]!r}.'
        if 'spec' in cleaned and self.context.get('has_base_model'):
            errors['spec'] = 'Only for a model trained from scratch.'
        if errors:
            raise serializers.ValidationError({'extra': errors})
        return cleaned

def coerce(value, default):
    """A value from the form ("10", "true", ...) as the type of the default."""
    if isinstance(default, bool):
        if isinstance(value, str):
            if value.strip().lower() in ('true', '1', 'yes', 'on'):
                return True
            if value.strip().lower() in ('false', '0', 'no', 'off'):
                return False
            raise ValueError(value)
        return bool(value)
    if isinstance(default, int):
        if isinstance(value, float) and not value.is_integer():
            raise ValueError(value)
        return int(value)
    if isinstance(default, float):
        return float(value)
    if isinstance(value, (bool, int, float, str)):
        return value
    raise TypeError(value)


def all_defaults(job):
    """The settings of every architecture of a job, merged: a base model's
    architecture is only known in the worker, which applies to each config
    just the settings it has."""
    from core import tasks
    if job == RECOGNITION:
        architectures = list(ARCHITECTURES.values())
    else:
        architectures = [None, *getattr(tasks, 'SEGMENTATION_TRAINING_CLASSES', {})]
    merged = {}
    for architecture in architectures:
        train, data = kraken_defaults(job, architecture)
        merged.update(data)
        merged.update(train)
    return merged


def kraken_defaults(job, architecture=None):
    """
    The default settings of kraken's training config and data config for a
    job, as upstream's tasks pick them for an architecture (None: training
    from scratch). Only plain values, for display and validation.
    """
    from core import tasks
    pick = (tasks.recognition_training_classes if job == RECOGNITION
            else tasks.segmentation_training_classes)
    train_config_class, data_config_class, *_ = pick(architecture)

    def plain(obj):
        return {k: v for k, v in vars(obj).items()
                if not k.startswith('_') and (v is None or isinstance(v, (bool, int, float, str)))}

    return plain(train_config_class()), plain(data_config_class())

def split(options):
    """
    Split validated options into what goes to kraken's training config, its
    data config and the trainer, the architecture to train from scratch, and
    the extra settings (applied to whichever config has them).
    """
    options = dict(options or {})
    extra = options.pop('extra', None) or {}
    trainer = {}
    if options.get('epochs') is not None:
        trainer['max_epochs'] = options['epochs']
    if options.get('min_epochs') is not None:
        trainer['min_epochs'] = options['min_epochs']
    if options.get('freeze_backbone'):
        trainer['freeze_backbone'] = options['freeze_backbone']
    return {
        'config': {k: options[k] for k in CONFIG_FIELDS if k in options},
        'data': {k: options[k] for k in DATA_FIELDS if k in options},
        'extra': extra,
        'trainer': trainer,
        'architecture': ARCHITECTURES.get(options.get('architecture')),
    }
