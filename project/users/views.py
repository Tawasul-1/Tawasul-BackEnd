from datetime import timedelta
import jwt
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView, ListAPIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from .models import User
from .utiles import send_activation_email, send_password_reset_email ,activate_premium
from .serializers import RegisterSerializer, LoginSerializer, UserListSerializer, UserProfileSerializer, UserUpdateSerializer
from users.permissions import IsFreeTrialValid, IsPremiumUser
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from cards.utils import create_board_with_initial_cards
from django.urls import reverse



class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    def perform_create(self, serializer):
        user = serializer.save()
        create_board_with_initial_cards(user)
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
    permission_classes = [IsAuthenticated,IsPremiumUser ]

    def get(self, request):
        return Response({"message": "Welcome to the premium content!"}, status=status.HTTP_200_OK)

class PaymobGetPaymentUrlView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.is_premium:
            return Response({"message": "your account is already premium "}, status=200)

        auth_response = requests.post(
            "https://accept.paymob.com/api/auth/tokens",
            json={"api_key": settings.PAYMOB_API_KEY}
        )
        token = auth_response.json().get("token")

        order_response = requests.post(
            "https://accept.paymob.com/api/ecommerce/orders",
            json={
                "auth_token": token,
                "delivery_needed": False,
                "amount_cents": "100000",
                "currency": "EGP",
                "items": [],
            }
        )
        order_id = order_response.json()["id"]

        payment_key_response = requests.post(
            "https://accept.paymob.com/api/acceptance/payment_keys",
            json={
                "auth_token": token,
                "amount_cents": "100000",
                "expiration": 3600,
                "order_id": order_id,
                "billing_data": {
                    "apartment": "NA",
                    "email": user.email,
                    "floor": "NA",
                    "first_name": user.first_name or "NA",
                    "last_name": user.last_name or "NA",
                    "street": "NA",
                    "building": "NA",
                    "phone_number": user.phone or "01234567890",
                    "city": "Cairo",
                    "country": "EG",
                    "state": "Cairo"
                },
                "currency": "EGP",
                "integration_id": settings.PAYMOB_INTEGRATION_ID,
                "lock_order_when_paid": False,
                "redirect_url": f"http://localhost:8000/users/payment/success/?email={user.email}&success=true"
            }
        )
        payment_token = payment_key_response.json()["token"]

        iframe_url = f"https://accept.paymob.com/api/acceptance/iframes/{settings.PAYMOB_IFRAME_ID}?payment_token={payment_token}"
        return Response({"iframe_url": iframe_url})

def paymob_success_redirect(request):
    success = request.GET.get("success")
    email = request.GET.get("email")

    if success == "true" and email:
        try:
            user = User.objects.get(email=email)
            activate_premium(user) 
            return HttpResponse("Your payment was successful and your account has been upgraded to premium.")
        except User.DoesNotExist:
            return HttpResponse("There is no user with this email.")
    return HttpResponse("There was an error with the payment.")

class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.account_type != 'premium':
            return Response({"message": "your account is on free plan ."}, status=status.HTTP_400_BAD_REQUEST)

        user.cancel_subscription()
        return Response({
            "message": f"your subscription has been successfully canceled: You will enjoy premium features  until {user.premium_expiry}."
        }, status=status.HTTP_200_OK)

class SubscriptionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "account_type": user.account_type,
            "is_premium": user.is_premium,
            "premium_start": (user.premium_expiry - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S') 
                              if user.premium_expiry else None,
            "premium_expiry": user.premium_expiry.strftime('%Y-%m-%d %H:%M:%S') if user.premium_expiry else None,
            "is_subscription_cancelled": user.is_subscription_cancelled,
        }, status=status.HTTP_200_OK)

class UserListView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [IsAdminUser] 