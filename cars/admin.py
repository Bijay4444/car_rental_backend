from django.contrib import admin
from .models import Car, CarDeleteReason

class CarDeleteReasonInline(admin.TabularInline):
    model = CarDeleteReason
    extra = 0
    readonly_fields = ['deleted_at', 'deleted_by']

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('car_name', 'type', 'fee', 'status', 'availability', 'created_at')
    list_filter = ('type', 'status', 'availability', 'gearbox', 'is_deleted')
    search_fields = ('car_name', 'color')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_at', 'deleted_by')
    fieldsets = (
        ('Basic Information', {
            'fields': ('car_name', 'car_image', 'fee', 'tracker_expiry_date')
        }),
        ('Specifications', {
            'fields': ('color', 'seats', 'mileage', 'type', 'gearbox', 'max_speed')
        }),
        ('Insurance', {
            'fields': ('collision_damage_waiver', 'third_party_liability_insurance', 
                      'optional_insurance_add_ons', 'insurance_expiry_date')
        }),
        ('Status', {
            'fields': ('status', 'availability')
        }),
        ('Audit', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by', 
                      'is_deleted', 'deleted_at', 'deleted_by'),
            'classes': ('collapse',)
        }),
    )
    inlines = [CarDeleteReasonInline]

@admin.register(CarDeleteReason)
class CarDeleteReasonAdmin(admin.ModelAdmin):
    list_display = ('car', 'reason', 'deleted_at', 'deleted_by')
    list_filter = ('reason', 'deleted_at')
    search_fields = ('car__car_name', 'description')
    readonly_fields = ('deleted_at',)
