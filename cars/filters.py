import django_filters
from .models import Car

class CarFilter(django_filters.FilterSet):
    min_fee = django_filters.NumberFilter(field_name="fee", lookup_expr='gte')
    max_fee = django_filters.NumberFilter(field_name="fee", lookup_expr='lte')
    min_seats = django_filters.NumberFilter(field_name="seats", lookup_expr='gte')
    
    class Meta:
        model = Car
        fields = {
            'type': ['exact', 'in'],
            'status': ['exact'],
            'availability': ['exact'],
            'gearbox': ['exact'],
            'color': ['exact', 'icontains'],
            'seats': ['exact'],
            'collision_damage_waiver': ['exact'],
            'third_party_liability_insurance': ['exact'],
        }
