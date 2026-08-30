from django.urls import path

from apps.rsvp.views import PublicRSVPUpdateView

app_name = 'rsvp'

urlpatterns = [
    path('respond/<slug:token>/', PublicRSVPUpdateView.as_view(), name='respond'),
]