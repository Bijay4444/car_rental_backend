from rest_framework import serializers
from .models import MenuItem

class MenuItemSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'icon', 'route', 'order', 'children']

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return MenuItemSerializer(children, many=True).data
