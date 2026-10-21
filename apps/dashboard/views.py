from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.utils import timezone
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
		breakdown = list(events.annotate(total_guests=Count('guests')).order_by('-event_date')[:5])
		max_guests = max((event.total_guests for event in breakdown), default=0) or 1
		for event in breakdown:
			event.guest_ratio = round(event.total_guests * 100 / max_guests)
		context['event_breakdown'] = breakdown
		context['upcoming_events'] = events.filter(event_date__gte=timezone.localdate()).order_by('event_date', 'event_time')[:4]
		labels = dict(Guest.Category.choices)
		context['guest_mix'] = [
			{'label': labels.get(item['category'], item['category'] or 'Non classé'), 'total': item['total']}
			for item in guests.values('category').annotate(total=Count('id')).order_by('-total')
		]
		context['recent_notifications'] = self.request.user.notifications.select_related('event')[:5]
		return context


class StatisticsView(LoginRequiredMixin, TemplateView):
	template_name = 'dashboard/statistics.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['events'] = Event.objects.filter(owner=self.request.user).annotate(total_guests=Count('guests')).order_by('-event_date')
		context['scans'] = ScanLog.objects.filter(event__owner=self.request.user).select_related('event', 'guest').order_by('-scanned_at')[:20]
		return context
