from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.views.generic import TemplateView

from apps.events.models import Event
from apps.guests.models import Guest
from apps.scanner.models import ScanLog


class DashboardHomeView(LoginRequiredMixin, TemplateView):
	template_name = 'dashboard/home.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		events = Event.objects.filter(owner=self.request.user)
		guests = Guest.objects.filter(event__owner=self.request.user)
		context['stats'] = {
			'events': events.count(),
			'guests': guests.count(),
			'sent': guests.filter(status=Guest.Status.SENT).count(),
			'present': guests.filter(status=Guest.Status.PRESENT).count(),
			'absent': guests.filter(status=Guest.Status.ABSENT).count(),
			'pending': guests.filter(status=Guest.Status.PENDING).count(),
			'scanned': ScanLog.objects.filter(event__owner=self.request.user, status=ScanLog.ScanStatus.ALLOWED).count(),
		}
		context['event_breakdown'] = events.annotate(total_guests=Count('guests')).order_by('-event_date')[:5]
		context['guest_mix'] = guests.values('category').annotate(total=Count('id')).order_by('-total')
		return context


class StatisticsView(LoginRequiredMixin, TemplateView):
	template_name = 'dashboard/statistics.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['events'] = Event.objects.filter(owner=self.request.user).annotate(total_guests=Count('guests'))
		context['scans'] = ScanLog.objects.filter(event__owner=self.request.user).select_related('event', 'guest')[:20]
		return context
