from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import FormView

from apps.invitations.models import Invitation
from apps.invitations.views import build_public_invitation_context
from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from apps.qrmanager.models import QRCode
from apps.qrmanager.services import generate_qr_image
from apps.rsvp.forms import RSVPForm
from apps.rsvp.models import RSVP


class PublicRSVPUpdateView(FormView):
    form_class = RSVPForm
    template_name = 'invitations/public_invitation.html'

    def dispatch(self, request, *args, **kwargs):
        self.invitation = get_object_or_404(
            Invitation.objects.select_related('event', 'guest', 'guest__rsvp', 'event__owner'),
            token=kwargs['token'],
        )
        self.rsvp = self.invitation.guest.rsvp
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        # Le formulaire vit sur la page d'invitation : un accès direct y renvoie.
        return redirect(f"{self.invitation.get_absolute_url()}#confirmation")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.rsvp
        kwargs['guest'] = self.invitation.guest
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Un ModelForm invalide a déjà modifié l'instance en mémoire : on repart de l'état enregistré.
        self.rsvp.refresh_from_db()
        context.update(build_public_invitation_context(self.invitation, form=context.get('form')))
        context['form_has_errors'] = True
        return context

    def form_valid(self, form):
        previous_response = self.rsvp.response
        rsvp = form.save(commit=False)
        rsvp.responded_at = timezone.now()
        rsvp.event = self.invitation.event
        rsvp.guest = self.invitation.guest
        rsvp.save()

        if rsvp.response == RSVP.Response.ACCEPTED:
            qr_code, _ = QRCode.objects.get_or_create(
                guest=self.invitation.guest,
                defaults={'event': self.invitation.event},
            )
            if not qr_code.image:
                generate_qr_image(qr_code)

        if previous_response in (RSVP.Response.ACCEPTED, RSVP.Response.DECLINED) and previous_response != rsvp.response:
            kind = Notification.Kind.RSVP_UPDATED
            title = 'Réponse mise à jour'
        elif rsvp.response == RSVP.Response.ACCEPTED:
            kind = Notification.Kind.RSVP_ACCEPTED
            title = 'Présence confirmée'
        else:
            kind = Notification.Kind.RSVP_DECLINED
            title = 'Invitation déclinée'

        if rsvp.response == RSVP.Response.ACCEPTED:
            companions = f" avec {rsvp.companion_count} accompagnant{'s' if rsvp.companion_count > 1 else ''}" if rsvp.companion_count else ''
            body = f'{self.invitation.guest.full_name} sera présent(e) à {self.invitation.event.name}{companions}.'
        else:
            body = f'{self.invitation.guest.full_name} ne pourra pas assister à {self.invitation.event.name}.'
        if rsvp.guest_message:
            body += f' Message : « {rsvp.guest_message.strip()[:160]} »'

        create_notification(
            user=self.invitation.event.owner,
            event=self.invitation.event,
            guest=self.invitation.guest,
            kind=kind,
            title=title,
            body=body,
        )
        self.request.session[f'rsvp_saved_{self.invitation.token}'] = True
        invitation_url = reverse('invitations:public', kwargs={'token': self.invitation.token})
        anchor = 'pass' if rsvp.response == RSVP.Response.ACCEPTED else 'confirmation'
        return redirect(f'{invitation_url}?response_saved=1#{anchor}')
