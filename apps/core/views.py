from django.shortcuts import render
from django.views.generic import TemplateView


class HomeView(TemplateView):
	template_name = 'core/home.html'


def error_404(request, exception=None):
	return render(request, 'errors/404.html', status=404)


def error_500(request):
	return render(request, 'errors/500.html', status=500)
