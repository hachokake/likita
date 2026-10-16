from dataclasses import dataclass
import mimetypes
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


def _build_cloud_media_api_url():
    return (
        f'https://graph.facebook.com/{settings.WHATSAPP_API_VERSION}/'
        f'{settings.WHATSAPP_PHONE_NUMBER_ID}/media'
    )


def _ensure_cloud_api_is_configured():
    if not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        raise WhatsAppDeliveryError(
            'WhatsApp Cloud API non configuree. Renseignez WHATSAPP_ACCESS_TOKEN et WHATSAPP_PHONE_NUMBER_ID.'
        )


def send_whatsapp_cloud_message(invitation):
    _ensure_cloud_api_is_configured()

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


def send_whatsapp_cloud_qr_image(invitation):
    _ensure_cloud_api_is_configured()
    qr_code = invitation.guest.qrcode
    if not qr_code.image:
        raise WhatsAppDeliveryError("L'image du QR code n'est pas disponible.")

    image_name = qr_code.image.name.rsplit('/', 1)[-1]
    image_content_type = mimetypes.guess_type(image_name)[0] or 'image/png'
    qr_code.image.open('rb')
    try:
        upload_response = requests.post(
            _build_cloud_media_api_url(),
            headers={'Authorization': f'******'},
            data={'messaging_product': 'whatsapp', 'type': image_content_type},
            files={'file': (image_name, qr_code.image.file, image_content_type)},
            timeout=20,
            verify=settings.WHATSAPP_VERIFY_SSL,
        )
    finally:
        qr_code.image.close()

    upload_data = upload_response.json()
    if upload_response.status_code >= 400 or 'error' in upload_data:
        error = upload_data.get('error', {}).get('message', upload_response.text)
        raise WhatsAppDeliveryError(error)

    media_id = upload_data.get('id')
    if not media_id:
        raise WhatsAppDeliveryError("WhatsApp n'a pas retourne l'identifiant du QR code.")

    send_response = requests.post(
        _build_cloud_api_url(),
        headers={
            'Authorization': f'******',
            'Content-Type': 'application/json',
        },
        json={
            'messaging_product': 'whatsapp',
            'recipient_type': 'individual',
            'to': _normalize_whatsapp_number(invitation.guest.whatsapp_number),
            'type': 'image',
            'image': {'id': media_id},
        },
        timeout=20,
        verify=settings.WHATSAPP_VERIFY_SSL,
    )
    send_data = send_response.json()
    if send_response.status_code >= 400 or 'error' in send_data:
        error = send_data.get('error', {}).get('message', send_response.text)
        raise WhatsAppDeliveryError(error)

    messages = send_data.get('messages', [])
    return DeliveryResult(
        success=True,
        message_id=messages[0].get('id', '') if messages else '',
        provider=Invitation.Provider.WHATSAPP_CLOUD,
    )


def send_qr_image_via_provider(invitation):
    if invitation.guest.rsvp.response != invitation.guest.rsvp.Response.ACCEPTED:
        return DeliveryResult(
            success=False,
            error="Le QR code ne peut etre envoye qu'apres confirmation de presence.",
        )

    if settings.WHATSAPP_PROVIDER != Invitation.Provider.WHATSAPP_CLOUD:
        return DeliveryResult(
            success=False,
            error="L'envoi automatique du QR code requiert WhatsApp Cloud API.",
        )

    try:
        return send_whatsapp_cloud_qr_image(invitation)
    except (WhatsAppDeliveryError, requests.RequestException) as exc:
        return DeliveryResult(success=False, error=str(exc), provider=Invitation.Provider.WHATSAPP_CLOUD)


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