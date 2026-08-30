from django.urls import path

from apps.invitations.views import InvitationPreviewView, SendInvitationView

app_name = 'invitations'

urlpatterns = [
    path('public/<slug:token>/', InvitationPreviewView.as_view(), name='public'),
    path('send/<slug:token>/', SendInvitationView.as_view(), name='send'),
]