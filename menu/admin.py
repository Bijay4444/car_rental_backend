from django.contrib import admin
from .models import MenuItem

class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'route', 'order', 'parent', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active', 'groups')
    search_fields = ('title', 'route')
    filter_horizontal = ('groups',)

admin.site.register(MenuItem, MenuItemAdmin)
