# views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Prefetch, Q, F, ExpressionWrapper, FloatField
from django.db.models.functions import ACos, Sin, Cos, Radians, Power, Sqrt
from django.utils import timezone
from datetime import timedelta
from .models import User, Ride, RideEvent
from .serializers import (
    UserSerializer, RideListSerializer, RideDetailSerializer,
    RideCreateUpdateSerializer, RideEventSerializer,
    RideEventCreateUpdateSerializer
)
from .permissions import IsAdminUser
from .filters import RideFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
import math


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Users"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filterset_fields = ['role', 'email']
    search_fields = ['email', 'first_name', 'last_name']


class RideViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Rides with optimized queries.
    Supports filtering, pagination, and distance-based sorting.
    
    Query Parameters:
    - status: Filter by ride status (e.g., 'en-route', 'pickup', 'dropoff')
    - rider_email: Filter by rider's email address
    - latitude: GPS latitude for distance calculation
    - longitude: GPS longitude for distance calculation
    - ordering: Sort by 'pickup_time', '-pickup_time', 'distance_to_pickup', or '-distance_to_pickup'
    - page: Page number for pagination
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = RideFilter
    ordering_fields = ['pickup_time', 'distance_to_pickup']
    ordering = ['-pickup_time']
    
    def get_queryset(self):
        """
        Optimized queryset with select_related and prefetch_related.
        Achieves 2-3 queries total for the list endpoint:
        1. Main query with JOINs for rider and driver
        2. Prefetch query for today's events only
        3. Count query for pagination (if paginating)
        """
        # Calculate 24 hours ago for filtering recent events
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        
        # Prefetch only today's events to minimize data transfer
        todays_events_prefetch = Prefetch(
            'events',
            queryset=RideEvent.objects.filter(
                created_at__gte=twenty_four_hours_ago
            ).order_by('-created_at'),
            to_attr='todays_events_prefetch'
        )
        
        # Query 1: Main query with select_related for rider and driver
        # Query 2: Prefetch today's events
        queryset = Ride.objects.select_related(
            'id_rider',   # Join with rider user
            'id_driver'   # Join with driver user
        ).prefetch_related(
            todays_events_prefetch  # Prefetch today's events only
        )
        
        # Add distance calculation if GPS coordinates are provided
        lat = self.request.query_params.get('latitude')
        lon = self.request.query_params.get('longitude')
        
        if lat and lon:
            try:
                lat = float(lat)
                lon = float(lon)
                queryset = self.annotate_distance(queryset, lat, lon)
            except (ValueError, TypeError):
                pass
        
        return queryset
    
    def annotate_distance(self, queryset, user_lat, user_lon):
        """
        Annotates queryset with distance_to_pickup using Haversine formula.
        This is calculated in the database for efficient sorting on large tables.
        
        The Haversine formula calculates great-circle distance:
        a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
        c = 2 ⋅ atan2(√a, √(1−a))
        d = R ⋅ c
        
        Where:
        - φ is latitude, λ is longitude
        - R is earth's radius (6371 km)
        
        Performance optimizations:
        1. Calculation is done at database level (pushed down to SQL)
        2. Works with existing indexes on pickup_latitude and pickup_longitude
        3. Supports efficient sorting even on very large tables
        4. Can be further optimized with PostGIS spatial indexes
        
        Alternative implementation using simpler Euclidean approximation
        for better database compatibility:
        """
        # Earth's radius in kilometers
        earth_radius = 6371.0
        
        # For databases that support trigonometric functions (PostgreSQL, MySQL 5.7+)
        try:
            # Convert user coordinates to radians
            user_lat_rad = math.radians(user_lat)
            user_lon_rad = math.radians(user_lon)
            
            # Haversine formula in database
            distance_expression = ExpressionWrapper(
                earth_radius * ACos(
                    Cos(Radians(F('pickup_latitude'))) *
                    Cos(user_lat_rad) *
                    Cos(Radians(F('pickup_longitude')) - user_lon_rad) +
                    Sin(Radians(F('pickup_latitude'))) *
                    Sin(user_lat_rad)
                ),
                output_field=FloatField()
            )
            
            return queryset.annotate(distance_to_pickup=distance_expression)
        except:
            # Fallback: Simplified Euclidean approximation for better compatibility
            # This is less accurate but works on all databases
            lat_diff = F('pickup_latitude') - user_lat
            lon_diff = F('pickup_longitude') - user_lon
            
            # Approximate distance using Pythagorean theorem
            # (multiply by 111 to convert degrees to km at equator)
            distance_expression = ExpressionWrapper(
                Sqrt(Power(lat_diff, 2) + Power(lon_diff, 2)) * 111.0,
                output_field=FloatField()
            )
            
            return queryset.annotate(distance_to_pickup=distance_expression)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return RideListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RideCreateUpdateSerializer
        return RideDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """
        List rides with optimized queries.
        
        Example requests:
        - GET /api/rides/
        - GET /api/rides/?status=en-route
        - GET /api/rides/?rider_email=john@example.com
        - GET /api/rides/?latitude=14.5995&longitude=120.9842&ordering=distance_to_pickup
        - GET /api/rides/?status=pickup&ordering=-pickup_time&page=2
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RideEventViewSet(viewsets.ModelViewSet):
    """ViewSet for managing RideEvents"""
    queryset = RideEvent.objects.select_related('id_ride')
    serializer_class = RideEventSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filterset_fields = ['id_ride']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Optimize queryset with select_related"""
        return RideEvent.objects.select_related('id_ride')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action in ['create', 'update', 'partial_update']:
            return RideEventCreateUpdateSerializer
        return RideEventSerializer