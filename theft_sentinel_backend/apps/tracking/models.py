"""
Tracking Record Model
"""
from django.db import models
from django.utils import timezone
from django_mongodb_backend.fields import ObjectIdAutoField


class TrackingRecord(models.Model):
    """Tracking Record model for person tracking feature vectors"""
    
    id = ObjectIdAutoField(primary_key=True)
    person_id = models.CharField(max_length=255, db_index=True)
    camera_id = models.ForeignKey(
        'cameras.Camera',
        on_delete=models.CASCADE,
        related_name='tracking_records'
    )
    vector = models.JSONField(default=dict)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        db_table = 'tracking_records'
        verbose_name = 'Tracking Record'
        verbose_name_plural = 'Tracking Records'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['person_id', '-timestamp']),
        ]
    
    def __str__(self):
        return f"Person {self.person_id} - {self.camera_id.name} at {self.timestamp}"

