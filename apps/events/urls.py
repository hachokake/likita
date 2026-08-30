from django.urls import path

from apps.events.views import (
    EventArchiveView,
    EventCreateView,
    EventDetailView,
    EventListView,
    EventPublishView,
    EventUpdateView,
)

app_name = 'events'

urlpatterns = [
    path('', EventListView.as_view(), name='list'),
    path('create/', EventCreateView.as_view(), name='create'),
    path('<slug:slug>/', EventDetailView.as_view(), name='detail'),
    path('<slug:slug>/edit/', EventUpdateView.as_view(), name='edit'),
    path('<slug:slug>/publish/', EventPublishView.as_view(), name='publish'),
    path('<slug:slug>/archive/', EventArchiveView.as_view(), name='archive'),
]