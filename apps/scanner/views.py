import uuid

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from apps.scanner.models import ScanLog
from apps.scanner.services import process_scan


class QRScannerView(LoginRequiredMixin, TemplateView):
    template_name = 'scanner/scanner.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_scans'] = ScanLog.objects.filter(event__owner=self.request.user).select_related('guest', 'event')[:10]
        return context


class ScanValidationView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        token = request.POST.get('token', '').strip()
        try:
            token_uuid = uuid.UUID(token)
        except ValueError:
            return JsonResponse({'ok': False, 'message': 'QR invalide'}, status=400)
        result = process_scan(
            token_uuid,
            user=request.user,
            scanner_label=request.POST.get('scanner_label', ''),
            device_info=request.META.get('HTTP_USER_AGENT', ''),
        )
        guest = result.get('guest')
        return JsonResponse(
            {
                'ok': result['ok'],
                'message': result['message'],
                'guest': {
                    'name': getattr(guest, 'full_name', ''),
                    'category': getattr(guest, 'category', ''),
                    'phone': getattr(guest, 'whatsapp_number', ''),
                    'companions': getattr(guest.rsvp, 'companion_count', 0) if guest and hasattr(guest, 'rsvp') else 0,
                    'arrival_time': guest.arrived_at.strftime('%H:%M') if guest and guest.arrived_at else '',
                },
            },
            status=200 if result['ok'] else 400,
            )
