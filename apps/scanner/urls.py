from django.urls import path

from apps.scanner.views import QRScannerView, ScanValidationView

app_name = 'scanner'

urlpatterns = [
    path('', QRScannerView.as_view(), name='home'),
    path('validate/', ScanValidationView.as_view(), name='validate'),
]