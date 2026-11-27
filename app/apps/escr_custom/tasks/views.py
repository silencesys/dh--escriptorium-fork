"""
My Tasks (/quotas/) and a task's page (/quotas/<pk>/).

Upstream's views, with templates of our own. My Tasks also gets a summary of
the last two weeks for the tiles above the list: tasks per day and how they
ended, CPU/GPU minutes per day, and what the disk usage is made of.

Users of the legacy UI keep upstream's templates, as our styles only load in
the new UI.
"""
from datetime import date, timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from reporting.models import TaskReport
from reporting.views import ReportDetail, ReportList

DAYS = 14
# a meter turns to a warning from this share of the limit
WARNING_AT = 80

# how a task ended, in the order the outcome bar shows them
OUTCOMES = (
    ('finished', _('Finished'), 'circle-check',
     (TaskReport.WORKFLOW_STATE_DONE,)),
    ('active', _('Running or queued'), 'loader-circle',
     (TaskReport.WORKFLOW_STATE_STARTED, TaskReport.WORKFLOW_STATE_QUEUED)),
    ('failed', _('Crashed'), 'circle-x',
     (TaskReport.WORKFLOW_STATE_ERROR,)),
    ('canceled', _('Canceled'), 'ban',
     (TaskReport.WORKFLOW_STATE_CANCELED,)),
)
OUTCOME_OF_STATE = {state: key for key, _label, _icon, states in OUTCOMES for state in states}
ICON_OF_STATE = {
    TaskReport.WORKFLOW_STATE_QUEUED: 'circle-dashed',
    TaskReport.WORKFLOW_STATE_STARTED: 'loader-circle',
    TaskReport.WORKFLOW_STATE_ERROR: 'circle-x',
    TaskReport.WORKFLOW_STATE_DONE: 'circle-check',
    TaskReport.WORKFLOW_STATE_CANCELED: 'ban',
}


def nice_axis(peak):
    """An axis top made of two equal, round steps that holds `peak`:
    (top, step)."""
    half = max(peak, 1) / 2
    magnitude = 1
    while True:
        for step in (1, 2, 5):
            if step * magnitude >= half:
                return step * magnitude * 2, step * magnitude
        magnitude *= 10


def percent(part, whole):
    return round(part * 100 / whole, 1) if whole else 0


def level(used_percentage):
    """How full a quota is: '', 'warning' or 'critical'."""
    if used_percentage is None:
        return ''
    if used_percentage >= 100:
        return 'critical'
    return 'warning' if used_percentage >= WARNING_AT else ''


def state_display(report):
    """A report's state as the list and the task page show it."""
    return {
        'key': OUTCOME_OF_STATE.get(report.workflow_state, 'canceled'),
        'icon': ICON_OF_STATE.get(report.workflow_state, 'circle-dashed'),
        'label': report.get_workflow_state_display(),
    }


class NewUITemplateMixin:
    """Our template for the new UI, upstream's for the legacy one."""
    upstream_template_name = None

    def legacy(self):
        return getattr(self.request.user, 'legacy_mode', False)

    def get_template_names(self):
        return [self.upstream_template_name if self.legacy() else self.template_name]


class MyTasks(NewUITemplateMixin, ReportList):
    template_name = 'escr_custom/tasks/my_tasks.html'
    upstream_template_name = 'reporting/taskreport_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.legacy():
            return context
        for report in context['object_list']:
            report.state = state_display(report)
        context.update(self.activity(context))
        context.update(self.disk(context))
        return context

    def activity(self, context):
        """The last DAYS days: tasks per day and how they ended (the tasks of
        the list), and CPU/GPU minutes per day (all tasks, like the quota)."""
        user = self.request.user
        today = timezone.localdate()
        days = [today - timedelta(days=n) for n in range(DAYS - 1, -1, -1)]
        # upstream's quota window (User.calc_cpu_usage)
        quota_since = date.today() - timedelta(days=7)

        keys = [key for key, *_rest in OUTCOMES]
        per_day = {day: dict.fromkeys(keys, 0) for day in days}
        rows = (self.get_queryset().order_by()
                .filter(queued_at__date__gte=days[0])
                .annotate(day=TruncDate('queued_at'))
                .values('day', 'workflow_state')
                .annotate(n=Count('id')))
        for row in rows:
            if row['day'] in per_day:
                per_day[row['day']][OUTCOME_OF_STATE.get(row['workflow_state'], 'canceled')] += row['n']

        usage = {row['day']: row for row in (
            TaskReport.objects.filter(user=user, started_at__date__gte=days[0]).order_by()
            .annotate(day=TruncDate('started_at'))
            .values('day')
            .annotate(cpu=Sum('cpu_cost'), gpu=Sum('gpu_cost')))}

        totals = {day: sum(counts.values()) for day, counts in per_day.items()}
        top, step = nice_axis(max(totals.values()))
        peak = {kind: max((usage.get(day, {}).get(kind) or 0) for day in days) for kind in ('cpu', 'gpu')}

        chart = []
        for day in days:
            cpu = usage.get(day, {}).get('cpu') or 0
            gpu = usage.get(day, {}).get('gpu') or 0
            chart.append({
                'date': day,
                'is_today': day == today,
                'total': totals[day],
                'breakdown': [{'key': key, 'label': label, 'count': per_day[day][key]}
                              for key, label, _icon, _states in OUTCOMES if per_day[day][key]],
                'height': percent(totals[day], top),
                'cpu': cpu,
                'gpu': gpu,
                'cpu_height': percent(cpu, peak['cpu']),
                'gpu_height': percent(gpu, peak['gpu']),
                'in_quota_window': day >= quota_since,
            })

        overall = {key: sum(per_day[day][key] for day in days) for key in keys}
        total = sum(overall.values())
        outcomes = [{
            'key': key, 'label': label, 'icon': icon,
            'count': overall[key], 'share': percent(overall[key], total),
        } for key, label, icon, _states in OUTCOMES]

        meters = []
        for kind, label, icon in (('cpu', _('CPU time'), 'cpu'), ('gpu', _('GPU time'), 'zap')):
            enforced = context[f'enforce_{kind}']
            used = context[f'{kind}_minutes_used_percentage'] if enforced else None
            meters.append({
                'kind': kind,
                'label': label,
                'icon': icon,
                'value': context[f'{kind}_cost_last_week'],
                'enforced': enforced,
                'limit': getattr(user, f'{kind}_minutes_limit')() if enforced else None,
                'used_percentage': used,
                'level': level(used),
                'bars': [{'date': d['date'], 'value': d[kind], 'height': d[f'{kind}_height'],
                          'in_quota_window': d['in_quota_window']} for d in chart],
                'any': peak[kind] > 0,
            })

        return {
            'chart': chart,
            'chart_top': top,
            'chart_ticks': [top, step, 0],
            'chart_total': total,
            'outcomes': outcomes,
            'usage_meters': meters,
            'quota_since': quota_since,
            'days': DAYS,
        }

    def disk(self, context):
        """What the disk usage is made of (User.calc_disk_usage, in parts)."""
        user = self.request.user
        models = user.ocrmodel_set.aggregate(size=Sum('file_size'))['size'] or 0
        images = user.document_set.aggregate(size=Sum('parts__image_file_size'))['size'] or 0
        total = images + models
        enforced = context['enforce_disk_storage']
        limit = user.disk_storage_limit() if enforced else None
        whole = limit if enforced else total
        used = context['disk_storage_used_percentage'] if enforced else None
        return {'disk': {
            'total': total,
            'limit': limit,
            'enforced': enforced,
            'used_percentage': used,
            'level': level(used),
            'parts': [
                {'key': 'images', 'label': _('Images'), 'size': images,
                 'share': min(percent(images, whole), 100)},
                {'key': 'models', 'label': _('Models'), 'size': models,
                 'share': min(percent(models, whole), 100)},
            ],
        }}


class TaskDetail(NewUITemplateMixin, ReportDetail):
    template_name = 'escr_custom/tasks/task_detail.html'
    upstream_template_name = 'reporting/taskreport_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = context['report']
        report.state = state_display(report)
        if report.started_at:
            context['waited'] = report.started_at - report.queued_at
            if report.done_at:
                context['ran'] = report.done_at - report.started_at
        return context
