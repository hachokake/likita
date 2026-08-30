from django.contrib import admin

from apps.events.models import Event, EventProgram, Gallery, Theme


class EventProgramInline(admin.TabularInline):
	model = EventProgram
	extra = 0


class GalleryInline(admin.TabularInline):
	model = Gallery
	extra = 0


class ThemeInline(admin.StackedInline):
	model = Theme
	extra = 0
	max_num = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
	list_display = ('name', 'owner', 'event_type', 'status', 'event_date', 'max_guests', 'allow_multiple_entries')
	list_filter = ('status', 'event_type', 'allow_multiple_entries', 'event_date')
	search_fields = ('name', 'host_names', 'address', 'owner__email')
	readonly_fields = ('slug', 'created_at', 'updated_at', 'published_at')
	inlines = (ThemeInline, EventProgramInline, GalleryInline)
	actions = ('publish_events', 'archive_events')

	@admin.action(description='Publier les evenements selectionnes')
	def publish_events(self, request, queryset):
		queryset.update(status=Event.Status.PUBLISHED)

	@admin.action(description='Archiver les evenements selectionnes')
	def archive_events(self, request, queryset):
		queryset.update(status=Event.Status.ARCHIVED)


@admin.register(EventProgram)
class EventProgramAdmin(admin.ModelAdmin):
	list_display = ('title', 'event', 'start_at', 'end_at', 'sort_order')
	list_filter = ('event',)
	search_fields = ('title', 'event__name', 'location')


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
	list_display = ('event', 'primary_color', 'secondary_color', 'accent_color', 'text_color')
	search_fields = ('event__name',)


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
	list_display = ('event', 'caption', 'is_organizer_photo', 'sort_order')
	list_filter = ('is_organizer_photo', 'event')
	search_fields = ('event__name', 'caption')
