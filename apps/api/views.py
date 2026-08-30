from rest_framework import permissions, viewsets

from apps.api.serializers import EventSerializer, GuestSerializer, InvitationSerializer, NotificationSerializer
from apps.events.models import Event
from apps.guests.models import Guest
from apps.invitations.models import Invitation
from apps.notifications.models import Notification


class OwnerScopedViewSet(viewsets.ModelViewSet):
	permission_classes = [permissions.IsAuthenticated]


class EventViewSet(OwnerScopedViewSet):
	serializer_class = EventSerializer

	def get_queryset(self):
		return Event.objects.filter(owner=self.request.user).select_related('theme')

	def perform_create(self, serializer):
		serializer.save(owner=self.request.user)


class GuestViewSet(OwnerScopedViewSet):
	serializer_class = GuestSerializer

	def get_queryset(self):
		return Guest.objects.filter(event__owner=self.request.user).select_related('event', 'invitation', 'rsvp', 'qrcode')


class InvitationViewSet(OwnerScopedViewSet):
	serializer_class = InvitationSerializer

	def get_queryset(self):
		return Invitation.objects.filter(event__owner=self.request.user).select_related('event', 'guest')


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
	serializer_class = NotificationSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		return Notification.objects.filter(user=self.request.user).select_related('event', 'guest')
