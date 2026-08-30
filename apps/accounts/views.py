from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from apps.accounts.forms import BosanganiAuthenticationForm, SignUpForm


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')


class BosanganiLoginView(LoginView):
    authentication_form = BosanganiAuthenticationForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = False


class BosanganiLogoutView(LogoutView):
    next_page = reverse_lazy('core:home')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/settings.html'
