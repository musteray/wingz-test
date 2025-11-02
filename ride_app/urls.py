from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from .views import UserViewSet, RideViewSet, RideEventViewSet
from .auth_views import (
    register_user, logout_user
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'rides', RideViewSet, basename='ride')
router.register(r'ride-events', RideEventViewSet, basename='ride-event')

urlpatterns = [
    # Router URLs (CRUD operations - admin only)
    path('', include(router.urls)),

    # Token authentication endpoint
    path('authenticate/', obtain_auth_token, name='api_token_auth'),
    path('logout/', logout_user, name='logout'),
    path('register/', register_user, name='register'),  # Public registration
]