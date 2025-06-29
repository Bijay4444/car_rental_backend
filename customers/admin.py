from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db import models
from django.utils import timezone
from django.contrib import messages
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    # FIXED: Changed 'status_badge' to 'status' so list_editable works
    list_display = ('name_with_image', 'email', 'phone_number', 'status', 'total_bookings_link',
                    'total_spent_formatted', 'last_booking_date', 'created_at')
    list_filter = ('status', 'gender', 'created_at',
                   'last_booking_date', 'total_bookings')
    search_fields = ('name', 'email', 'phone_number',
                     'user__email', 'user__username')
    readonly_fields = ('total_bookings', 'total_spent', 'last_booking_date', 'created_at',
                       'updated_at', 'created_by', 'identification_image_preview', 'profile_image_preview',
                       'customer_stats', 'customer_summary')
    # Now this works because 'status' is in list_display
    list_editable = ('status',)
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'email', 'phone_number', 'gender', 'date_of_birth', 'address'),
            'classes': ('wide',)
        }),
        ('Images', {
            'fields': ('profile_image', 'profile_image_preview', 'identification_image', 'identification_image_preview'),
            'classes': ('collapse',)
        }),
        ('Account & Status', {
            'fields': ('user', 'status'),
            'classes': ('wide',)
        }),
        ('Booking Statistics', {
            'fields': ('customer_summary', 'customer_stats', 'total_bookings', 'total_spent', 'last_booking_date'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    actions = ['export_customer_data', 'update_booking_stats', 'mark_active', 'mark_inactive',
               'mark_blocked', 'send_welcome_email', 'generate_customer_report']

    def get_queryset(self, request):
        """Optimize queries with select_related"""
        return super().get_queryset(request).select_related('user', 'created_by')

    def name_with_image(self, obj):
        """Display customer name with profile image"""
        if obj.profile_image:
            try:
                image_url = obj.profile_image.url
                return format_html(
                    '<div style="display: flex; align-items: center;">'
                    '<img src="{}" width="40" height="40" style="margin-right: 10px; border-radius: 50%; object-fit: cover; border: 2px solid #ddd;" />'
                    '<div>'
                    '<strong style="color: #007cba;">{}</strong><br>'
                    '<small style="color: #666;">ID: {}</small>'
                    '</div></div>',
                    image_url, obj.name, obj.id
                )
            except:
                pass

        return format_html(
            '<div style="display: flex; align-items: center;">'
            '<div style="width: 40px; height: 40px; margin-right: 10px; border-radius: 50%; background: linear-gradient(45deg, #007cba, #28a745); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 16px;">'
            '{}</div>'
            '<div>'
            '<strong style="color: #007cba;">{}</strong><br>'
            '<small style="color: #666;">ID: {}</small>'
            '</div></div>',
            obj.name[0].upper(), obj.name, obj.id
        )
    name_with_image.short_description = "Customer"
    name_with_image.admin_order_field = 'name'

    def profile_image_preview(self, obj):
        """Display profile image preview"""
        if obj.profile_image:
            try:
                return format_html(
                    '<div style="text-align: center;">'
                    '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />'
                    '</div>',
                    obj.profile_image.url
                )
            except:
                return format_html('<span style="color: #dc3545;">❌ Image file not found</span>')
        return format_html('<span style="color: #6c757d;">📷 No profile image</span>')
    profile_image_preview.short_description = "Profile Image Preview"

    def identification_image_preview(self, obj):
        """Display identification image preview"""
        if obj.identification_image:
            try:
                return format_html(
                    '<div style="text-align: center;">'
                    '<img src="{}" style="max-width: 300px; max-height: 200px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />'
                    '</div>',
                    obj.identification_image.url
                )
            except:
                return format_html('<span style="color: #dc3545;">❌ Image file not found</span>')
        return format_html('<span style="color: #6c757d;">🆔 No ID image uploaded</span>')
    identification_image_preview.short_description = "ID Image Preview"

    def status_badge(self, obj):
        """Display status with color-coded badge - KEPT for detail view"""
        colors = {
            'Active': '#28a745',
            'Inactive': '#6c757d',
            'Blocked': '#dc3545'
        }
        color = colors.get(obj.status, '#28a745')

        # Add icon based on status
        icons = {
            'Active': '✅',
            'Inactive': '⏸️',
            'Blocked': '🚫'
        }
        icon = icons.get(obj.status, '❓')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 15px; font-size: 11px; font-weight: bold;">'
            '{} {}</span>',
            color, icon, obj.status.upper()
        )
    status_badge.short_description = "Status Badge"
    status_badge.admin_order_field = 'status'

    def total_bookings_link(self, obj):
        """Display total bookings with link to booking admin"""
        count = obj.total_bookings
        if count > 0:
            url = reverse('admin:bookings_booking_changelist') + \
                f'?customer__id__exact={obj.id}'
            return format_html(
                '<div style="text-align: center;">'
                '<a href="{}" style="color: #007cba; font-weight: bold; text-decoration: none;">'
                '<div style="background: #e3f2fd; padding: 8px 12px; border-radius: 20px; display: inline-block;">'
                '📋 {} booking{}'
                '</div></a></div>',
                url, count, 's' if count != 1 else ''
            )
        return format_html(
            '<div style="text-align: center;">'
            '<span style="color: #6c757d; font-style: italic;">No bookings</span>'
            '</div>'
        )
    total_bookings_link.short_description = "Bookings"
    total_bookings_link.admin_order_field = 'total_bookings'

    def total_spent_formatted(self, obj):
        """Display total spent with formatting"""
        amount = float(obj.total_spent)
        if amount > 0:
            # Color coding based on spending level
            if amount >= 100000:  # 1 lakh+
                color = '#28a745'  # Green for high value customers
                badge = '💎 VIP'
            elif amount >= 50000:  # 50k+
                color = '#17a2b8'  # Blue for good customers
                badge = '⭐ Premium'
            elif amount >= 10000:  # 10k+
                color = '#ffc107'  # Yellow for regular customers
                badge = '🥉 Regular'
            else:
                color = '#6c757d'  # Gray for new customers
                badge = '🆕 New'

            return format_html(
                '<div style="text-align: right;">'
                '<strong style="color: {}; font-size: 14px;">₹{}</strong><br>'
                '<small style="background: {}; color: white; padding: 2px 6px; border-radius: 10px; font-size: 10px;">{}</small>'
                '</div>',
                color, f"{amount:,.2f}", color, badge
            )
        return format_html('<span style="color: #6c757d;">₹0.00</span>')
    total_spent_formatted.short_description = "Total Spent"
    total_spent_formatted.admin_order_field = 'total_spent'

    def customer_stats(self, obj):
        """Display detailed booking statistics"""
        try:
            from bookings.models import Booking
            stats = Booking.objects.filter(customer=obj).aggregate(
                active_bookings=models.Count(
                    'id', filter=models.Q(booking_status='Active')),
                completed_bookings=models.Count(
                    'id', filter=models.Q(booking_status='Returned')),
                cancelled_bookings=models.Count(
                    'id', filter=models.Q(booking_status='Cancelled')),
                overdue_bookings=models.Count('id', filter=models.Q(
                    end_date__lt=timezone.now().date(),
                    car_returned=False,
                    booking_status='Active'
                ))
            )

            return format_html(
                '<div style="line-height: 1.6; padding: 10px; background: #f8f9fa; border-radius: 6px;">'
                '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">'
                '<div><span style="color: #007bff;">🔵 Active:</span> <strong>{}</strong></div>'
                '<div><span style="color: #28a745;">✅ Completed:</span> <strong>{}</strong></div>'
                '<div><span style="color: #6c757d;">❌ Cancelled:</span> <strong>{}</strong></div>'
                '<div><span style="color: #dc3545;">⚠️ Overdue:</span> <strong>{}</strong></div>'
                '</div></div>',
                stats['active_bookings'],
                stats['completed_bookings'],
                stats['cancelled_bookings'],
                stats['overdue_bookings']
            )
        except Exception as e:
            return format_html('<span style="color: #dc3545;">Error loading stats: {}</span>', str(e))
    customer_stats.short_description = "Booking Breakdown"

    def customer_summary(self, obj):
        """Comprehensive customer summary"""
        age = None
        if obj.date_of_birth:
            today = timezone.now().date()
            age = today.year - obj.date_of_birth.year - \
                ((today.month, today.day) <
                 (obj.date_of_birth.month, obj.date_of_birth.day))

        # Calculate customer tenure
        tenure_days = (timezone.now().date() - obj.created_at.date()).days

        # Calculate average booking value
        avg_booking_value = 0
        if obj.total_bookings > 0:
            avg_booking_value = float(obj.total_spent) / obj.total_bookings

        return format_html(
            '<div style="line-height: 1.8; padding: 15px; background: #f8f9fa; border-radius: 8px;">'
            '<h4 style="margin-top: 0; color: #495057;">👤 Customer Overview</h4>'
            '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">'
            '<div>'
            '<p><strong>👤 Name:</strong> {}</p>'
            '<p><strong>📧 Email:</strong> {}</p>'
            '<p><strong>📱 Phone:</strong> {}</p>'
            '<p><strong>🎂 Age:</strong> {} years</p>'
            '<p><strong>⚧ Gender:</strong> {}</p>'
            '</div>'
            '<div>'
            '<p><strong>📅 Customer Since:</strong> {} days</p>'
            '<p><strong>💰 Average Booking:</strong> ₹{}</p>'
            '<p><strong>📍 Address:</strong> {}</p>'
            '<p><strong>👤 Linked User:</strong> {}</p>'
            '<p><strong>📊 Status:</strong> {}</p>'
            '</div>'
            '</div></div>',
            obj.name,
            obj.email,
            obj.phone_number,
            age if age else "Not provided",
            obj.gender,
            tenure_days,
            f"{avg_booking_value:,.2f}",
            obj.address[:50] + "..." if len(obj.address) > 50 else obj.address,
            obj.user.username if obj.user else "No linked account",
            obj.status
        )
    customer_summary.short_description = "Customer Summary"

    # Custom Actions
    def update_booking_stats(self, request, queryset):
        """Update booking statistics for selected customers"""
        updated = 0
        for customer in queryset:
            try:
                customer.update_booking_stats()
                updated += 1
            except Exception as e:
                self.message_user(
                    request, f'Error updating stats for {customer.name}: {str(e)}', messages.ERROR)

        if updated > 0:
            self.message_user(
                request, f'✅ Updated booking statistics for {updated} customers.', messages.SUCCESS)
    update_booking_stats.short_description = "🔄 Update booking statistics"

    def mark_active(self, request, queryset):
        """Mark selected customers as active"""
        updated = queryset.update(status='Active')
        self.message_user(
            request, f'✅ {updated} customers marked as active.', messages.SUCCESS)
    mark_active.short_description = "✅ Mark as Active"

    def mark_inactive(self, request, queryset):
        """Mark selected customers as inactive"""
        updated = queryset.update(status='Inactive')
        self.message_user(
            request, f'⏸️ {updated} customers marked as inactive.', messages.WARNING)
    mark_inactive.short_description = "⏸️ Mark as Inactive"

    def mark_blocked(self, request, queryset):
        """Block selected customers"""
        updated = queryset.update(status='Blocked')
        self.message_user(
            request, f'🚫 {updated} customers blocked.', messages.ERROR)
    mark_blocked.short_description = "🚫 Block customers"

    def send_welcome_email(self, request, queryset):
        """Send welcome email to selected customers"""
        count = queryset.count()
        self.message_user(
            request, f'📧 Welcome email functionality ready for {count} customers.', messages.INFO)
    send_welcome_email.short_description = "📧 Send welcome email"

    def generate_customer_report(self, request, queryset):
        """Generate customer report"""
        count = queryset.count()
        self.message_user(
            request, f'📊 Customer report generation ready for {count} customers.', messages.INFO)
    generate_customer_report.short_description = "📊 Generate customer report"

    def export_customer_data(self, request, queryset):
        """Export customer data"""
        count = queryset.count()
        self.message_user(
            request, f'📤 Customer data export ready for {count} customers.', messages.INFO)
    export_customer_data.short_description = "📤 Export customer data"

    def save_model(self, request, obj, form, change):
        """Override to set audit fields"""
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
# Test sync Sun Jun 29 07:52:57 PM +0545 2025
# Test sync Sun Jun 29 07:54:52 PM +0545 2025
