from rest_framework import serializers

from apps.events.models import Event, Theme
from apps.guests.models import Guest
from apps.invitations.models import Invitation
from apps.notifications.models import Notification
from apps.qrmanager.models import QRCode
from apps.rsvp.models import RSVP


class ThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theme
        fields = ('primary_color', 'secondary_color', 'accent_color', 'text_color', 'glass_opacity')


class EventSerializer(serializers.ModelSerializer):
    theme = ThemeSerializer(read_only=True)

    class Meta:
        model = Event
        fields = (
            'id',
            'name',
            'slug',
            'event_type',
            'description',
            'host_names',
            'event_date',
            'event_time',
            'address',
            'google_maps_url',
            'dress_code',
            'welcome_message',
            'rsvp_deadline',
            'max_guests',
            'status',
            'allow_multiple_entries',
            'theme',
        )


class RSVPSerializer(serializers.ModelSerializer):
    class Meta:
        model = RSVP
        fields = ('response', 'companion_count', 'guest_message', 'responded_at')


class QRCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = QRCode
        fields = ('token', 'image', 'is_active', 'scan_count', 'last_scanned_at')


class GuestSerializer(serializers.ModelSerializer):
    rsvp = RSVPSerializer(read_only=True)
    qrcode = QRCodeSerializer(read_only=True)

    class Meta:
        model = Guest
        fields = (
            'id',
            'event',
            'full_name',
            'whatsapp_number',
            'email',
            'category',
            'allowed_companions',
            'reserved_table',
            'notes',
            'status',
            'rsvp',
            'qrcode',
        )


class InvitationSerializer(serializers.ModelSerializer):
    guest = GuestSerializer(read_only=True)

    class Meta:
        model = Invitation
        fields = ('id', 'event', 'guest', 'token', 'delivery_status', 'whatsapp_message', 'sent_at', 'opened_at')


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'kind', 'title', 'body', 'is_read', 'created_at', 'event', 'guest')