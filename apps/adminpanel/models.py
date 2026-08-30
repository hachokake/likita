from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedUUIDModel


class ActivityLog(TimeStampedUUIDModel):
	actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
	action = models.CharField(max_length=255)
	target_type = models.CharField(max_length=120, blank=True)
	target_identifier = models.CharField(max_length=120, blank=True)
	metadata = models.JSONField(default=dict, blank=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return self.action
