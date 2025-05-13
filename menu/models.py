from django.db import models
from django.contrib.auth.models import Group

class MenuItem(models.Model):
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
        return self.title
