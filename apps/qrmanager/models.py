import uuid

from django.db import models

from apps.core.models import TimeStampedUUIDModel


class QRCode(TimeStampedUUIDModel):
	event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='qr_codes')
	guest = models.OneToOneField('guests.Guest', on_delete=models.CASCADE, related_name='qrcode')
	token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
	image = models.ImageField(upload_to='qr-codes/', blank=True, null=True)
	is_active = models.BooleanField(default=True)
	last_scanned_at = models.DateTimeField(null=True, blank=True)
	scan_count = models.PositiveIntegerField(default=0)

	class Meta:
		verbose_name = 'QR code'
		verbose_name_plural = 'QR codes'

	def __str__(self):
		return f'QR for {self.guest}'
