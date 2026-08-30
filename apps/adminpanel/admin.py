from django.contrib import admin

from apps.adminpanel.models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
	list_display = ('action', 'actor', 'target_type', 'target_identifier', 'created_at')
	list_filter = ('target_type', 'created_at')
	search_fields = ('action', 'target_identifier', 'actor__email')
	readonly_fields = ('actor', 'action', 'target_type', 'target_identifier', 'metadata', 'created_at', 'updated_at')
