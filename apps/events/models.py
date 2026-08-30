import uuid

from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify

from apps.core.models import TimeStampedUUIDModel


class Event(TimeStampedUUIDModel):
	class EventType(models.TextChoices):
		WEDDING = 'wedding', 'Mariage'
		BIRTHDAY = 'birthday', 'Anniversaire'
		COLLATION = 'collation', 'Collation'
		BAPTISM = 'baptism', 'Bapteme'
		CONFERENCE = 'conference', 'Conference'
		FAMILY_PARTY = 'family_party', 'Fete familiale'
		GRADUATION = 'graduation', 'Remise de diplome'
		MEETING = 'meeting', 'Reunion'
		OTHER = 'other', 'Autre'

	class Status(models.TextChoices):
		DRAFT = 'draft', 'Brouillon'
		PUBLISHED = 'published', 'Publie'
		ARCHIVED = 'archived', 'Archive'

	owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='events')
	name = models.CharField(max_length=255)
	slug = models.SlugField(max_length=280, unique=True, blank=True)
	event_type = models.CharField(max_length=32, choices=EventType.choices, default=EventType.OTHER)
	description = models.TextField(blank=True)
	host_names = models.CharField(max_length=255, help_text='Names shown in the WhatsApp invitation.')
	cover_image = models.ImageField(upload_to='events/covers/', blank=True, null=True)
	event_date = models.DateField()
	event_time = models.TimeField()
	address = models.CharField(max_length=255)
	google_maps_url = models.URLField(blank=True)
	detailed_program = models.TextField(blank=True)
	dress_code = models.CharField(max_length=255, blank=True)
	welcome_message = models.TextField(blank=True)
	rsvp_deadline = models.DateField(null=True, blank=True)
	max_guests = models.PositiveIntegerField(default=100)
	background_music = models.FileField(upload_to='events/music/', blank=True, null=True)
	status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
	allow_multiple_entries = models.BooleanField(default=False)
	published_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ['-event_date', '-event_time']
		indexes = [
			models.Index(fields=['owner', 'status']),
			models.Index(fields=['event_date', 'event_type']),
		]

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.name)[:240]
			if Event.objects.filter(slug=self.slug).exists():
				self.slug = f'{self.slug}-{uuid.uuid4().hex[:6]}'
		super().save(*args, **kwargs)

	def __str__(self):
		return self.name


class EventProgram(TimeStampedUUIDModel):
	event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='program_items')
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	start_at = models.DateTimeField()
	end_at = models.DateTimeField(null=True, blank=True)
	location = models.CharField(max_length=255, blank=True)
	sort_order = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ['sort_order', 'start_at']

	def __str__(self):
		return self.title


class Theme(TimeStampedUUIDModel):
	event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='theme')
	primary_color = models.CharField(max_length=7, default='#0D0D0D')
	secondary_color = models.CharField(max_length=7, default='#C1121F')
	accent_color = models.CharField(max_length=7, default='#E5383B')
	text_color = models.CharField(max_length=7, default='#F8FAFC')
	glass_opacity = models.DecimalField(max_digits=3, decimal_places=2, default=0.18)

	def __str__(self):
		return f'Theme for {self.event}'


class Gallery(TimeStampedUUIDModel):
	event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='gallery_items')
	image = models.ImageField(upload_to='events/gallery/')
	caption = models.CharField(max_length=255, blank=True)
	is_organizer_photo = models.BooleanField(default=False)
	sort_order = models.PositiveIntegerField(default=0)

	class Meta:
		ordering = ['sort_order', 'created_at']

	def __str__(self):
		return self.caption or f'Gallery item for {self.event}'
