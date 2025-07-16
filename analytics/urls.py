# analytics/urls.py
from django.urls import path
from . import views
from .views import upload_dataset, analyze_data

urlpatterns = [
    path('registration/upload/',
         upload_dataset, name='upload_dataset'),
    path('analyze/<int:dataset_id>/', analyze_data, name='analyze'),
    path('', views.analytics_home, name='analytics_home'),
]
