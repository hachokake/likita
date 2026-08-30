from django.urls import path

from apps.adminpanel.views import (
    AdminDashboardView,
    AdminEventActionView,
    AdminEventDetailView,
    AdminEventListView,
    AdminUserActionView,
    AdminUserDetailView,
    AdminUserListView,
)

app_name = 'adminpanel'

urlpatterns = [
    path('', AdminDashboardView.as_view(), name='dashboard'),
    path('utilisateurs/', AdminUserListView.as_view(), name='users'),
    path('utilisateurs/<uuid:pk>/', AdminUserDetailView.as_view(), name='user-detail'),
    path('utilisateurs/<uuid:pk>/action/<slug:action>/', AdminUserActionView.as_view(), name='user-action'),
    path('evenements/', AdminEventListView.as_view(), name='events'),
    path('evenements/<uuid:pk>/', AdminEventDetailView.as_view(), name='event-detail'),
    path('evenements/<uuid:pk>/action/<slug:action>/', AdminEventActionView.as_view(), name='event-action'),
]