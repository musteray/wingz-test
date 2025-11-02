from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import User
from .serializers import UserCreateSerializer, UserSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    Public endpoint for user registration.
    No authentication required.
    
    POST /api/v1/register/
    
    Body:
    {
        "username": "newuser",
        "email": "user@example.com",
        "password": "securepassword123",
        "password_confirm": "securepassword123",
        "role": "rider",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890"
    }
    
    Response:
    {
        "user": {
            "id_user": 1,
            "username": "newuser",
            "email": "user@example.com",
            "role": "rider",
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+1234567890"
        },
        "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
        "message": "User registered successfully"
    }
    """
    serializer = UserCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        # Create user
        user = serializer.save()
        
        # Generate authentication token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout_user(request):
    """
    Logout endpoint - deletes the user's token.
    Requires authentication.
    
    POST /api/v1/logout/
    Headers: Authorization: Token YOUR_TOKEN
    
    Response:
    {
        "message": "Logout successful"
    }
    """
    try:
        # Delete the user's token
        request.user.auth_token.delete()
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Something went wrong'
        }, status=status.HTTP_400_BAD_REQUEST)