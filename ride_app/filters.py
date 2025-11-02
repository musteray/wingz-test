import django_filters
from .models import Ride


class RideFilter(django_filters.FilterSet):
    """
    Custom filter for Ride model.
    Supports filtering by status and rider email.
    """
    status = django_filters.CharFilter(
        field_name='status',
        lookup_expr='iexact',
        help_text="Filter by ride status (e.g., 'en-route', 'pickup', 'dropoff')"
    )
    rider_email = django_filters.CharFilter(
        field_name='id_rider__email',
        lookup_expr='iexact',
        help_text="Filter by rider's email (case-insensitive exact match)"
    )
    rider_email_contains = django_filters.CharFilter(
        field_name='id_rider__email',
        lookup_expr='icontains',
        help_text="Filter by partial rider email match"
    )
    
    class Meta:
        model = Ride
        fields = ['status', 'rider_email', 'rider_email_contains']