"""
Upstream's URLs, with ours in front of them: our API under /api/custom/, and
our versions of some of upstream's pages (same paths, so upstream's names and
links still lead to them).
"""
from django.urls import include, path

from escriptorium.urls import urlpatterns as upstream_urlpatterns

from .tasks.views import MyTasks, TaskDetail

urlpatterns = [
    path('api/custom/', include('escr_custom.training.urls')),
    path('quotas/', MyTasks.as_view()),
    path('quotas/<int:pk>/', TaskDetail.as_view()),
    *upstream_urlpatterns,
]
