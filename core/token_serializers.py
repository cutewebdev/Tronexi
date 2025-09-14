from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'  # We will use email as login field

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # Check if email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.fail('no_active_account')

        # Check if password matches
        if not check_password(password, user.password):
            self.fail('no_active_account')

        if not user.is_active:
            self.fail('no_active_account')

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }