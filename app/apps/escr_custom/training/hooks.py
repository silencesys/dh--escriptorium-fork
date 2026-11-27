"""
Applies a training's options inside upstream's training tasks, without
changing them.

Our API queues upstream's own task with one more keyword argument,
`training_options`, which the task accepts and ignores (it takes **kwargs).
In the worker, a Celery signal picks the options up before the task runs and
drops them after. While they are set, the names upstream's training code looks
up in core.tasks at run time are wrapped:

- recognition_training_classes / segmentation_training_classes: the config
  classes they return are replaced by factories that add our settings, and a
  recognition model trained from scratch can get another architecture;
- recognition_batch_size: follows that architecture;
- KrakenTrainer: gets the epoch limits and the backbone freezing.

The wrapped names behave exactly like the originals when no options are set.
If upstream renames any of them, nothing is wrapped, an error is logged and
our API refuses options (see `available()`), so training keeps working the
upstream way.
"""
import logging

from celery.signals import task_postrun, task_prerun

from .options import RECOGNITION, SEGMENTATION, split

logger = logging.getLogger(__name__)

OPTIONS_KWARG = 'training_options'
TRAINING_TASKS = {
    'core.tasks.train': RECOGNITION,
    'core.tasks.train_from_collection': RECOGNITION,
    'core.tasks.segtrain': SEGMENTATION,
    'core.tasks.segtrain_from_collection': SEGMENTATION,
}
SEAMS = (
    'recognition_training_classes',
    'segmentation_training_classes',
    'recognition_batch_size',
    'KrakenTrainer',
)

# the running training's options (a worker process runs one task at a time)
_current = {'options': None, 'architecture': None}
_installed = {'ok': False}


def available():
    """True when the hooks are in place, so options will take effect."""
    return _installed['ok']


def current():
    return _current['options']


# ---- the wrapped names ---------------------------------------------------

def _with(config_class, settings):
    """A stand-in for a kraken config class that adds our settings."""
    if not settings:
        return config_class

    def make(*args, **kwargs):
        kwargs.update(settings)
        return config_class(*args, **kwargs)
    # still an instance of kraken's own class, so checkpoints pickle as usual
    make.__wrapped__ = config_class
    return make


def _for_config(config_class, named, extra):
    """Our settings for one config class: the named ones, and the extra ones
    the class actually has."""
    if not (named or extra):
        return config_class
    known = vars(config_class())
    return _with(config_class, {**named, **{k: v for k, v in extra.items() if k in known}})


def _wrap_classes(original, job):
    def training_classes(architecture):
        options = current()
        if not options or options['job'] != job:
            return original(architecture)
        if architecture is None and options['architecture']:
            architecture = options['architecture']
        _current['architecture'] = architecture
        train_config_class, data_config_class, *rest = original(architecture)
        return (
            _for_config(train_config_class, options['config'], options['extra']),
            _for_config(data_config_class, options['data'], options['extra']),
            *rest,
        )
    training_classes.__wrapped__ = original
    return training_classes


def _wrap_batch_size(original):
    def batch_size(architecture):
        options = current()
        if options and architecture is None and options['architecture']:
            architecture = options['architecture']
        return original(architecture)
    batch_size.__wrapped__ = original
    return batch_size


def _wrap_trainer(original):
    def trainer(*args, **kwargs):
        options = current()
        if options:
            settings = dict(options['trainer'])
            # kraken freezes all but the last layer of `net`, which only VGSL
            # recognition models have
            if 'freeze_backbone' in settings and _current['architecture'] not in (None, 'TorchVGSLModel'):
                logger.info('Not freezing the backbone: %s has none to freeze', _current['architecture'])
                settings.pop('freeze_backbone')
            kwargs.update(settings)
            logger.info('Training with options %s', {k: v for k, v in options.items() if v})
        return original(*args, **kwargs)
    trainer.__wrapped__ = original
    return trainer


# ---- the task's options --------------------------------------------------

@task_prerun.connect
def _start(sender=None, task=None, kwargs=None, **_):
    name = getattr(task, 'name', None)
    if name not in TRAINING_TASKS or not available():
        return
    options = (kwargs or {}).get(OPTIONS_KWARG)
    if options:
        _current['options'] = {**split(options), 'job': TRAINING_TASKS[name]}
        _current['architecture'] = None


@task_postrun.connect
def _end(sender=None, task=None, **_):
    if getattr(task, 'name', None) in TRAINING_TASKS:
        _current['options'] = None
        _current['architecture'] = None


def install():
    """Wrap upstream's names, once per process."""
    if _installed['ok']:
        return
    from core import tasks
    missing = [name for name in SEAMS if not hasattr(tasks, name)]
    if missing:
        logger.error('Training options are off: core.tasks no longer has %s', ', '.join(missing))
        return
    tasks.recognition_training_classes = _wrap_classes(tasks.recognition_training_classes, RECOGNITION)
    tasks.segmentation_training_classes = _wrap_classes(tasks.segmentation_training_classes, SEGMENTATION)
    tasks.recognition_batch_size = _wrap_batch_size(tasks.recognition_batch_size)
    tasks.KrakenTrainer = _wrap_trainer(tasks.KrakenTrainer)
    _installed['ok'] = True
