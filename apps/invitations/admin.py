from django.contrib import admin
from django.contrib import messages

from apps.invitations.models import Invitation
from apps.invitations.services import send_invitation_via_provider


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
	list_display = ('guest', 'event', 'provider', 'delivery_status', 'provider_message_id', 'sent_at', 'opened_at')
	list_filter = ('provider', 'delivery_status', 'event')
	search_fields = ('guest__full_name', 'guest__whatsapp_number', 'event__name', 'token', 'provider_message_id')
	readonly_fields = ('token', 'provider_message_id', 'sent_at', 'opened_at', 'last_delivery_error')
	actions = ('send_now',)

	@admin.action(description='Envoyer immediatement via le provider configure')
	def send_now(self, request, queryset):
		failures = 0
		for invitation in queryset.select_related('event', 'guest'):
			result = send_invitation_via_provider(invitation)
			if not result.success:
				failures += 1
		if failures:
			self.message_user(request, f'{failures} invitation(s) ont echoue.', level=messages.WARNING)
		else:
			self.message_user(request, 'Invitations envoyees avec succes.')
