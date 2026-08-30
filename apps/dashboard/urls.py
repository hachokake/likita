from django.urls import path

from apps.dashboard.views import DashboardHomeView, StatisticsView

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardHomeView.as_view(), name='home'),
    path('statistics/', StatisticsView.as_view(), name='statistics'),
]