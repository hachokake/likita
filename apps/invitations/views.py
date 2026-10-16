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
from apps.rsvp.models import RSVP


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
        qr_code = getattr(self.object.guest, 'qrcode', None)
        context['show_invitation_pass'] = (
            response_saved
            and self.object.guest.rsvp.response == RSVP.Response.ACCEPTED
            and qr_code is not None
            and bool(qr_code.image)
        )
        context['response_saved'] = response_saved
        return context


class SendInvitationView(DetailView):
    queryset = Invitation.objects.select_related('guest', 'event')
    slug_field = 'token'
    slug_url_kwarg = 'token'

    def get(self, request, *args, **kwargs):
        invitation = get_object_or_404(self.get_queryset(), token=kwargs['token'], event__owner=request.user)
        result = send_invitation_via_provider(invitation, base_url=settings.APP_BASE_URL)
        if result.success and result.provider == Invitation.Provider.WHATSAPP_CLOUD:
            messages.success(request, 'Invitation envoyee via WhatsApp Business.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('guests:list')))

        if result.success:
            messages.info(request, 'Provider non configure. Redirection vers le partage WhatsApp manuel.')
            return HttpResponseRedirect(result.fallback_url)

        messages.error(request, f"Echec d'envoi via WhatsApp Business: {result.error}")
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
            messages.success(request, 'Le QR code a ete envoye sur WhatsApp.')
        else:
            messages.error(request, f"Impossible d'envoyer le QR code: {result.error}")
        return HttpResponseRedirect(redirect_url)
