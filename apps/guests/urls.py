from django.urls import path

from apps.guests.views import (
    GuestCreateView,
    GuestDeleteView,
    GuestDetailView,
    GuestImportMappingView,
    GuestImportUploadView,
    GuestListView,
    GuestUpdateView,
)

app_name = 'guests'

urlpatterns = [
    path('', GuestListView.as_view(), name='list'),
    path('create/', GuestCreateView.as_view(), name='create'),
    path('import/', GuestImportUploadView.as_view(), name='import-upload'),
    path('import/mapping/', GuestImportMappingView.as_view(), name='import-map'),
    path('<uuid:pk>/', GuestDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', GuestUpdateView.as_view(), name='edit'),
    path('<uuid:pk>/delete/', GuestDeleteView.as_view(), name='delete'),
]