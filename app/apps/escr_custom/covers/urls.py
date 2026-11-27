from django.urls import path

from . import views

urlpatterns = [
    path('covers/', views.CoversView.as_view(), name='custom-covers'),
]
