from django.db import models
from django.contrib.auth.models import Group

class MenuItem(models.Model):
    """
    Model representing a menu item for the application's navigation.

    Supports hierarchical menus, group-based access control, and ordering.

    Attributes:
        title (str): Display name of the menu item.
        icon (str): Icon name for the menu item.
        route (str): Frontend route or identifier.
        order (int): Display order.
        parent (MenuItem): Parent menu item for nested menus.
        groups (ManyToMany[Group]): User groups allowed to see this menu.
        is_active (bool): Whether the menu item is active.
    """
    title = models.CharField(max_length=100)
    icon = models.CharField(max_length=50)  # e.g., "credit-card", "calendar", "chart-bar"
    route = models.CharField(max_length=200, blank=True, null=True)  # e.g., "PaymentTracker"
    order = models.PositiveIntegerField(default=0)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    groups = models.ManyToManyField(Group, blank=True, help_text="Restrict menu to certain user groups")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        """
        Return the string representation of the menu item.

        Returns:
            str: Menu item title.
        """
        return self.title
