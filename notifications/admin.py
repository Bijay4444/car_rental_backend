from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import NotificationToken

@admin.register(NotificationToken)
class NotificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'device_type_badge', 'token_preview', 'active_status', 'created_at')
    list_filter = ('device_type', 'created_at')
    search_fields = ('user__email', 'user__full_name', 'token')
    readonly_fields = ('created_at', 'updated_at', 'token_full')
    # Remove list_editable for now
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User & Device', {
            'fields': ('user', 'device_type', 'device_name')
        }),
        ('Token Information', {
            'fields': ('token_full', 'token')
        }),
        ('Usage Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['test_push_notification']
    
    def user_link(self, obj):
        url = reverse('admin:authentication_customuser_change', args=[obj.user.id])
        return format_html('<a href="{}" style="color: #007cba;">{}</a>', url, obj.user.full_name or obj.user.email)
    user_link.short_description = "User"
    user_link.admin_order_field = 'user__full_name'
    
    def device_type_badge(self, obj):
        colors = {
            'android': '#3ddc84',
            'ios': '#007aff',
            'web': '#ff6b35'
        }
        color = colors.get(obj.device_type.lower())
        return format_html(
            '<span style="background-color: {} padding: 3px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color, obj.device_type.upper()
        )
    device_type_badge.short_description = "Device Type"
    device_type_badge.admin_order_field = 'device_type'
    
    def token_preview(self, obj):
        if obj.token:
            preview = obj.token[:20] + '...' if len(obj.token) > 20 else obj.token
            return format_html('<code style=" padding: 2px 4px;">{}</code>', preview)
        return "No token"
    token_preview.short_description = "Token Preview"
    
    def active_status(self, obj):
        # Since is_active might not exist, use a default
        is_active = getattr(obj, 'is_active', True)
        color = 'green' if is_active else 'red'
        status = 'Active' if is_active else 'Inactive'
        return format_html('<span style="color: {};">{}</span>', color, status)
    active_status.short_description = "Status"
    
    def token_full(self, obj):
        if obj.token:
            return format_html('<textarea readonly style="width: 100%; height: 100px;">{}</textarea>', obj.token)
        return "No token"
    token_full.short_description = "Full Token"
    
    def test_push_notification(self, request, queryset):
        # This would integrate with your push notification service
        count = queryset.count()
        self.message_user(request, f'Test notification would be sent to {count} devices.')
    test_push_notification.short_description = "Send test notification"