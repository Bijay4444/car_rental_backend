from django.contrib import admin
from .models import Booking, Payment, BookingExtension

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['created_at', 'created_by']

class BookingExtensionInline(admin.TabularInline):
    model = BookingExtension
    extra = 0
    readonly_fields = ['created_at', 'created_by']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'customer', 'car', 'start_date', 'end_date', 
                    'booking_status', 'payment_status', 'total_amount', 'created_at')
    list_filter = ('booking_status', 'payment_status', 'car_returned', 'has_been_swapped')
    search_fields = ('booking_id', 'customer__name', 'car__car_name')
    readonly_fields = ('booking_id', 'created_at', 'updated_at', 'created_by')
    inlines = [PaymentInline, BookingExtensionInline]
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_id', 'customer', 'car', 'original_car', 'has_been_swapped')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'pickup_time', 'dropoff_time', 'actual_return_date')
        }),
        ('Status', {
            'fields': ('booking_status', 'car_returned')
        }),
        ('Financial', {
            'fields': ('payment_status', 'subtotal', 'tax', 'discount', 
                      'extension_charges', 'total_amount', 'paid_amount',
                      'payment_date', 'payment_method')
        }),
        ('Accident Information', {
            'fields': ('has_accident', 'accident_description', 
                      'accident_date', 'accident_charges'),
            'classes': ('collapse',)
        }),
        ('Car Swap', {
            'fields': ('swap_date', 'swap_reason'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('remarks', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'payment_date', 'payment_method', 'is_successful')
    list_filter = ('payment_method', 'is_successful', 'payment_date')
    search_fields = ('booking__booking_id', 'transaction_id')
    readonly_fields = ('created_at', 'created_by')

@admin.register(BookingExtension)
class BookingExtensionAdmin(admin.ModelAdmin):
    list_display = ('booking', 'previous_end_date', 'new_end_date', 'extension_fee', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('booking__booking_id', 'reason')
    readonly_fields = ('created_at', 'created_by')
