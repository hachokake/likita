from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.api.views import EventViewSet, GuestViewSet, InvitationViewSet, NotificationViewSet

app_name = 'api'

router = DefaultRouter()
router.register('events', EventViewSet, basename='events')
router.register('guests', GuestViewSet, basename='guests')
router.register('invitations', InvitationViewSet, basename='invitations')
router.register('notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('', include(router.urls)),
]