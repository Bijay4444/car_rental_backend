from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from .models import Car, CarDeleteReason


class CarDeleteReasonInline(admin.TabularInline):
    """Inline admin for car deletion reasons"""
    model = CarDeleteReason
    extra = 0
    readonly_fields = ('deleted_at', 'deleted_by')
    fields = ('reason', 'description', 'deleted_at', 'deleted_by')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        # Only allow adding deletion reasons if car is actually deleted
        return obj and obj.is_deleted if obj else False


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    # Fixed: Use 'fee' instead of 'fee_formatted' to allow inline editing
    list_display = ('car_name_with_image', 'type', 'fee', 'status', 'availability',
                    'insurance_status', 'tracker_status', 'active_bookings_count', 'total_revenue', 'created_at')
    list_filter = ('type', 'gearbox', 'status', 'availability', 'is_deleted', 'created_at',
                   'tracker_expiry_date', 'insurance_expiry_date')
    search_fields = ('car_name', 'color', 'type')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_at', 'deleted_by',
                       'car_image_preview', 'booking_stats', 'revenue_stats', 'insurance_tracker_status')
    # Now all fields are properly in list_display
    list_editable = ('fee', 'status', 'availability')
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('car_name', 'car_image', 'car_image_preview', 'fee', 'type')
        }),
        ('Specifications', {
            'fields': ('color', 'seats', 'mileage', 'gearbox', 'max_speed'),
            'classes': ('wide',)
        }),
        ('Tracking & Insurance', {
            'fields': ('tracker_expiry_date', 'insurance_expiry_date', 'insurance_tracker_status'),
            'classes': ('wide',)
        }),
        ('Insurance Coverage', {
            'fields': ('collision_damage_waiver', 'third_party_liability_insurance', 'optional_insurance_add_ons'),
            'classes': ('collapse',)
        }),
        ('Status & Availability', {
            'fields': ('status', 'availability'),
            'classes': ('wide',)
        }),
        ('Business Analytics', {
            'fields': ('booking_stats', 'revenue_stats'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by',
                       'is_deleted', 'deleted_at', 'deleted_by'),
            'classes': ('collapse',)
        }),
    )

    inlines = [CarDeleteReasonInline]
    actions = ['mark_available', 'mark_booked', 'mark_maintenance', 'soft_delete_cars',
               'bulk_update_insurance', 'generate_revenue_report', 'check_expiry_dates']

    def get_queryset(self, request):
        """Optimize queries with select_related and prefetch_related"""
        return super().get_queryset(request).select_related(
            'created_by', 'updated_by', 'deleted_by'
        ).prefetch_related('delete_reasons')

    def car_name_with_image(self, obj):
        """Display car name with thumbnail image"""
        if obj.car_image:
            try:
                return format_html(
                    '<div style="display: flex; align-items: center;">'
                    '<img src="{}" width="50" height="35" style="margin-right: 10px; border-radius: 5px; object-fit: cover; border: 1px solid #ddd;" />'
                    '<div>'
                    '<strong>{}</strong><br>'
                    '<small style="color: #666;">{}</small>'
                    '</div></div>',
                    obj.car_image.url,
                    obj.car_name,
                    f'{obj.color} • {obj.seats} seats'
                )
            except:
                return format_html(
                    '<div>'
                    '<strong>{}</strong><br>'
                    '<small style="color: #dc3545;">❌ Image Error</small>'
                    '</div>',
                    obj.car_name
                )
        return format_html(
            '<div>'
            '<strong>{}</strong><br>'
            '<small style="color: #666;">{}</small>'
            '</div>',
            obj.car_name,
            f'{obj.color} • {obj.seats} seats'
        )
    car_name_with_image.short_description = "Car Details"
    car_name_with_image.admin_order_field = 'car_name'

    def car_image_preview(self, obj):
        """Display large car image in detail view"""
        if obj.car_image:
            try:
                return format_html(
                    '<div style="text-align: center; margin: 10px 0;">'
                    '<img src="{}" style="max-width: 300px; max-height: 200px; border-radius: 10px; '
                    'object-fit: cover; border: 2px solid #dee2e6; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />'
                    '<br><small style="color: #6c757d; margin-top: 5px; display: block;">Car Image</small></div>',
                    obj.car_image.url
                )
            except:
                return format_html('<span style="color: #dc3545;">❌ Image file error - Check file path</span>')
        return format_html('<span style="color: #6c757d;">📷 No image uploaded</span>')
    car_image_preview.short_description = "Image Preview"

    def insurance_status(self, obj):
        """Display insurance expiry status"""
        from datetime import date, timedelta

        today = date.today()
        expiry = obj.insurance_expiry_date
        days_left = (expiry - today).days

        if days_left < 0:
            color = '#dc3545'
            status = f'Expired {abs(days_left)} days ago'
            icon = '❌'
        elif days_left <= 7:
            color = '#ffc107'
            status = f'Expires in {days_left} days'
            icon = '⚠️'
        elif days_left <= 30:
            color = '#fd7e14'
            status = f'{days_left} days left'
            icon = '⏰'
        else:
            color = '#28a745'
            status = f'{days_left} days left'
            icon = '✅'

        return format_html(
            '<div style="color: {}; font-size: 12px;">'
            '{} {}<br>'
            '<small>{}</small>'
            '</div>',
            color, icon, status, expiry.strftime('%d %b %Y')
        )
    insurance_status.short_description = "Insurance"
    insurance_status.admin_order_field = 'insurance_expiry_date'

    def tracker_status(self, obj):
        """Display tracker expiry status"""
        from datetime import date, timedelta

        today = date.today()
        expiry = obj.tracker_expiry_date
        days_left = (expiry - today).days

        if days_left < 0:
            color = '#dc3545'
            status = f'Expired {abs(days_left)} days ago'
            icon = '❌'
        elif days_left <= 7:
            color = '#ffc107'
            status = f'Expires in {days_left} days'
            icon = '⚠️'
        elif days_left <= 30:
            color = '#fd7e14'
            status = f'{days_left} days left'
            icon = '⏰'
        else:
            color = '#28a745'
            status = f'{days_left} days left'
            icon = '✅'

        return format_html(
            '<div style="color: {}; font-size: 12px;">'
            '{} {}<br>'
            '<small>{}</small>'
            '</div>',
            color, icon, status, expiry.strftime('%d %b %Y')
        )
    tracker_status.short_description = "Tracker"
    tracker_status.admin_order_field = 'tracker_expiry_date'

    def insurance_tracker_status(self, obj):
        """Combined insurance and tracker status for detail view"""
        from datetime import date

        today = date.today()

        insurance_days = (obj.insurance_expiry_date - today).days
        tracker_days = (obj.tracker_expiry_date - today).days

        def get_status_info(days, name, date_obj):
            if days < 0:
                return f'❌ {name}: Expired {abs(days)} days ago ({date_obj})'
            elif days <= 7:
                return f'🚨 {name}: Critical - {days} days left ({date_obj})'
            elif days <= 30:
                return f'⚠️ {name}: Warning - {days} days left ({date_obj})'
            else:
                return f'✅ {name}: Good - {days} days left ({date_obj})'

        return format_html(
            '<div style="line-height: 1.6; padding: 10px; border-radius: 5px;">'
            '{}<br>'
            '{}'
            '</div>',
            get_status_info(insurance_days, 'Insurance',
                            obj.insurance_expiry_date),
            get_status_info(tracker_days, 'Tracker', obj.tracker_expiry_date)
        )
    insurance_tracker_status.short_description = "Insurance & Tracker Status"

    def active_bookings_count(self, obj):
        """Display count of active bookings with link"""
        try:
            # Try to get bookings - adjust the field name based on your Booking model
            from bookings.models import Booking
            count = Booking.objects.filter(car=obj, car_returned=False).count()

            if count > 0:
                url = reverse('admin:bookings_booking_changelist') + \
                    f'?car__id__exact={obj.id}&car_returned__exact=0'
                return format_html('<a href="{}" style="color: #007cba; font-weight: bold;">{} active</a>', url, count)
            return format_html('<span style="color: #28a745;">✅ No active bookings</span>')
        except Exception as e:
            return format_html('<span style="color: #6c757d;">No booking data</span>')
    active_bookings_count.short_description = "Active Bookings"

    def total_revenue(self, obj):
        """Display total revenue generated by this car"""
        try:
            from django.db.models import Sum
            from bookings.models import Booking

            revenue = Booking.objects.filter(car=obj, car_returned=True).aggregate(
                total=Sum('total_amount')
            )['total'] or 0

            return format_html('<strong style="color: #28a745;">₹{:,.0f}</strong>', revenue)
        except Exception:
            return format_html('<span style="color: #6c757d;">₹0</span>')
    total_revenue.short_description = "Total Revenue"

    def booking_stats(self, obj):
        """Display comprehensive booking statistics"""
        try:
            from bookings.models import Booking

            total_bookings = Booking.objects.filter(car=obj).count()
            active_bookings = Booking.objects.filter(
                car=obj, car_returned=False).count()
            completed_bookings = Booking.objects.filter(
                car=obj, car_returned=True).count()

            return format_html(
                '<div style="line-height: 1.6; padding: 10px; background: #f8f9fa; border-radius: 5px;">'
                '<strong>📊 Booking Statistics</strong><br>'
                '<span style="color: #007bff;">📋 Total Bookings: {}</span><br>'
                '<span style="color: #dc3545;">🔄 Active: {}</span><br>'
                '<span style="color: #28a745;">✅ Completed: {}</span><br>'
                '<strong>📈 Utilization Rate: {:.1f}%</strong>'
                '</div>',
                total_bookings,
                active_bookings,
                completed_bookings,
                (completed_bookings / total_bookings *
                 100) if total_bookings > 0 else 0
            )
        except Exception:
            return format_html('<span style="color: #6c757d;">No booking data available</span>')
    booking_stats.short_description = "Booking Statistics"

    def revenue_stats(self, obj):
        """Display detailed revenue analytics"""
        try:
            from django.db.models import Sum, Avg, Count
            from bookings.models import Booking

            revenue_data = Booking.objects.filter(car=obj, car_returned=True).aggregate(
                total_revenue=Sum('total_amount'),
                avg_booking_value=Avg('total_amount'),
                total_bookings=Count('id')
            )

            total_rev = revenue_data['total_revenue'] or 0
            avg_booking = revenue_data['avg_booking_value'] or 0
            bookings = revenue_data['total_bookings'] or 0

            return format_html(
                '<div style="line-height: 1.6; padding: 10px; background: #f8f9fa; border-radius: 5px;">'
                '<strong>💰 Revenue Analytics</strong><br>'
                '<span style="color: #28a745;">💵 Total Revenue: ₹{:,.0f}</span><br>'
                '<span style="color: #007bff;">📊 Average Booking: ₹{:,.0f}</span><br>'
                '<span style="color: #6f42c1;">📈 Daily Rate Efficiency: {:.1f}%</span><br>'
                '<small style="color: #6c757d;">Based on {} completed bookings</small>'
                '</div>',
                total_rev,
                avg_booking,
                (avg_booking / obj.fee * 100) if obj.fee > 0 else 0,
                bookings
            )
        except Exception:
            return format_html('<span style="color: #6c757d;">No revenue data available</span>')
    revenue_stats.short_description = "Revenue Analytics"

    # Custom Actions
    def mark_available(self, request, queryset):
        """Mark selected cars as available"""
        updated = queryset.update(availability='Available', status='Active')
        self.message_user(
            request, f'✅ {updated} cars marked as available.', messages.SUCCESS)
    mark_available.short_description = "✅ Mark as available"

    def mark_booked(self, request, queryset):
        """Mark selected cars as booked"""
        updated = queryset.update(availability='Booked', status='Booked')
        self.message_user(
            request, f'📅 {updated} cars marked as booked.', messages.SUCCESS)
    mark_booked.short_description = "📅 Mark as booked"

    def mark_maintenance(self, request, queryset):
        """Mark selected cars for maintenance"""
        updated = queryset.update(availability='Reserved', status='Active')
        self.message_user(
            request, f'🔧 {updated} cars marked for maintenance.', messages.WARNING)
    mark_maintenance.short_description = "🔧 Mark for maintenance"

    def soft_delete_cars(self, request, queryset):
        """Soft delete selected cars"""
        count = 0
        for car in queryset:
            if not car.is_deleted:
                car.soft_delete(user=request.user, reason='Admin bulk action')
                count += 1

        self.message_user(
            request, f'🗑️ {count} cars were soft deleted.', messages.WARNING)
    soft_delete_cars.short_description = "🗑️ Soft delete selected cars"

    def bulk_update_insurance(self, request, queryset):
        """Placeholder for bulk insurance update"""
        count = queryset.count()
        self.message_user(
            request, f'📋 Insurance update functionality ready for {count} cars.', messages.INFO)
    bulk_update_insurance.short_description = "📋 Update insurance info"

    def generate_revenue_report(self, request, queryset):
        """Placeholder for revenue report generation"""
        count = queryset.count()
        self.message_user(
            request, f'📊 Revenue report functionality ready for {count} cars.', messages.INFO)
    generate_revenue_report.short_description = "📊 Generate revenue report"

    def check_expiry_dates(self, request, queryset):
        """Check and report on expiry dates"""
        from datetime import date, timedelta

        today = date.today()
        warning_date = today + timedelta(days=30)

        insurance_expiring = queryset.filter(
            insurance_expiry_date__lte=warning_date, insurance_expiry_date__gte=today).count()
        tracker_expiring = queryset.filter(
            tracker_expiry_date__lte=warning_date, tracker_expiry_date__gte=today).count()
        insurance_expired = queryset.filter(
            insurance_expiry_date__lt=today).count()
        tracker_expired = queryset.filter(
            tracker_expiry_date__lt=today).count()

        message = f'📅 Expiry Check: {insurance_expiring} insurance expiring, {tracker_expiring} tracker expiring, {insurance_expired} insurance expired, {tracker_expired} tracker expired'

        if insurance_expired > 0 or tracker_expired > 0:
            self.message_user(request, message, messages.ERROR)
        elif insurance_expiring > 0 or tracker_expiring > 0:
            self.message_user(request, message, messages.WARNING)
        else:
            self.message_user(
                request, '✅ All selected cars have valid insurance and tracker dates.', messages.SUCCESS)
    check_expiry_dates.short_description = "📅 Check expiry dates"

    def save_model(self, request, obj, form, change):
        """Override to set audit fields"""
        if not change:  # Creating new car
            obj.created_by = request.user
        else:  # Updating existing car
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """Override to use soft delete instead of hard delete"""
        obj.soft_delete(user=request.user, reason='Admin deletion')
        self.message_user(
            request, f'Car "{obj.car_name}" has been soft deleted.', messages.WARNING)


@admin.register(CarDeleteReason)
class CarDeleteReasonAdmin(admin.ModelAdmin):
    list_display = ('car_link', 'reason', 'deleted_at',
                    'deleted_by_name', 'description_preview')
    list_filter = ('reason', 'deleted_at')
    search_fields = ('car__car_name', 'description', 'reason')
    readonly_fields = ('deleted_at', 'deleted_by')
    date_hierarchy = 'deleted_at'
    ordering = ['-deleted_at']

    fieldsets = (
        ('Deletion Information', {
            'fields': ('car', 'reason', 'description')
        }),
        ('Audit Information', {
            'fields': ('deleted_at', 'deleted_by'),
            'classes': ('collapse',)
        }),
    )

    def car_link(self, obj):
        """Link to the deleted car"""
        url = reverse('admin:cars_car_change', args=[obj.car.id])
        return format_html('<a href="{}" style="color: #007cba;">{}</a>', url, obj.car.car_name)
    car_link.short_description = "Car"
    car_link.admin_order_field = 'car__car_name'

    def deleted_by_name(self, obj):
        """Display who deleted the car"""
        if obj.deleted_by:
            return format_html('<strong>{}</strong>', obj.deleted_by.full_name or obj.deleted_by.email)
        return format_html('<em style="color: #6c757d;">System</em>')
    deleted_by_name.short_description = "Deleted By"
    deleted_by_name.admin_order_field = 'deleted_by__full_name'

    def description_preview(self, obj):
        """Show preview of description"""
        if obj.description:
            preview = obj.description[:50] + \
                '...' if len(obj.description) > 50 else obj.description
            return format_html('<span title="{}">{}</span>', obj.description, preview)
        return format_html('<em style="color: #6c757d;">No description</em>')
    description_preview.short_description = "Description"
