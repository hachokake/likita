from celery import shared_task

from apps.invitations.models import Invitation, normalize_absolute_base_url
from apps.invitations.services import send_invitation_via_provider


@shared_task
def compose_invitation_message(invitation_id, base_url='https://monsite.com'):
    invitation = Invitation.objects.select_related('event', 'guest').get(pk=invitation_id)
    invitation.whatsapp_message = invitation.build_whatsapp_message(normalize_absolute_base_url(base_url))
    invitation.save(update_fields=['whatsapp_message', 'updated_at'])
    return invitation.whatsapp_message


@shared_task
def deliver_invitation(invitation_id):
    invitation = Invitation.objects.select_related('event', 'guest').get(pk=invitation_id)
    result = send_invitation_via_provider(invitation)
    return {
        'success': result.success,
        'provider': result.provider,
        'message_id': result.message_id,
        'error': result.error,
        'fallback_url': result.fallback_url,
    }