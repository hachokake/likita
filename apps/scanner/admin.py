from django.contrib import admin

from apps.scanner.models import ScanLog


@admin.register(ScanLog)
class ScanLogAdmin(admin.ModelAdmin):
	list_display = ('event', 'guest', 'status', 'scanner_label', 'scanned_by', 'scanned_at')
	list_filter = ('status', 'event', 'scanned_at')
	search_fields = ('guest__full_name', 'event__name', 'scanner_label', 'device_info')
	readonly_fields = ('event', 'guest', 'qr_code', 'scanned_by', 'scanner_label', 'device_info', 'status', 'scanned_at')
