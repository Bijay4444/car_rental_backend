from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'full_name', 'is_staff', 'is_active', 'is_fingerprint_enabled',
                    'user_image_preview', 'date_joined', 'last_login')
    list_filter = ('is_staff', 'is_active', 'is_superuser',
                   'is_fingerprint_enabled', 'date_joined', 'last_login')
    search_fields = ('email', 'full_name', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login',
                       'user_image_display', 'device_info_display', 'user_stats')
    list_editable = ('is_active', 'is_fingerprint_enabled')
    list_per_page = 25
    date_hierarchy = 'date_joined'

    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'password')
        }),
        ('Personal Information', {
            'fields': ('full_name', 'first_name', 'last_name', 'user_image_url', 'user_image_display')
        }),
        ('Security Settings', {
            'fields': ('is_fingerprint_enabled', 'login_device_info', 'device_info_display')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('User Statistics', {
            'fields': ('user_stats',),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        ('Create New User', {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2', 'is_staff', 'is_active', 'is_fingerprint_enabled')
        }),
    )

    def user_image_preview(self, obj):
        """Display small user image in list view"""
        if obj.user_image_url:
            try:
                return format_html(
                    '<img src="{}" width="40" height="40" style="border-radius: 50%; object-fit: cover;" />',
                    obj.user_image_url.url if hasattr(
                        obj.user_image_url, 'url') else obj.user_image_url
                )
            except:
                return format_html('<span style="color: #dc3545;">❌ Image Error</span>')
        return format_html('<span style="color: #6c757d;">📷 No Image</span>')
    user_image_preview.short_description = "Profile"

    def user_image_display(self, obj):
        """Display large user image in detail view"""
        if obj.user_image_url:
            try:
                return format_html(
                    '<div style="text-align: center;">'
                    '<img src="{}" width="150" height="150" style="border-radius: 10px; object-fit: cover; border: 2px solid #dee2e6;" />'
                    '<br><small style="color: #6c757d;">Profile Image</small></div>',
                    obj.user_image_url.url if hasattr(
                        obj.user_image_url, 'url') else obj.user_image_url
                )
            except:
                return format_html('<span style="color: #dc3545;">❌ Image Error - Check file path</span>')
        return format_html('<span style="color: #6c757d;">📷 No Profile Image</span>')
    user_image_display.short_description = "Profile Image"

    def device_info_display(self, obj):
        """Display login device information in a formatted way"""
        if obj.login_device_info:
            device_info = obj.login_device_info
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px; line-height: 1.5;">'
                '<strong>Device Info:</strong><br>'
                '{}</div>',
                '<br>'.join(
                    [f'<strong>{k}:</strong> {v}' for k, v in device_info.items()])
            )
        return format_html('<em style="color: #6c757d;">No device info recorded</em>')
    device_info_display.short_description = "Login Device Info"

    def user_stats(self, obj):
        """Display user statistics (bookings, activity, etc.)"""
        try:
            # Get user-related statistics
            from customers.models import Customer
            from bookings.models import Booking

            stats_html = '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px; line-height: 1.5;">'

            # Check if user has a customer profile
            try:
                customer = Customer.objects.get(user=obj)
                total_bookings = customer.total_bookings
                total_spent = customer.total_spent

                stats_html += f'<strong>Customer Profile:</strong> ✅<br>'
                stats_html += f'<strong>Total Bookings:</strong> {total_bookings}<br>'
                stats_html += f'<strong>Total Spent:</strong> ₹{total_spent:,.2f}<br>'

                # Get recent booking activity
                recent_bookings = Booking.objects.filter(
                    customer=customer).order_by('-created_at')[:3]
                if recent_bookings:
                    stats_html += '<strong>Recent Bookings:</strong><br>'
                    for booking in recent_bookings:
                        stats_html += f'• {booking.booking_id} ({booking.start_date})<br>'

            except Customer.DoesNotExist:
                stats_html += '<strong>Customer Profile:</strong> ❌ Not linked<br>'

            # User account info
            stats_html += f'<strong>Staff User:</strong> {"✅" if obj.is_staff else "❌"}<br>'
            stats_html += f'<strong>Superuser:</strong> {"✅" if obj.is_superuser else "❌"}<br>'
            stats_html += f'<strong>Groups:</strong> {obj.groups.count()}<br>'

            stats_html += '</div>'
            return format_html(stats_html)

        except Exception as e:
            return format_html('<span style="color: #dc3545;">Error loading stats: {}</span>', str(e))
    user_stats.short_description = "User Statistics"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related().prefetch_related('groups', 'user_permissions')

    # Custom Actions
    actions = ['activate_users', 'deactivate_users', 'enable_fingerprint', 'disable_fingerprint',
               'make_staff', 'remove_staff', 'send_welcome_email', 'export_user_data']

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(
            request, f'✅ {updated} users were successfully activated.')
    activate_users.short_description = "✅ Activate selected users"

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request, f'❌ {updated} users were successfully deactivated.')
    deactivate_users.short_description = "❌ Deactivate selected users"

    def enable_fingerprint(self, request, queryset):
        updated = queryset.update(is_fingerprint_enabled=True)
        self.message_user(
            request, f'👆 Fingerprint enabled for {updated} users.')
    enable_fingerprint.short_description = "👆 Enable fingerprint authentication"

    def disable_fingerprint(self, request, queryset):
        updated = queryset.update(is_fingerprint_enabled=False)
        self.message_user(
            request, f'🚫 Fingerprint disabled for {updated} users.')
    disable_fingerprint.short_description = "🚫 Disable fingerprint authentication"

    def make_staff(self, request, queryset):
        updated = queryset.update(is_staff=True)
        self.message_user(request, f'👑 {updated} users granted staff access.')
    make_staff.short_description = "👑 Grant staff access"

    def remove_staff(self, request, queryset):
        # Don't remove staff from superusers
        updated = queryset.filter(is_superuser=False).update(is_staff=False)
        self.message_user(
            request, f'👤 Staff access removed from {updated} users (superusers skipped).')
    remove_staff.short_description = "👤 Remove staff access"

    def send_welcome_email(self, request, queryset):
        # Placeholder for email functionality
        count = queryset.count()
        self.message_user(
            request, f'📧 Welcome email functionality ready for {count} users.')
    send_welcome_email.short_description = "📧 Send welcome email"

    def export_user_data(self, request, queryset):
        # Placeholder for export functionality
        count = queryset.count()
        self.message_user(
            request, f'📊 Export functionality ready for {count} users.')
    export_user_data.short_description = "📊 Export user data"

    def save_model(self, request, obj, form, change):
        """Override to handle custom logic when saving users"""
        if not change:  # Creating new user
            # You can add logic here for new user creation
            pass
        super().save_model(request, obj, form, change)

    # Custom list filters
    def get_list_filter(self, request):
        list_filter = list(self.list_filter)

        # Add custom filters based on user role
        if request.user.is_superuser:
            list_filter.append('groups')

        return tuple(list_filter)

    # Customize form display based on user permissions
    def get_fieldsets(self, request, obj=None):
        fieldsets = list(self.fieldsets)

        # If user is not superuser, limit permission access
        if not request.user.is_superuser:
            for i, (name, options) in enumerate(fieldsets):
                if name == 'Permissions':
                    fieldsets[i] = ('Permissions', {
                        'fields': ('is_active',),
                        'classes': ('collapse',)
                    })
                    break

        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(self.readonly_fields)

        # If editing existing user and not superuser, make certain fields readonly
        if obj and not request.user.is_superuser:
            readonly_fields.extend(
                ['is_staff', 'is_superuser', 'groups', 'user_permissions'])

        return readonly_fields

    # Add custom CSS and JS
    class Media:
        css = {
            'all': (
                'admin/css/custom_user_admin.css',  # You can add custom CSS
            )
        }
        js = (
            'admin/js/custom_user_admin.js',  # You can add custom JS
        )


# Optional: Custom admin site title
admin.site.site_header = "Car Rental Management"
admin.site.site_title = "Car Rental Admin"
admin.site.index_title = "Welcome to Car Rental Management"
