from django.conf import settings 
import jwt
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .models import User
from .utiles import send_activation_email, send_password_reset_email
from .serializers import RegisterSerializer, LoginSerializer, UserProfileSerializer, UserUpdateSerializer
from users.permissions import IsFreeTrialValid

class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    def perform_create(self, serializer):
        user = serializer.save()
        send_activation_email(user, self.request)


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    


@api_view(['POST'])
def logout(request):
    try:
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"detail": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

class UserProfileView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    

class ActivateAccountView(APIView):
    def get(self, request, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            if payload.get("type") != "activation":
                return Response({"error": "Invalid token type"}, status=status.HTTP_400_BAD_REQUEST)
            
            user_id = payload.get("user_id")
            user = User.objects.get(id=user_id)
            if user.verified:
                return Response({"detail": "Account already activated"}, status=status.HTTP_200_OK)
            
            user.verified = True
            user.save()
            return Response({"detail": "Account activated successfully"}, status=status.HTTP_200_OK)
        
        except jwt.ExpiredSignatureError:
            return Response({"error": "Activation link expired"}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.InvalidTokenError:
            return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
class RequestPasswordResetView(APIView):
    def post(self, request):
        email = request.data.get("email")
        try:
            user = User.objects.get(email=email)
            send_password_reset_email(user, request)
            return Response({"detail": "Password reset email sent."}, status=200)
        except User.DoesNotExist:
            return Response({"detail": "User with this email does not exist."}, status=404)
        
class ResetPasswordView(APIView):
    def post(self, request, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            if payload["type"] != "password_reset":
                raise jwt.InvalidTokenError

            user = User.objects.get(id=payload["user_id"])
            password = request.data.get("password")
            password2 = request.data.get("password2")

            if password != password2:
                return Response({"detail": "Passwords do not match."}, status=400)

            user.set_password(password)
            user.save()
            return Response({"detail": "Password has been reset."}, status=200)

        except jwt.ExpiredSignatureError:
            return Response({"detail": "Token has expired."}, status=400)
        except jwt.InvalidTokenError:
            return Response({"detail": "Invalid token."}, status=400)
        except User.DoesNotExist:
            return Response({"detail": "User does not exist."}, status=404)
        

class UserUpdateView(RetrieveUpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user



class PremiumProtectedView(APIView):
    permission_classes = [IsAuthenticated, IsFreeTrialValid]

    def get(self, request):
        return Response({"message": "Welcome to the premium content!"}, status=status.HTTP_200_OK)
