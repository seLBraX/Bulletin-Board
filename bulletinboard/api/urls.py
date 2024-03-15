from django.urls import path

from .views import ads, AdDetailView, comments

urlpatterns = [
    path('ads/<int:pk>/comments/', comments),
    path('ads/<int:pk>/', AdDetailView.as_view()),
    path('ads/', ads),
]
