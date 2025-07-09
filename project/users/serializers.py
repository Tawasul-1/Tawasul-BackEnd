from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password

class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        user = authenticate(email=email, password=password)

        if user is None:
            raise AuthenticationFailed("Invalid email or password.")
        if not user.verified:
            raise AuthenticationFailed("Account is not activated. Please check your email.")

        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        return super().get_token(user)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    phone = serializers.CharField(required=True, validators=[RegexValidator(regex=r'^01[0125][0-9]{8}$', message="Phone number must be a valid Egyptian mobile number.")])

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "password", "password2", 
                  "address", "birth_date", "phone",
                  "profile_picture"]
        read_only_fields = ["account_type", "verified", "created_at"]
    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError("Passwords do not match")
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    is_premium = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "profile_picture", "bio", "address", "birth_date", "phone", "account_type", "is_premium"]
        read_only_fields = ["id", "username", "email", "account_type", "is_premium"]

    def get_is_premium(self, obj):
        return obj.is_premium

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "profile_picture", "bio", "address", "birth_date", "phone"]
        read_only_fields = ["email"]

    def validate_phone(self, value):
        if value:
            RegexValidator(regex=r'^01[0125][0-9]{8}$')(value)
        return value