from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'status', 'total_bookings', 'total_spent', 'created_at')
    list_filter = ('status', 'gender', 'created_at')
    search_fields = ('name', 'email', 'phone_number')
    readonly_fields = ('total_bookings', 'total_spent', 'last_booking_date', 'created_at', 'updated_at', 'created_by')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'email', 'phone_number', 'gender', 'date_of_birth', 'address')
        }),
        ('Identification & Status', {
            'fields': ('identification_image', 'status')
        }),
        ('User Account', {
            'fields': ('user',),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('total_bookings', 'total_spent', 'last_booking_date')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
