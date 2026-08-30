from dataclasses import dataclass
import re

import requests
from django.conf import settings
from django.utils import timezone

from apps.invitations.models import Invitation, normalize_absolute_base_url


class WhatsAppDeliveryError(Exception):
    pass


@dataclass
class DeliveryResult:
    success: bool
    message_id: str = ''
    fallback_url: str = ''
    error: str = ''
    provider: str = Invitation.Provider.MANUAL


def _normalize_whatsapp_number(value):
    cleaned = re.sub(r'[^\d+]', '', value or '')
    if cleaned.startswith('00'):
        cleaned = cleaned[2:]
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
    return cleaned


def _build_cloud_api_url():
    return (
        f'https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/'
        f'{settings.WHATSAPP_PHONE_NUMBER_ID}/messages'
    )


def send_whatsapp_cloud_message(invitation):
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        raise WhatsAppDeliveryError(
            'WhatsApp Cloud API non configuree. Renseignez WHATSAPP_ACCESS_TOKEN et WHATSAPP_PHONE_NUMBER_ID.'
        )

    response = requests.post(
        _build_cloud_api_url(),
        headers={
            'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}',
            'Content-Type': 'application/json',
        },
        json={
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': _normalize_whatsapp_number(invitation.guest.whatsapp_number),
            'type': 'text',
            'text': {
                'preview_url': True,
                'body': invitation.whatsapp_message,
            },
        },
        timeout=20,
        verify=settings.WHATSAPP_VERIFY_SSL,
    )
    data = response.json()
    if response.status_code >= 400 or 'error' in data:
        error = data.get('error', {}).get('message', response.text)
        raise WhatsAppDeliveryError(error)

    messages = data.get('messages', [])
    return DeliveryResult(
        success=True,
        message_id=messages[0].get('id', '') if messages else '',
        provider=Invitation.Provider.WHATSAPP_CLOUD,
    )


def send_invitation_via_provider(invitation, base_url=''):
    resolved_base_url = normalize_absolute_base_url(base_url or settings.APP_BASE_URL)
    invitation.whatsapp_message = invitation.build_whatsapp_message(resolved_base_url)
    invitation.save(update_fields=['whatsapp_message', 'updated_at'])

    if settings.WHATSAPP_PROVIDER == Invitation.Provider.WHATSAPP_CLOUD:
        try:
            delivery = send_whatsapp_cloud_message(invitation)
        except (WhatsAppDeliveryError, requests.RequestException) as exc:
            invitation.provider = Invitation.Provider.WHATSAPP_CLOUD
            invitation.delivery_status = Invitation.DeliveryStatus.FAILED
            invitation.last_delivery_error = str(exc)
            invitation.save(update_fields=['provider', 'delivery_status', 'last_delivery_error', 'updated_at'])
            return DeliveryResult(
                success=False,
                error=str(exc),
                fallback_url=invitation.whatsapp_share_url,
                provider=Invitation.Provider.WHATSAPP_CLOUD,
            )

        invitation.provider = delivery.provider
        invitation.provider_message_id = delivery.message_id
        invitation.delivery_status = Invitation.DeliveryStatus.SENT
        invitation.last_delivery_error = ''
        invitation.sent_at = timezone.now()
        invitation.guest.status = invitation.guest.Status.SENT
        invitation.guest.invited_at = invitation.sent_at
        invitation.save(
            update_fields=[
                'provider',
                'provider_message_id',
                'delivery_status',
                'last_delivery_error',
                'sent_at',
                'updated_at',
            ]
        )
        invitation.guest.save(update_fields=['status', 'invited_at', 'updated_at'])
        return delivery

    invitation.provider = Invitation.Provider.MANUAL
    invitation.delivery_status = Invitation.DeliveryStatus.GENERATED
    invitation.last_delivery_error = ''
    invitation.save(update_fields=['provider', 'delivery_status', 'last_delivery_error', 'updated_at'])
    return DeliveryResult(
        success=True,
        fallback_url=invitation.whatsapp_share_url,
        provider=Invitation.Provider.MANUAL,
    )