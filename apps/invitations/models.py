from django.db import models
from django.urls import reverse
from django.utils.crypto import get_random_string
from urllib.parse import quote

from apps.core.models import TimeStampedUUIDModel


def generate_personal_token():
	return get_random_string(8, allowed_chars='ABCDEFGHJKLMNPQRSTUVWXYZ23456789')


def normalize_absolute_base_url(value):
	base_url = (value or '').strip()
	if not base_url:
		base_url = 'http://127.0.0.1:8000'
	if '://' not in base_url:
		base_url = f'https://{base_url.lstrip("/")}'
	return base_url.rstrip('/')


def normalize_whatsapp_number(value):
	cleaned = ''.join(ch for ch in (value or '') if ch.isdigit() or ch == '+')
	if cleaned.startswith('00'):
		cleaned = cleaned[2:]
	if cleaned.startswith('+'):
		cleaned = cleaned[1:]
	return cleaned


class Invitation(TimeStampedUUIDModel):
	class DeliveryStatus(models.TextChoices):
		PENDING = 'pending', 'En attente'
		GENERATED = 'generated', 'Generee'
		SENT = 'sent', 'Envoyee'
		OPENED = 'opened', 'Ouverte'
		FAILED = 'failed', 'Echec'

	class Provider(models.TextChoices):
		MANUAL = 'manual', 'Lien manuel'
		WHATSAPP_CLOUD = 'whatsapp_cloud', 'WhatsApp Cloud API'

	event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='invitations')
	guest = models.OneToOneField('guests.Guest', on_delete=models.CASCADE, related_name='invitation')
	token = models.CharField(max_length=12, unique=True, default=generate_personal_token, editable=False)
	delivery_status = models.CharField(max_length=16, choices=DeliveryStatus.choices, default=DeliveryStatus.PENDING)
	provider = models.CharField(max_length=32, choices=Provider.choices, default=Provider.MANUAL)
	whatsapp_message = models.TextField(blank=True)
	provider_message_id = models.CharField(max_length=255, blank=True)
	last_delivery_error = models.TextField(blank=True)
	sent_at = models.DateTimeField(null=True, blank=True)
	opened_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ['-created_at']
		indexes = [models.Index(fields=['event', 'delivery_status'])]

	def __str__(self):
		return f'Invitation for {self.guest}'

	def get_absolute_url(self):
		return reverse('invitations:public', kwargs={'token': self.token})

	def build_whatsapp_message(self, absolute_url='https://monsite.com'):
		event = self.event
		base_url = normalize_absolute_base_url(absolute_url)
		link = f"{base_url}{self.get_absolute_url()}"
		return (
			f"Bonjour {self.guest.full_name}\n\n"
			f"{event.host_names} ont le plaisir de vous inviter a {event.name}.\n\n"
			f"Date : {event.event_date:%d/%m/%Y} a {event.event_time:%Hh%M}\n"
			f"Lieu : {event.address}\n\n"
			f"Votre invitation personnelle (cliquez ici) :\n{link}\n\n"
			f"Merci de confirmer votre presence."
		)

	@property
	def whatsapp_share_url(self):
		message = self.whatsapp_message or self.build_whatsapp_message()
		phone = normalize_whatsapp_number(self.guest.whatsapp_number)
		return f'https://api.whatsapp.com/send?phone={phone}&text={quote(message)}'
