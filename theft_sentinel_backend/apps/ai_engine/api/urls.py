"""
AI Engine API URLs
"""
from django.urls import path
from .views import (
    AnalyzeFrameView,
    ProcessCameraView,
    FullPipelineView,
    ModelInfoView,
    InferenceHistoryView,
    HealthCheckView,
    StartContinuousMonitorView,
    StopContinuousMonitorView,
    MonitorStatusView,
)

urlpatterns = [
    # Main endpoints
    path('analyze-frame/', AnalyzeFrameView.as_view(), name='ai-analyze-frame'),
    path('process-camera/', ProcessCameraView.as_view(), name='ai-process-camera'),
    path('full-pipeline/', FullPipelineView.as_view(), name='ai-full-pipeline'),
    
    # Continuous monitoring (NEW - for live feed processing)
    path('monitor/start/', StartContinuousMonitorView.as_view(), name='ai-monitor-start'),
    path('monitor/stop/', StopContinuousMonitorView.as_view(), name='ai-monitor-stop'),
    path('monitor/status/', MonitorStatusView.as_view(), name='ai-monitor-status'),
    
    # Info and monitoring
    path('model-info/', ModelInfoView.as_view(), name='ai-model-info'),
    path('inference-history/', InferenceHistoryView.as_view(), name='ai-inference-history'),
    path('health/', HealthCheckView.as_view(), name='ai-health'),
]

