from django.db import models

from apps.core.models import TimeStampedUUIDModel


class Guest(TimeStampedUUIDModel):
	class Category(models.TextChoices):
		VIP = 'vip', 'VIP'
		FAMILY = 'family', 'Famille'
		FRIENDS = 'friends', 'Amis'
		COLLEAGUES = 'colleagues', 'Collegues'
		WITNESSES = 'witnesses', 'Temoins'
		PARENTS = 'parents', 'Parents'
		OTHER = 'other', 'Autres'

	class Status(models.TextChoices):
		PENDING = 'pending', 'En attente'
		SENT = 'sent', 'Invitation envoyee'
		PRESENT = 'present', 'Present'
		ABSENT = 'absent', 'Absent'
		ARRIVED = 'arrived', 'Arrive'
		SCANNED = 'scanned', 'QR Scanne'

	event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='guests')
	full_name = models.CharField(max_length=255)
	whatsapp_number = models.CharField(max_length=32)
	email = models.EmailField(blank=True)
	category = models.CharField(max_length=32, choices=Category.choices, default=Category.OTHER)
	allowed_companions = models.PositiveIntegerField(default=0)
	reserved_table = models.CharField(max_length=120, blank=True)
	notes = models.TextField(blank=True)
	status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
	invited_at = models.DateTimeField(null=True, blank=True)
	arrived_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ['full_name']
		constraints = [
			models.UniqueConstraint(fields=['event', 'whatsapp_number'], name='unique_guest_phone_per_event'),
		]
		indexes = [
			models.Index(fields=['event', 'status']),
			models.Index(fields=['event', 'category']),
		]

	def __str__(self):
		return self.full_name
