from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from apps.accounts.models import User, UserSettings


admin.site.site_header = 'Likita Control Room'
admin.site.site_title = 'Likita Admin'
admin.site.index_title = 'Pilotage de la plateforme'
admin.site.enable_nav_sidebar = True


@admin.register(User)
class BosanganiUserAdmin(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'subscription_badge', 'is_suspended', 'is_staff', 'last_login')
    list_filter = ('subscription_tier', 'is_suspended', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number', 'company_name')
    readonly_fields = ('last_login', 'date_joined', 'last_seen_at')
    fieldsets = UserAdmin.fieldsets + (
        ('Likita', {'fields': ('phone_number', 'company_name', 'subscription_tier', 'is_suspended', 'last_seen_at')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Likita', {'fields': ('email', 'phone_number', 'company_name')}),
    )

    actions = ('suspend_users', 'reactivate_users', 'promote_to_pro', 'promote_to_premium')

    @admin.display(description='Abonnement')
    def subscription_badge(self, obj):
        palette = {
            obj.SubscriptionTier.FREE: '#64748b',
            obj.SubscriptionTier.PRO: '#c1121f',
            obj.SubscriptionTier.PREMIUM: '#f59e0b',
        }
        color = palette.get(obj.subscription_tier, '#64748b')
        return format_html(
            '<span style="padding:4px 10px;border-radius:999px;background:{}22;color:{};font-weight:700;">{}</span>',
            color,
            color,
            obj.get_subscription_tier_display(),
        )

    @admin.action(description='Suspendre les utilisateurs selectionnes')
    def suspend_users(self, request, queryset):
        queryset.update(is_suspended=True)

    @admin.action(description='Reactiver les utilisateurs selectionnes')
    def reactivate_users(self, request, queryset):
        queryset.update(is_suspended=False)

    @admin.action(description='Passer les comptes en Pro')
    def promote_to_pro(self, request, queryset):
        queryset.update(subscription_tier=User.SubscriptionTier.PRO)

    @admin.action(description='Passer les comptes en Premium')
    def promote_to_premium(self, request, queryset):
        queryset.update(subscription_tier=User.SubscriptionTier.PREMIUM)


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'locale', 'timezone', 'email_notifications', 'whatsapp_notifications', 'scan_alerts')
    list_filter = ('locale', 'email_notifications', 'whatsapp_notifications', 'scan_alerts')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
