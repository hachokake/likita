from django.urls import path

from apps.accounts.views import BosanganiLoginView, BosanganiLogoutView, ProfileView, SettingsView, SignUpView

app_name = 'accounts'

urlpatterns = [
    path('login/', BosanganiLoginView.as_view(), name='login'),
    path('logout/', BosanganiLogoutView.as_view(), name='logout'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('settings/', SettingsView.as_view(), name='settings'),
]