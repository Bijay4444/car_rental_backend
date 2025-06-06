from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.db import models
from .models import MenuItem
from .serializers import MenuItemSerializer

class MenuItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing and retrieving menu items.

    Provides CRUD operations and filters menu items based on user group and active status.
    Returns hierarchical menu structure for navigation.
    """
    serializer_class = MenuItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return the queryset of top-level active menu items, filtered by user group.

        Returns:
            QuerySet: Filtered menu items.
        """
        user = self.request.user
        qs = MenuItem.objects.filter(parent__isnull=True, is_active=True)
        if user.is_superuser:
            return qs
        return qs.filter(models.Q(groups__in=user.groups.all()) | models.Q(groups__isnull=True)).distinct()

    def list(self, request, *args, **kwargs):
        """
        List all accessible menu items for the current user.

        Returns:
            Response: API response with menu items.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "data": serializer.data,
            "message": "Menu items fetched successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve details of a specific menu item.

        Returns:
            Response: API response with menu item details.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "data": serializer.data,
            "message": "Menu item retrieved successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """
        Create a new menu item.

        Returns:
            Response: API response with created menu item.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            "data": serializer.data,
            "message": "Menu item created successfully",
            "status_code": status.HTTP_201_CREATED
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Update an existing menu item.

        Returns:
            Response: API response with updated menu item.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "data": serializer.data,
            "message": "Menu item updated successfully",
            "status_code": status.HTTP_200_OK
        }, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update a menu item.

        Returns:
            Response: API response with updated menu item.
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Delete a menu item.

        Returns:
            Response: API response with deletion status.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "data": None,
            "message": "Menu item deleted successfully",
            "status_code": status.HTTP_204_NO_CONTENT
        }, status=status.HTTP_204_NO_CONTENT)
