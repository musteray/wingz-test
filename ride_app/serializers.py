from rest_framework import serializers
from .models import User, Ride, RideEvent
from django.utils import timezone
from datetime import timedelta


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = ['id_user', 'role', 'first_name', 'last_name', 'email', 'phone_number']
        read_only_fields = ['id_user']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users with password handling"""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['id_user', 'username', 'email', 'password', 'password_confirm', 
                  'role', 'first_name', 'last_name', 'phone_number']
        read_only_fields = ['id_user']
    
    def validate(self, attrs):
        """Validate that passwords match"""
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        """Ensure username is unique"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def validate_role(self, value):
        """Validate role"""
        valid_roles = ['admin', 'driver', 'rider']
        if value not in valid_roles:
            raise serializers.ValidationError(f"Role must be one of: {', '.join(valid_roles)}")
        return value
    
    def create(self, validated_data):
        """Create user with hashed password"""
        # Remove password_confirm as it's not needed for user creation
        validated_data.pop('password_confirm')
        
        # Extract password
        password = validated_data.pop('password')
        
        # Create user instance
        user = User(**validated_data)
        user.set_password(password)  # Hash the password
        user.save()
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information"""
    class Meta:
        model = User
        fields = ['role', 'first_name', 'last_name', 'email', 'phone_number']
    
    def validate_email(self, value):
        """Ensure email is unique (excluding current user)"""
        user = self.instance
        if User.objects.filter(email=value).exclude(id_user=user.id_user).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class RideEventSerializer(serializers.ModelSerializer):
    """Serializer for RideEvent model"""
    class Meta:
        model = RideEvent
        fields = ['id_ride_event', 'id_ride', 'description', 'created_at']
        read_only_fields = ['id_ride_event']


class RideListSerializer(serializers.ModelSerializer):
    """Optimized serializer for listing rides with related data"""
    rider = UserSerializer(source='id_rider', read_only=True)
    driver = UserSerializer(source='id_driver', read_only=True)
    todays_ride_events = serializers.SerializerMethodField()
    distance_to_pickup = serializers.FloatField(read_only=True, required=False)
    
    class Meta:
        model = Ride
        fields = [
            'id_ride', 'status', 'rider', 'driver',
            'pickup_latitude', 'pickup_longitude',
            'dropoff_latitude', 'dropoff_longitude',
            'pickup_time', 'todays_ride_events', 'distance_to_pickup'
        ]
    
    def get_todays_ride_events(self, obj):
        """
        Returns only events from the last 24 hours.
        This method accesses prefetched data to avoid N+1 queries.
        """
        # Access prefetched data using the custom prefetch name
        if hasattr(obj, 'todays_events_prefetch'):
            events = obj.todays_events_prefetch
        else:
            # Fallback (shouldn't happen with proper prefetch)
            twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
            events = obj.events.filter(created_at__gte=twenty_four_hours_ago)
        
        return RideEventSerializer(events, many=True).data


class RideDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual ride retrieval"""
    rider = UserSerializer(source='id_rider', read_only=True)
    driver = UserSerializer(source='id_driver', read_only=True)
    events = RideEventSerializer(many=True, read_only=True)
    
    class Meta:
        model = Ride
        fields = [
            'id_ride', 'status', 'rider', 'driver',
            'pickup_latitude', 'pickup_longitude',
            'dropoff_latitude', 'dropoff_longitude',
            'pickup_time', 'events'
        ]
        read_only_fields = ['id_ride']


class RideCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating rides"""
    id_rider = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    id_driver = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Ride
        fields = [
            'id_ride', 'status', 'id_rider', 'id_driver',
            'pickup_latitude', 'pickup_longitude',
            'dropoff_latitude', 'dropoff_longitude',
            'pickup_time'
        ]
        read_only_fields = ['id_ride']
    
    def validate_id_rider(self, value):
        """Ensure rider has the correct role"""
        if value.role not in ['rider', 'admin']:
            raise serializers.ValidationError("User must have 'rider' or 'admin' role")
        return value
    
    def validate_id_driver(self, value):
        """Ensure driver has the correct role"""
        if value and value.role not in ['driver', 'admin']:
            raise serializers.ValidationError("User must have 'driver' or 'admin' role")
        return value


class RideEventCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating ride events"""
    class Meta:
        model = RideEvent
        fields = ['id_ride_event', 'id_ride', 'description', 'created_at']
        read_only_fields = ['id_ride_event']