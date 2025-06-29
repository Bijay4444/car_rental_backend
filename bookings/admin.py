from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db import models
from django.utils import timezone
from django.contrib import messages
from .models import Booking, Payment, BookingExtension


class PaymentInline(admin.TabularInline):
    """Inline admin for booking payments"""
    model = Payment
    extra = 0
    readonly_fields = ['created_at', 'created_by']
    fields = ['amount', 'payment_method', 'payment_date',
              'transaction_id', 'is_successful', 'notes', 'created_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class BookingExtensionInline(admin.TabularInline):
    """Inline admin for booking extensions"""
    model = BookingExtension
    extra = 0
    readonly_fields = ['created_at', 'created_by']
    fields = ['previous_end_date', 'new_end_date',
              'extension_fee', 'reason', 'remarks', 'created_at']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id_link', 'customer_link', 'car_link', 'date_range', 'booking_status',
                    'payment_status', 'car_returned', 'total_amount_formatted', 'balance_due_formatted', 'days_count', 'created_at')
    list_filter = ('booking_status', 'payment_status', 'car_returned', 'has_been_swapped', 'has_accident', 'created_at',
                   'start_date', 'end_date', 'payment_method')
    search_fields = ('booking_id', 'customer__name',
                     'car__car_name', 'customer__email')
    readonly_fields = ('booking_id', 'created_at', 'updated_at', 'created_by', 'booking_summary',
                       'financial_summary', 'accident_summary', 'swap_summary', 'calculated_paid_amount', 'balance_due')
    list_editable = ('booking_status', 'payment_status', 'car_returned')
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_id', 'customer', 'car', 'original_car', 'has_been_swapped')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'pickup_time', 'dropoff_time', 'actual_return_date'),
            'classes': ('wide',)
        }),
        ('Status & Return', {
            'fields': ('booking_status', 'car_returned', 'payment_status'),
            'classes': ('wide',)
        }),
        ('Financial Details', {
            'fields': ('financial_summary', 'subtotal', 'tax', 'discount', 'extension_charges',
                       'total_amount', 'paid_amount', 'calculated_paid_amount', 'balance_due',
                       'payment_date', 'payment_method'),
            'classes': ('wide',)
        }),
        ('Accident Information', {
            'fields': ('accident_summary', 'has_accident', 'accident_description', 'accident_date', 'accident_charges'),
            'classes': ('collapse',)
        }),
        ('Car Swap Information', {
            'fields': ('swap_summary', 'swap_date', 'swap_reason'),
            'classes': ('collapse',)
        }),
        ('Booking Summary', {
            'fields': ('booking_summary',),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('remarks', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    inlines = [PaymentInline, BookingExtensionInline]
    actions = ['mark_returned', 'mark_cancelled', 'mark_active', 'send_reminder', 'bulk_payment_update',
               'check_overdue_bookings', 'generate_booking_report']

    def get_queryset(self, request):
        """Optimize queries with select_related and prefetch_related"""
        return super().get_queryset(request).select_related(
            'customer', 'car', 'original_car', 'created_by'
        ).prefetch_related('payments', 'extensions')

    def booking_id_link(self, obj):
        """Display booking ID as a styled link"""
        return format_html(
            '<div>'
            '<strong style="color: #007cba;">{}</strong><br>'
            '<small style="color: #666;">Created: {}</small>'
            '</div>',
            obj.booking_id,
            obj.created_at.strftime('%d %b %Y')
        )
    booking_id_link.short_description = "Booking ID"
    booking_id_link.admin_order_field = 'booking_id'

    def customer_link(self, obj):
        """Display customer with link to customer admin"""
        if obj.customer:
            url = reverse('admin:customers_customer_change',
                          args=[obj.customer.id])
            return format_html(
                '<div>'
                '<a href="{}" style="color: #007cba; font-weight: bold;">{}</a><br>'
                '<small style="color: #666;">{}</small>'
                '</div>',
                url, obj.customer.name, obj.customer.email
            )
        return format_html('<span style="color: #dc3545;">❌ No Customer</span>')
    customer_link.short_description = "Customer"
    customer_link.admin_order_field = 'customer__name'

    def car_link(self, obj):
        """Display car with link to car admin - FIXED None check"""
        if obj.car:
            url = reverse('admin:cars_car_change', args=[obj.car.id])
            swap_indicator = " 🔄" if obj.has_been_swapped else ""
            return format_html(
                '<div>'
                '<a href="{}" style="color: #007cba; font-weight: bold;">{}{}</a><br>'
                '<small style="color: #666;">₹{}/day</small>'
                '</div>',
                url, obj.car.car_name, swap_indicator, int(obj.car.fee)
            )
        return format_html('<span style="color: #dc3545;">❌ No Car Assigned</span>')
    car_link.short_description = "Car"
    car_link.admin_order_field = 'car__car_name'

    def date_range(self, obj):
        """Display booking date range with duration"""
        today = timezone.now().date()
        duration = obj.get_duration_days()

        # Determine status colors
        start_color = '#28a745' if obj.start_date <= today else '#007bff'
        end_color = '#dc3545' if obj.end_date < today and not obj.car_returned else '#28a745'

        return format_html(
            '<div style="text-align: center;">'
            '<span style="color: {}; font-weight: bold;">{}</span><br>'
            '<small style="color: #666;">to</small><br>'
            '<span style="color: {}; font-weight: bold;">{}</span><br>'
            '<small style="color: #666;">({} days)</small>'
            '</div>',
            start_color, obj.start_date.strftime('%d %b'),
            end_color, obj.end_date.strftime('%d %b'),
            duration
        )
    date_range.short_description = "Date Range"
    date_range.admin_order_field = 'start_date'

    def total_amount_formatted(self, obj):
        """Display total amount with breakdown"""
        extra_charges = float(obj.extension_charges or 0) + \
            float(obj.accident_charges or 0)
        return format_html(
            '<div style="text-align: right;">'
            '<strong style="font-size: 14px;">₹{}</strong><br>'
            '<small style="color: #666;">+ ₹{} charges</small>'
            '</div>',
            f"{float(obj.total_amount):,.2f}",
            f"{extra_charges:,.0f}"
        )
    total_amount_formatted.short_description = "Total Amount"
    total_amount_formatted.admin_order_field = 'total_amount'

    def balance_due_formatted(self, obj):
        """Display remaining balance with overdue fees"""
        try:
            balance = obj.get_total_balance()
        except:
            balance = float(obj.total_amount or 0) - \
                float(obj.paid_amount or 0)

        color = '#dc3545' if balance > 0 else '#28a745'

        return format_html(
            '<div style="text-align: right; color: {};">'
            '<strong style="font-size: 14px;">₹{}</strong><br>'
            '<small>{}</small>'
            '</div>',
            color, f"{balance:,.2f}",
            'Due' if balance > 0 else 'Paid'
        )
    balance_due_formatted.short_description = "Balance"

    def days_count(self, obj):
        """Display duration with overdue indicator"""
        duration = obj.get_duration_days()
        today = timezone.now().date()

        if obj.end_date < today and not obj.car_returned:
            overdue_days = (today - obj.end_date).days
            return format_html(
                '<div style="text-align: center;">'
                '<strong>{}</strong> days<br>'
                '<small style="color: #dc3545;">⚠️ {} days overdue</small>'
                '</div>',
                duration, overdue_days
            )

        return format_html(
            '<div style="text-align: center;">'
            '<strong>{}</strong> days'
            '</div>',
            duration
        )
    days_count.short_description = "Duration"

    def booking_summary(self, obj):
        """Comprehensive booking summary - FIXED None checks"""
        duration = obj.get_duration_days()
        daily_rate = float(obj.car.fee) if obj.car else 0

        return format_html(
            '<div style="line-height: 1.6; padding: 15px; background: #f8f9fa; border-radius: 8px;">'
            '<h4 style="margin-top: 0; color: #495057;">📋 Booking Overview</h4>'
            '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">'
            '<div><strong>Duration:</strong> {} days</div>'
            '<div><strong>Daily Rate:</strong> ₹{}</div>'
            '<div><strong>Car Returned:</strong> {}</div>'
            '<div><strong>Has Accident:</strong> {}</div>'
            '<div><strong>Car Swapped:</strong> {}</div>'
            '<div><strong>Pickup Time:</strong> {}</div>'
            '<div><strong>Dropoff Time:</strong> {}</div>'
            '<div><strong>Actual Return:</strong> {}</div>'
            '</div></div>',
            duration, f"{daily_rate:,.2f}",
            "✅ Yes" if obj.car_returned else "❌ No",
            "⚠️ Yes" if obj.has_accident else "✅ No",
            "🔄 Yes" if obj.has_been_swapped else "❌ No",
            obj.pickup_time or "Not set",
            obj.dropoff_time or "Not set",
            obj.actual_return_date or "Not returned"
        )
    booking_summary.short_description = "Booking Overview"

    def financial_summary(self, obj):
        """Detailed financial breakdown"""
        try:
            balance = obj.get_total_balance()
            total_paid_calculated = obj.get_total_paid()
        except:
            balance = float(obj.total_amount or 0) - \
                float(obj.paid_amount or 0)
            total_paid_calculated = float(obj.paid_amount or 0)

        return format_html(
            '<div style="line-height: 1.6; padding: 15px; background: #f8f9fa; border-radius: 8px;">'
            '<h4 style="margin-top: 0; color: #495057;">💰 Financial Breakdown</h4>'
            '<table style="width: 100%; border-collapse: collapse;">'
            '<tr><td><strong>Subtotal:</strong></td><td style="text-align: right;">₹{}</td></tr>'
            '<tr><td><strong>Tax:</strong></td><td style="text-align: right;">₹{}</td></tr>'
            '<tr><td><strong>Discount:</strong></td><td style="text-align: right; color: green;">-₹{}</td></tr>'
            '<tr><td><strong>Extension Charges:</strong></td><td style="text-align: right;">₹{}</td></tr>'
            '<tr><td><strong>Accident Charges:</strong></td><td style="text-align: right;">₹{}</td></tr>'
            '<tr style="border-top: 2px solid #dee2e6;"><td><strong>Total Amount:</strong></td><td style="text-align: right;"><strong>₹{}</strong></td></tr>'
            '<tr><td><strong>Paid Amount (DB):</strong></td><td style="text-align: right; color: green;">₹{}</td></tr>'
            '<tr><td><strong>Calculated Paid:</strong></td><td style="text-align: right; color: blue;">₹{}</td></tr>'
            '<tr style="border-top: 1px solid #dee2e6;"><td><strong>Balance Due:</strong></td><td style="text-align: right; color: {};">₹{}</td></tr>'
            '</table></div>',
            f"{float(obj.subtotal or 0):,.2f}",
            f"{float(obj.tax or 0):,.2f}",
            f"{float(obj.discount or 0):,.2f}",
            f"{float(obj.extension_charges or 0):,.2f}",
            f"{float(obj.accident_charges or 0):,.2f}",
            f"{float(obj.total_amount or 0):,.2f}",
            f"{float(obj.paid_amount or 0):,.2f}",
            f"{total_paid_calculated:,.2f}",
            'red' if balance > 0 else 'green',
            f"{balance:,.2f}"
        )
    financial_summary.short_description = "Financial Summary"

    def accident_summary(self, obj):
        """Accident information summary"""
        if not obj.has_accident:
            return format_html('<span style="color: #28a745;">✅ No accidents reported</span>')

        return format_html(
            '<div style="line-height: 1.6; padding: 15px; background: #fff3cd; border-radius: 8px; border-left: 4px solid #ffc107;">'
            '<h4 style="margin-top: 0; color: #856404;">⚠️ Accident Report</h4>'
            '<p><strong>Date:</strong> {}</p>'
            '<p><strong>Charges:</strong> ₹{}</p>'
            '<p><strong>Description:</strong></p>'
            '<p style="background: white; padding: 10px; border-radius: 4px;">{}</p>'
            '</div>',
            obj.accident_date or "Not specified",
            f"{float(obj.accident_charges or 0):,.2f}",
            obj.accident_description or "No description provided"
        )
    accident_summary.short_description = "Accident Information"

    def swap_summary(self, obj):
        """Car swap information summary - FIXED None checks"""
        if not obj.has_been_swapped:
            return format_html('<span style="color: #28a745;">✅ No car swaps</span>')

        return format_html(
            '<div style="line-height: 1.6; padding: 15px; background: #d1ecf1; border-radius: 8px; border-left: 4px solid #17a2b8;">'
            '<h4 style="margin-top: 0; color: #0c5460;">🔄 Car Swap Details</h4>'
            '<p><strong>Original Car:</strong> {}</p>'
            '<p><strong>Current Car:</strong> {}</p>'
            '<p><strong>Swap Date:</strong> {}</p>'
            '<p><strong>Reason:</strong> {}</p>'
            '</div>',
            obj.original_car.car_name if obj.original_car else "Not recorded",
            obj.car.car_name if obj.car else "Not assigned",
            obj.swap_date or "Not specified",
            obj.swap_reason or "No reason provided"
        )
    swap_summary.short_description = "Car Swap Information"

    # Custom Actions
    def mark_returned(self, request, queryset):
        """Mark selected bookings as returned"""
        updated = 0
        for booking in queryset:
            if not booking.car_returned:
                booking.car_returned = True
                booking.booking_status = 'Returned'
                booking.actual_return_date = timezone.now().date()

                # Update car availability - FIXED None check
                if booking.car:
                    booking.car.availability = 'Available'
                    booking.car.status = 'Active'
                    booking.car.save()

                booking.save()
                updated += 1

        self.message_user(
            request, f'✅ {updated} bookings marked as returned.', messages.SUCCESS)
    mark_returned.short_description = "✅ Mark selected bookings as returned"

    def mark_cancelled(self, request, queryset):
        """Cancel selected bookings"""
        updated = 0
        for booking in queryset:
            if booking.booking_status not in ['Returned', 'Cancelled']:
                booking.booking_status = 'Cancelled'

                # Update car availability - FIXED None check
                if booking.car:
                    booking.car.availability = 'Available'
                    booking.car.status = 'Active'
                    booking.car.save()

                booking.save()
                updated += 1

        self.message_user(
            request, f'❌ {updated} bookings cancelled.', messages.WARNING)
    mark_cancelled.short_description = "❌ Cancel selected bookings"

    def mark_active(self, request, queryset):
        """Mark selected bookings as active"""
        updated = 0
        for booking in queryset:
            if booking.booking_status != 'Active':
                booking.booking_status = 'Active'
                booking.car_returned = False

                # Update car availability - FIXED None check
                if booking.car:
                    booking.car.availability = 'Booked'
                    booking.car.status = 'Booked'
                    booking.car.save()

                booking.save()
                updated += 1

        self.message_user(
            request, f'🔄 {updated} bookings marked as active.', messages.INFO)
    mark_active.short_description = "🔄 Mark as active"

    def send_reminder(self, request, queryset):
        """Send reminder to customers"""
        count = queryset.count()
        self.message_user(
            request, f'📧 Reminder functionality ready for {count} bookings.', messages.INFO)
    send_reminder.short_description = "📧 Send reminder to customers"

    def bulk_payment_update(self, request, queryset):
        """Bulk update payment status"""
        count = queryset.count()
        self.message_user(
            request, f'💳 Payment update functionality ready for {count} bookings.', messages.INFO)
    bulk_payment_update.short_description = "💳 Bulk payment update"

    def check_overdue_bookings(self, request, queryset):
        """Check for overdue bookings"""
        today = timezone.now().date()
        overdue_count = queryset.filter(
            end_date__lt=today,
            car_returned=False,
            booking_status__in=['Active', 'Overdue']
        ).count()

        if overdue_count > 0:
            self.message_user(
                request, f'⚠️ Found {overdue_count} overdue bookings in selection.', messages.WARNING)
        else:
            self.message_user(
                request, '✅ No overdue bookings found in selection.', messages.SUCCESS)
    check_overdue_bookings.short_description = "⚠️ Check overdue bookings"

    def generate_booking_report(self, request, queryset):
        """Generate booking report"""
        count = queryset.count()
        self.message_user(
            request, f'📊 Report generation ready for {count} bookings.', messages.INFO)
    generate_booking_report.short_description = "📊 Generate booking report"

    def save_model(self, request, obj, form, change):
        """Override to set audit fields"""
        if not change:  # Creating new booking
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking_link', 'amount_formatted', 'payment_method', 'payment_date',
                    'success_status', 'transaction_id', 'created_at')
    list_filter = ('payment_method', 'is_successful',
                   'payment_date', 'created_at')
    search_fields = ('booking__booking_id', 'transaction_id',
                     'booking__customer__name')
    readonly_fields = ('created_at', 'created_by')
    date_hierarchy = 'payment_date'
    ordering = ['-payment_date']

    fieldsets = (
        ('Payment Information', {
            'fields': ('booking', 'amount', 'payment_method', 'payment_date', 'is_successful')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'payment_method_details', 'receipt_image')
        }),
        ('Additional Information', {
            'fields': ('notes', 'remarks', 'created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def booking_link(self, obj):
        """Link to the booking"""
        url = reverse('admin:bookings_booking_change', args=[obj.booking.id])
        return format_html(
            '<div>'
            '<a href="{}" style="color: #007cba; font-weight: bold;">{}</a><br>'
            '<small style="color: #666;">{}</small>'
            '</div>',
            url, obj.booking.booking_id, obj.booking.customer.name
        )
    booking_link.short_description = "Booking"
    booking_link.admin_order_field = 'booking__booking_id'

    def amount_formatted(self, obj):
        """Display amount with success status color"""
        color = '#28a745' if obj.is_successful else '#dc3545'
        return format_html(
            '<div style="text-align: right;">'
            '<strong style="color: {}; font-size: 14px;">₹{}</strong>'
            '</div>',
            color, f"{float(obj.amount):,.2f}"
        )
    amount_formatted.short_description = "Amount"
    amount_formatted.admin_order_field = 'amount'

    def success_status(self, obj):
        """Display success status badge"""
        if obj.is_successful:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">✅ SUCCESS</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">❌ FAILED</span>'
            )
    success_status.short_description = "Status"
    success_status.admin_order_field = 'is_successful'

    def save_model(self, request, obj, form, change):
        """Override to set created_by"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(BookingExtension)
class BookingExtensionAdmin(admin.ModelAdmin):
    list_display = ('booking_link', 'date_extension',
                    'extension_fee_formatted', 'reason', 'created_at')
    list_filter = ('created_at', 'extension_fee')
    search_fields = ('booking__booking_id', 'reason',
                     'booking__customer__name')
    readonly_fields = ('created_at', 'created_by')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Extension Information', {
            'fields': ('booking', 'previous_end_date', 'new_end_date', 'extension_fee')
        }),
        ('Additional Details', {
            'fields': ('reason', 'remarks', 'created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

    def booking_link(self, obj):
        """Link to the booking"""
        url = reverse('admin:bookings_booking_change', args=[obj.booking.id])
        return format_html('<a href="{}" style="color: #007cba;">{}</a>', url, obj.booking.booking_id)
    booking_link.short_description = "Booking"

    def date_extension(self, obj):
        """Display date extension details"""
        days_extended = (obj.new_end_date - obj.previous_end_date).days
        return format_html(
            '<div style="text-align: center;">'
            '{} <br>→<br> {}<br>'
            '<small style="color: #666;">(+{} days)</small>'
            '</div>',
            obj.previous_end_date.strftime('%d %b'),
            obj.new_end_date.strftime('%d %b'),
            days_extended
        )
    date_extension.short_description = "Extension"

    def extension_fee_formatted(self, obj):
        """Display formatted extension fee"""
        return format_html('<strong>₹{}</strong>', f"{float(obj.extension_fee):,.2f}")
    extension_fee_formatted.short_description = "Fee"
    extension_fee_formatted.admin_order_field = 'extension_fee'

    def save_model(self, request, obj, form, change):
        """Override to set created_by"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
