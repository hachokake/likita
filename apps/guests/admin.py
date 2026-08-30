from django.contrib import admin

from apps.guests.models import Guest


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
	list_display = ('full_name', 'event', 'category', 'status', 'whatsapp_number', 'allowed_companions', 'reserved_table')
	list_filter = ('status', 'category', 'event')
	search_fields = ('full_name', 'whatsapp_number', 'email', 'event__name')
	autocomplete_fields = ('event',)
	actions = ('mark_sent', 'mark_present', 'mark_absent')

	@admin.action(description='Marquer comme invitation envoyee')
	def mark_sent(self, request, queryset):
		queryset.update(status=Guest.Status.SENT)

	@admin.action(description='Marquer comme present')
	def mark_present(self, request, queryset):
		queryset.update(status=Guest.Status.PRESENT)

	@admin.action(description='Marquer comme absent')
	def mark_absent(self, request, queryset):
		queryset.update(status=Guest.Status.ABSENT)
