from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView

from apps.invitations.models import Invitation
from apps.invitations.services import send_invitation_via_provider


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


class SendInvitationView(DetailView):
    queryset = Invitation.objects.select_related('guest', 'event')
    slug_field = 'token'
    slug_url_kwarg = 'token'

    def get(self, request, *args, **kwargs):
        invitation = get_object_or_404(self.get_queryset(), token=kwargs['token'], event__owner=request.user)
        base_url = request.build_absolute_uri('/').rstrip('/')
        result = send_invitation_via_provider(invitation, base_url=base_url)
        if result.success and result.provider == Invitation.Provider.WHATSAPP_CLOUD:
            messages.success(request, 'Invitation envoyee via WhatsApp Business.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('guests:list')))

        if result.success:
            messages.info(request, 'Provider non configure. Redirection vers le partage WhatsApp manuel.')
            return HttpResponseRedirect(result.fallback_url)

        messages.error(request, f"Echec d'envoi via WhatsApp Business: {result.error}")
        return HttpResponseRedirect(result.fallback_url or request.META.get('HTTP_REFERER', reverse('guests:list')))
