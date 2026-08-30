from django.utils import timezone

from apps.guests.models import Guest
from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from apps.qrmanager.models import QRCode
from apps.scanner.models import ScanLog


def process_scan(token, user=None, scanner_label='', device_info=''):
    try:
        qr_code = QRCode.objects.select_related('guest', 'event').get(token=token, is_active=True)
    except QRCode.DoesNotExist:
        return {'ok': False, 'message': 'QR invalide', 'guest': None, 'log': None}

    event = qr_code.event
    guest = qr_code.guest
    if qr_code.scan_count and not event.allow_multiple_entries:
        log = ScanLog.objects.create(
            event=event,
            guest=guest,
            qr_code=qr_code,
            scanned_by=user,
            scanner_label=scanner_label,
            device_info=device_info,
            status=ScanLog.ScanStatus.REUSED,
        )
        return {'ok': False, 'message': 'QR deja utilise', 'guest': guest, 'log': log}

    now = timezone.now()
    qr_code.scan_count += 1
    qr_code.last_scanned_at = now
    qr_code.save(update_fields=['scan_count', 'last_scanned_at', 'updated_at'])
    guest.status = Guest.Status.SCANNED
    guest.arrived_at = now
    guest.save(update_fields=['status', 'arrived_at', 'updated_at'])
    log = ScanLog.objects.create(
        event=event,
        guest=guest,
        qr_code=qr_code,
        scanned_by=user,
        scanner_label=scanner_label,
        device_info=device_info,
        status=ScanLog.ScanStatus.ALLOWED,
    )
    create_notification(
        user=event.owner,
        event=event,
        guest=guest,
        kind=Notification.Kind.QR_SCANNED,
        title='QR scanne',
        body=f'{guest.full_name} vient d arriver sur {event.name}.',
    )
    return {'ok': True, 'message': f'Bienvenue {guest.full_name}', 'guest': guest, 'log': log}