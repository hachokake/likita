from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import FormView

from apps.invitations.models import Invitation
from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from apps.rsvp.forms import RSVPForm
from apps.rsvp.models import RSVP


class PublicRSVPUpdateView(FormView):
    form_class = RSVPForm
    template_name = 'rsvp/respond.html'

    def dispatch(self, request, *args, **kwargs):
        self.invitation = get_object_or_404(
            Invitation.objects.select_related('event', 'guest', 'guest__rsvp', 'event__owner'),
            token=kwargs['token'],
        )
        self.rsvp = self.invitation.guest.rsvp
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.rsvp
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invitation'] = self.invitation
        return context

    def form_valid(self, form):
        previous_response = self.rsvp.response
        rsvp = form.save(commit=False)
        rsvp.responded_at = timezone.now()
        rsvp.event = self.invitation.event
        rsvp.guest = self.invitation.guest
        rsvp.save()

        if previous_response in (RSVP.Response.ACCEPTED, RSVP.Response.DECLINED) and previous_response != rsvp.response:
            kind = Notification.Kind.RSVP_UPDATED
            title = 'RSVP mis a jour'
        elif rsvp.response == RSVP.Response.ACCEPTED:
            kind = Notification.Kind.RSVP_ACCEPTED
            title = 'Presence confirmee'
        else:
            kind = Notification.Kind.RSVP_DECLINED
            title = 'Invitation refusee'

        create_notification(
            user=self.invitation.event.owner,
            event=self.invitation.event,
            guest=self.invitation.guest,
            kind=kind,
            title=title,
            body=f'{self.invitation.guest.full_name} a repondu pour {self.invitation.event.name}.',
        )
        messages.success(self.request, 'Votre reponse a bien ete enregistree.')
        return redirect('invitations:public', token=self.invitation.token)
