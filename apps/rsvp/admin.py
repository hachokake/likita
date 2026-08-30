from django.contrib import admin

from apps.rsvp.models import RSVP


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
	list_display = ('guest', 'event', 'response', 'companion_count', 'responded_at')
	list_filter = ('response', 'event')
	search_fields = ('guest__full_name', 'event__name', 'guest_message')
