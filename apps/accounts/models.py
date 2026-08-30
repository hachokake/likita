import uuid

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import TimeStampedUUIDModel


class UserManager(BaseUserManager):
	use_in_migrations = True

	def _create_user(self, email, password, **extra_fields):
		if not email:
			raise ValueError('L\'adresse courriel est obligatoire.')
		email = self.normalize_email(email)
		user = self.model(email=email, username=email, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_user(self, email, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', False)
		extra_fields.setdefault('is_superuser', False)
		return self._create_user(email, password, **extra_fields)

	def create_superuser(self, email, password, **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)
		if extra_fields.get('is_staff') is not True:
			raise ValueError('Le super administrateur doit avoir is_staff=True.')
		if extra_fields.get('is_superuser') is not True:
			raise ValueError('Le super administrateur doit avoir is_superuser=True.')
		return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
	class SubscriptionTier(models.TextChoices):
		FREE = 'free', 'Gratuit'
		PRO = 'pro', 'Professionnel'
		PREMIUM = 'premium', 'Premium'

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	username = models.CharField(max_length=150, blank=True)
	email = models.EmailField(unique=True)
	phone_number = models.CharField(max_length=32, blank=True)
	company_name = models.CharField(max_length=255, blank=True)
	is_suspended = models.BooleanField(default=False)
	subscription_tier = models.CharField(
		max_length=16,
		choices=SubscriptionTier.choices,
		default=SubscriptionTier.FREE,
	)
	last_seen_at = models.DateTimeField(null=True, blank=True)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []

	objects = UserManager()

	class Meta:
		ordering = ['email']
		indexes = [models.Index(fields=['email', 'subscription_tier'])]

	def __str__(self):
		return self.get_full_name() or self.email


class UserSettings(TimeStampedUUIDModel):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='settings')
	locale = models.CharField(max_length=10, default='fr')
	timezone = models.CharField(max_length=64, default='Africa/Kinshasa')
	email_notifications = models.BooleanField(default=True)
	whatsapp_notifications = models.BooleanField(default=True)
	scan_alerts = models.BooleanField(default=True)
	default_guest_limit = models.PositiveIntegerField(default=150)

	class Meta:
		verbose_name = 'Parametres utilisateur'
		verbose_name_plural = 'Parametres utilisateur'

	def __str__(self):
		return f'Settings for {self.user}'
