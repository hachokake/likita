from django.contrib import admin

from apps.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ('title', 'user', 'kind', 'is_read', 'created_at')
	list_filter = ('kind', 'is_read', 'created_at')
	search_fields = ('title', 'body', 'user__email', 'event__name', 'guest__full_name')
	actions = ('mark_read', 'mark_unread')

	@admin.action(description='Marquer comme lues')
	def mark_read(self, request, queryset):
		queryset.update(is_read=True)

	@admin.action(description='Marquer comme non lues')
	def mark_unread(self, request, queryset):
		queryset.update(is_read=False)
