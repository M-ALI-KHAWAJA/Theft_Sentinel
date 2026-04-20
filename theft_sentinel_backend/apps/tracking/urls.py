"""
URL configuration for tracking app
"""
from django.urls import path
from .views import (
    TrackingRecordListCreateView,
    TrackingRecordDetailView,
    PersonTrackingPathView,
    TrackingIngestView
)

urlpatterns = [
    path('records/', TrackingRecordListCreateView.as_view(), name='tracking_record_list_create'),
    path('records/<int:pk>/', TrackingRecordDetailView.as_view(), name='tracking_record_detail'),
    path('person/<str:person_id>/path/', PersonTrackingPathView.as_view(), name='person_tracking_path'),
    path('ingest/', TrackingIngestView.as_view(), name='tracking_ingest'),
]

