from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import MenuItem

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('title_with_icon', 'route_link', 'order', 'parent_item', 'groups_list', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active', 'groups', 'parent')
    search_fields = ('title', 'route', 'icon')
    filter_horizontal = ('groups',)
    ordering = ('parent__title', 'order', 'title')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'icon', 'route', 'parent')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active')
        }),
        ('Access Control', {
            'fields': ('groups',),
            'description': 'Leave empty to allow access to all users. Select groups to restrict access.'
        }),
    )
    
    actions = ['activate_items', 'deactivate_items', 'move_to_top', 'move_to_bottom']
    
    def title_with_icon(self, obj):
        if obj.icon:
            return format_html(
                '<div style="display: flex; align-items: center;">'
                '<i class="{}" style="margin-right: 8px; width: 20px;"></i>'
                '<strong>{}</strong></div>',
                obj.icon, obj.title
            )
        return format_html('<strong>{}</strong>', obj.title)
    title_with_icon.short_description = "Menu Item"
    title_with_icon.admin_order_field = 'title'
    
    def route_link(self, obj):
        if obj.route:
            return format_html('<code style="padding: 2px 4px;">{}</code>', obj.route)
        return format_html('<em style="color: #6c757d;">No route</em>')
    route_link.short_description = "Route"
    
    def parent_item(self, obj):
        if obj.parent:
            return format_html('<span style="color: #007cba;">{}</span>', obj.parent.title)
        return format_html('<em style="color: #6c757d;">Root item</em>')
    parent_item.short_description = "Parent"
    parent_item.admin_order_field = 'parent__title'
    
    def groups_list(self, obj):
        groups = obj.groups.all()
        if groups:
            group_names = [group.name for group in groups]
            return format_html('<span style="color: #28a745;">{}</span>', ', '.join(group_names))
        return format_html('<em style="color: #6c757d;">All users</em>')
    groups_list.short_description = "Access Groups"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent').prefetch_related('groups')
    
    # Actions
    def activate_items(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} menu items activated.')
    activate_items.short_description = "Activate selected menu items"
    
    def deactivate_items(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} menu items deactivated.')
    deactivate_items.short_description = "Deactivate selected menu items"
    
    def move_to_top(self, request, queryset):
        for item in queryset:
            item.order = 0
            item.save()
        self.message_user(request, f'{queryset.count()} menu items moved to top.')
    move_to_top.short_description = "Move selected items to top"
    
    def move_to_bottom(self, request, queryset):
        max_order = MenuItem.objects.aggregate(max_order=models.Max('order'))['max_order'] or 0
        for i, item in enumerate(queryset):
            item.order = max_order + i + 1
            item.save()
        self.message_user(request, f'{queryset.count()} menu items moved to bottom.')
    move_to_bottom.short_description = "Move selected items to bottom"
    
    class Media:
        css = {
            'all': ('admin/css/menu_admin.css',)  # You can add custom CSS
        }
        js = ('admin/js/menu_admin.js',)  # You can add custom JS