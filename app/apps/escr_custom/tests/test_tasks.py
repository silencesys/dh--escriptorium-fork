"""
My Tasks and a task's page (escr_custom.tasks). Run with our settings:

    DJANGO_SETTINGS_MODULE=apps.escr_custom.settings python manage.py test escr_custom
"""
from datetime import timedelta

from django.template.loader import get_template
from django.test import SimpleTestCase
from django.urls import resolve, reverse
from django.utils import timezone

from core.tests.factory import CoreFactoryTestCase
from escr_custom.tasks.views import DAYS, MyTasks, TaskDetail, nice_axis
from escr_custom.templatetags.escr_ui import icon, minutes
from reporting import views as upstream
from reporting.models import TaskReport


class UpstreamSeamsTestCase(SimpleTestCase):
    """Fails when upstream moves what our pages build on."""

    def test_our_views_take_upstreams_urls(self):
        self.assertIs(resolve('/quotas/').func.view_class, MyTasks)
        self.assertIs(resolve('/quotas/1/').func.view_class, TaskDetail)
        self.assertEqual(reverse('report-list'), '/quotas/')
        self.assertEqual(reverse('report-detail', kwargs={'pk': 1}), '/quotas/1/')

    def test_upstream_views_and_templates_exist(self):
        self.assertTrue(issubclass(MyTasks, upstream.ReportList))
        self.assertTrue(issubclass(TaskDetail, upstream.ReportDetail))
        for view in (MyTasks, TaskDetail):
            get_template(view.template_name)
            get_template(view.upstream_template_name)


class HelpersTestCase(SimpleTestCase):

    def test_nice_axis(self):
        self.assertEqual(nice_axis(0), (2, 1))
        self.assertEqual(nice_axis(3), (4, 2))
        self.assertEqual(nice_axis(6), (10, 5))
        self.assertEqual(nice_axis(14), (20, 10))
        self.assertEqual(nice_axis(150), (200, 100))

    def test_minutes(self):
        self.assertEqual(minutes(None), '0')
        self.assertEqual(minutes(0.001), '<0.01')
        self.assertEqual(minutes(1.234), '1.23')
        self.assertEqual(minutes(12.34), '12.3')
        self.assertEqual(minutes(1234.5), '1,234')

    def test_icon(self):
        self.assertIn('aria-hidden="true"', icon('cpu', 14))
        self.assertIn('width="14"', icon('cpu', 14))


class MyTasksTestCase(CoreFactoryTestCase):

    def setUp(self):
        super().setUp()
        self.user = self.factory.make_user()
        self.client.force_login(self.user)

    def report(self, state, days_ago=0, method='core.tasks.segment', **kwargs):
        when = timezone.now() - timedelta(days=days_ago)
        report = TaskReport.objects.create(
            user=self.user, label='A task', method=method, workflow_state=state,
            started_at=when, cpu_cost=kwargs.pop('cpu_cost', 1), **kwargs)
        TaskReport.objects.filter(pk=report.pk).update(queued_at=when)
        return report

    def test_summary(self):
        self.report(TaskReport.WORKFLOW_STATE_DONE)
        self.report(TaskReport.WORKFLOW_STATE_DONE, days_ago=1)
        self.report(TaskReport.WORKFLOW_STATE_ERROR, days_ago=1)
        self.report(TaskReport.WORKFLOW_STATE_STARTED)
        # not in the list (upstream leaves these out), but in the CPU time
        self.report(TaskReport.WORKFLOW_STATE_DONE, method='core.tasks.convert', cpu_cost=5)
        # too old for the chart
        self.report(TaskReport.WORKFLOW_STATE_DONE, days_ago=DAYS + 2)

        response = self.client.get(reverse('report-list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, MyTasks.template_name)
        context = response.context

        chart = context['chart']
        self.assertEqual(len(chart), DAYS)
        self.assertTrue(chart[-1]['is_today'])
        self.assertEqual(chart[-1]['total'], 2)
        self.assertEqual(chart[-2]['total'], 2)
        self.assertEqual(context['chart_total'], 4)
        self.assertEqual(context['chart_ticks'], [2, 1, 0])
        self.assertEqual(chart[-1]['height'], 100)

        outcomes = {outcome['key']: outcome['count'] for outcome in context['outcomes']}
        self.assertEqual(outcomes, {'finished': 2, 'active': 1, 'failed': 1, 'canceled': 0})

        cpu = context['usage_meters'][0]
        self.assertEqual(cpu['kind'], 'cpu')
        self.assertEqual(cpu['bars'][-1]['value'], 7)
        self.assertTrue(cpu['bars'][-1]['in_quota_window'])
        self.assertFalse(cpu['bars'][0]['in_quota_window'])

        self.assertEqual(context['disk']['total'], self.user.calc_disk_usage())
        self.assertContains(response, 'escr-chart-col')

    def test_empty(self):
        response = self.client.get(reverse('report-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['chart_total'], 0)
        self.assertContains(response, 'No tasks in the last')

    def test_legacy_ui_keeps_upstreams_page(self):
        self.user.legacy_mode = True
        self.user.save()
        response = self.client.get(reverse('report-list'))
        self.assertTemplateUsed(response, MyTasks.upstream_template_name)
        self.assertNotIn('chart', response.context)


class TaskDetailTestCase(CoreFactoryTestCase):

    def setUp(self):
        super().setUp()
        self.user = self.factory.make_user()
        self.client.force_login(self.user)

    def test_detail(self):
        now = timezone.now()
        report = TaskReport.objects.create(
            user=self.user, label='Train', workflow_state=TaskReport.WORKFLOW_STATE_DONE,
            started_at=now, done_at=now + timedelta(minutes=3), messages='All good')
        response = self.client.get(reverse('report-detail', kwargs={'pk': report.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, TaskDetail.template_name)
        self.assertEqual(response.context['ran'], timedelta(minutes=3))
        self.assertContains(response, 'All good')

    def test_someone_elses_task(self):
        report = TaskReport.objects.create(user=self.factory.make_user(), label='Theirs')
        response = self.client.get(reverse('report-detail', kwargs={'pk': report.pk}))
        self.assertEqual(response.status_code, 404)
