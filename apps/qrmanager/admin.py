from django.contrib import admin

from apps.qrmanager.models import QRCode


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
	list_display = ('guest', 'event', 'is_active', 'scan_count', 'last_scanned_at')
	list_filter = ('is_active', 'event')
	search_fields = ('guest__full_name', 'guest__whatsapp_number', 'token')
	readonly_fields = ('token', 'scan_count', 'last_scanned_at', 'image')
	actions = ('activate_codes', 'deactivate_codes')

	@admin.action(description='Activer les QR selectionnes')
	def activate_codes(self, request, queryset):
		queryset.update(is_active=True)

	@admin.action(description='Desactiver les QR selectionnes')
	def deactivate_codes(self, request, queryset):
		queryset.update(is_active=False)
