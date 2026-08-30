from django.shortcuts import render
from django.views.generic import TemplateView

from apps.events.models import Event


class HomeView(TemplateView):
	template_name = 'core/home.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['featured_events'] = Event.objects.filter(status=Event.Status.PUBLISHED).select_related('theme', 'owner')[:3]
		return context


def error_404(request, exception=None):
	return render(request, 'errors/404.html', status=404)


def error_500(request):
	return render(request, 'errors/500.html', status=500)
