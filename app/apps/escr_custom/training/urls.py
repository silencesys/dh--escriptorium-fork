from django.urls import path

from . import views

urlpatterns = [
    path('training/', views.TrainingInfoView.as_view(), name='custom-training-info'),
    path('collections/<int:pk>/train_recognizer/',
         views.CollectionTrainingView.as_view(job='recognition'),
         name='custom-collection-train-recognizer'),
    path('collections/<int:pk>/train_segmenter/',
         views.CollectionTrainingView.as_view(job='segmentation'),
         name='custom-collection-train-segmenter'),
]
