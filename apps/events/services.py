from django.db.models import Count, Q

from apps.guests.models import Guest
from apps.notifications.models import Notification
from apps.qrmanager.models import QRCode
from apps.rsvp.models import RSVP
from apps.scanner.models import ScanLog


def _percentage(numerator, denominator):
    if not denominator:
        return 0
    return round((numerator / denominator) * 100, 1)


def get_event_dashboard_data(event):
    guest_totals = Guest.objects.filter(event=event).aggregate(
        total=Count('id'),
        accepted=Count('id', filter=Q(rsvp__response=RSVP.Response.ACCEPTED)),
        declined=Count('id', filter=Q(rsvp__response=RSVP.Response.DECLINED)),
    )
    total_guests = guest_totals['total']
    accepted_guests = guest_totals['accepted']
    declined_guests = guest_totals['declined']
    pending_guests = total_guests - accepted_guests - declined_guests

    scan_logs = ScanLog.objects.filter(event=event)
    scan_totals = scan_logs.aggregate(
        qr_codes_scanned=Count('qr_code_id', distinct=True),
        valid_scans=Count('id', filter=Q(status=ScanLog.ScanStatus.ALLOWED)),
        unique_admissions=Count(
            'guest_id',
            filter=Q(status=ScanLog.ScanStatus.ALLOWED),
            distinct=True,
        ),
        confirmed_arrivals=Count(
            'guest_id',
            filter=Q(
                status=ScanLog.ScanStatus.ALLOWED,
                guest__rsvp__response=RSVP.Response.ACCEPTED,
            ),
            distinct=True,
        ),
    )
    confirmed_arrivals = scan_totals['confirmed_arrivals']

    metrics = {
        'total_guests': total_guests,
        'accepted_guests': accepted_guests,
        'declined_guests': declined_guests,
        'pending_guests': pending_guests,
        'confirmation_rate': _percentage(accepted_guests, total_guests),
        'total_qr_codes': QRCode.objects.filter(event=event).count(),
        'qr_codes_scanned': scan_totals['qr_codes_scanned'],
        'valid_scans': scan_totals['valid_scans'],
        'unique_admissions': scan_totals['unique_admissions'],
        'confirmed_not_arrived': accepted_guests - confirmed_arrivals,
        'arrival_rate': _percentage(confirmed_arrivals, accepted_guests),
    }
    metrics['response_breakdown'] = (
        {
            'label': 'Confirmées',
            'count': accepted_guests,
            'percentage': _percentage(accepted_guests, total_guests),
            'color': 'bg-emerald-400',
        },
        {
            'label': 'Refusées',
            'count': declined_guests,
            'percentage': _percentage(declined_guests, total_guests),
            'color': 'bg-rose-400',
        },
        {
            'label': 'En attente',
            'count': pending_guests,
            'percentage': _percentage(pending_guests, total_guests),
            'color': 'bg-amber-300',
        },
    )

    return {
        'metrics': metrics,
        'recent_activities': Notification.objects.filter(event=event)
        .select_related('guest')
        .order_by('-created_at')[:8],
        'recent_scans': scan_logs.select_related('guest').order_by('-scanned_at')[:6],
    }
