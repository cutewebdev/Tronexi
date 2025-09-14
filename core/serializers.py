from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

from .models import KYC


# ✅ User Serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


# ✅ KYC Serializer
class KYCSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYC
        fields = ['id', 'user', 'document_type', 'document_number']