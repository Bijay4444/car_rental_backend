from rest_framework import serializers
from .models import MenuItem

class MenuItemSerializer(serializers.ModelSerializer):
    """
    Serializer for menu items.

    Includes nested children for hierarchical menus.
    """
    children = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'icon', 'route', 'order', 'children']

    def get_children(self, obj):
        """
        Get active child menu items.

        Args:
            obj (MenuItem): The parent menu item.

        Returns:
            list: Serialized child menu items.
        """
        children = obj.children.filter(is_active=True)
        return MenuItemSerializer(children, many=True).data
