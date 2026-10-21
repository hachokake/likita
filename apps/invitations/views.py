from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.contrib import messages
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView

from apps.invitations.models import Invitation
from apps.invitations.services import send_invitation_via_provider, send_qr_image_via_provider
from apps.rsvp.forms import RSVPForm
from apps.rsvp.models import RSVP


def build_calendar_url(event):
    """Lien « Ajouter à Google Agenda » ; durée par défaut de 4 heures."""
    tz = timezone.get_current_timezone()
    start = datetime.combine(event.event_date, event.event_time).replace(tzinfo=tz)
    end = start + timedelta(hours=4)
    fmt = '%Y%m%dT%H%M%S'
    params = {
        'action': 'TEMPLATE',
        'text': event.name,
        'dates': f'{start.strftime(fmt)}/{end.strftime(fmt)}',
        'ctz': str(tz),
        'location': event.address,
        'details': event.welcome_message or event.description or '',
    }
    return f'https://calendar.google.com/calendar/render?{urlencode(params)}'


def build_public_invitation_context(invitation, form=None, response_saved=False):
    """Contexte commun à l'affichage de l'invitation et au ré-affichage après erreur RSVP."""
    guest = invitation.guest
    rsvp = getattr(guest, 'rsvp', None)
    qr_code = getattr(guest, 'qrcode', None)
    accepted = rsvp is not None and rsvp.response == RSVP.Response.ACCEPTED
    program_items = list(invitation.event.program_items.all())
    return {
        'invitation': invitation,
        'event': invitation.event,
        'guest': guest,
        'rsvp': rsvp,
        'form': form or RSVPForm(instance=rsvp, guest=guest),
        'response_saved': response_saved,
        'has_responded': rsvp is not None and rsvp.response != RSVP.Response.PENDING,
        'accepted': accepted,
        'show_invitation_pass': accepted and qr_code is not None and bool(qr_code.image),
        'qr_code': qr_code,
        'program_items': program_items,
        'calendar_url': build_calendar_url(invitation.event),
    }


class InvitationPreviewView(DetailView):
    template_name = 'invitations/public_invitation.html'
    context_object_name = 'invitation'
    slug_field = 'token'
    slug_url_kwarg = 'token'
    queryset = Invitation.objects.select_related('event', 'guest', 'guest__rsvp', 'guest__qrcode').prefetch_related('event__program_items', 'event__gallery_items')

    def get_object(self, queryset=None):
        invitation = super().get_object(queryset)
        if invitation.delivery_status != Invitation.DeliveryStatus.OPENED:
            invitation.delivery_status = Invitation.DeliveryStatus.OPENED
            invitation.opened_at = timezone.now()
            invitation.save(update_fields=['delivery_status', 'opened_at', 'updated_at'])
        return invitation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        response_saved = (
            self.request.GET.get('response_saved') == '1'
            and self.request.session.pop(f'rsvp_saved_{self.object.token}', False)
        )
        context.update(build_public_invitation_context(self.object, response_saved=response_saved))
        return context


class SendInvitationView(DetailView):
    queryset = Invitation.objects.select_related('guest', 'event')
    slug_field = 'token'
    slug_url_kwarg = 'token'

    def get(self, request, *args, **kwargs):
        invitation = get_object_or_404(self.get_queryset(), token=kwargs['token'], event__owner=request.user)
        result = send_invitation_via_provider(invitation, base_url=settings.APP_BASE_URL)
        if result.success and result.provider == Invitation.Provider.WHATSAPP_CLOUD:
            messages.success(request, 'Invitation envoyée via WhatsApp Business.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('guests:list')))

        if result.success:
            return HttpResponseRedirect(result.fallback_url)

        messages.error(request, f"Échec d'envoi via WhatsApp Business : {result.error}")
        return HttpResponseRedirect(result.fallback_url or request.META.get('HTTP_REFERER', reverse('guests:list')))


class SendQRCodeImageView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        invitation = get_object_or_404(
            Invitation.objects.select_related('event', 'guest__rsvp', 'guest__qrcode'),
            token=kwargs['token'],
            event__owner=request.user,
        )
        result = send_qr_image_via_provider(invitation)
        redirect_url = reverse('guests:detail', kwargs={'pk': invitation.guest.pk})
        if result.success:
            messages.success(request, 'Le QR code a été envoyé sur WhatsApp.')
        else:
            messages.error(request, f"Impossible d'envoyer le QR code : {result.error}")
        return HttpResponseRedirect(redirect_url)
