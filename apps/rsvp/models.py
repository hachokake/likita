from django.db import models

from apps.core.models import TimeStampedUUIDModel


class RSVP(TimeStampedUUIDModel):
	class Response(models.TextChoices):
		PENDING = 'pending', 'En attente'
		ACCEPTED = 'accepted', 'Je serai present'
		DECLINED = 'declined', 'Je ne pourrai pas venir'

	event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='rsvps')
	guest = models.OneToOneField('guests.Guest', on_delete=models.CASCADE, related_name='rsvp')
	response = models.CharField(max_length=16, choices=Response.choices, default=Response.PENDING)
	companion_count = models.PositiveIntegerField(default=0)
	drink_preference = models.CharField(max_length=32, blank=True)
	guest_message = models.TextField(blank=True)
	responded_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		verbose_name = 'RSVP'
		verbose_name_plural = 'RSVPs'
		indexes = [models.Index(fields=['event', 'response'])]

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)
		if self.response == self.Response.ACCEPTED:
			self.guest.status = self.guest.Status.PRESENT
		elif self.response == self.Response.DECLINED:
			self.guest.status = self.guest.Status.ABSENT
		self.guest.save(update_fields=['status', 'updated_at'])

	def __str__(self):
		return f'RSVP for {self.guest}'
