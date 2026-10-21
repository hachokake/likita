from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from apps.notifications.models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 50

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).select_related('event', 'guest')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Les notifications affichées passent à "lu" ; les objets déjà chargés gardent l'état non lu pour ce rendu.
        unread_ids = [n.pk for n in context['notifications'] if not n.is_read]
        if unread_ids:
            Notification.objects.filter(pk__in=unread_ids).update(is_read=True)
        return context
