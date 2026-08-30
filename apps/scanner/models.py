from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedUUIDModel


class ScanLog(TimeStampedUUIDModel):
	class ScanStatus(models.TextChoices):
		ALLOWED = 'allowed', 'Acces autorise'
		INVALID = 'invalid', 'QR invalide'
		REUSED = 'reused', 'QR deja utilise'

	event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='scan_logs')
	guest = models.ForeignKey('guests.Guest', on_delete=models.SET_NULL, null=True, blank=True, related_name='scan_logs')
	qr_code = models.ForeignKey('qrcode.QRCode', on_delete=models.SET_NULL, null=True, blank=True, related_name='scan_logs')
	scanned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='performed_scans')
	scanner_label = models.CharField(max_length=255, blank=True)
	device_info = models.CharField(max_length=255, blank=True)
	status = models.CharField(max_length=16, choices=ScanStatus.choices)
	scanned_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-scanned_at']
		indexes = [models.Index(fields=['event', 'status', 'scanned_at'])]

	def __str__(self):
		return f'{self.event} - {self.status}'
