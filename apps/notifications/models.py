from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedUUIDModel


class Notification(TimeStampedUUIDModel):
	class Kind(models.TextChoices):
		RSVP_ACCEPTED = 'rsvp_accepted', 'RSVP accepted'
		RSVP_DECLINED = 'rsvp_declined', 'RSVP declined'
		RSVP_UPDATED = 'rsvp_updated', 'RSVP updated'
		QR_SCANNED = 'qr_scanned', 'QR scanned'

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
	event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
	guest = models.ForeignKey('guests.Guest', on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
	kind = models.CharField(max_length=32, choices=Kind.choices)
	title = models.CharField(max_length=255)
	body = models.TextField()
	is_read = models.BooleanField(default=False)

	class Meta:
		ordering = ['-created_at']
		indexes = [models.Index(fields=['user', 'is_read', 'created_at'])]

	def __str__(self):
		return self.title
