import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
import joblib
import os
from django.conf import settings
from django.utils.timezone import now

def generate_activation_jwt(user):
    payload = {
        "user_id": user.id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
        "type": "activation"
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token

def send_activation_email(user, request):
    token = generate_activation_jwt(user)
    activation_url = request.build_absolute_uri(
        reverse('activate-account', kwargs={'token': token})
    )
    subject = 'Activate your account'
    message = f"Hi {user.username}, activate your account here:\n{activation_url}"
    send_mail(subject, message, 'abdo.moh4443@gmail.com', [user.email])


def generate_password_reset_jwt(user):
    payload = {
        "user_id": user.id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
        "type": "password_reset"
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    return token

def send_password_reset_email(user, request):
    token = generate_password_reset_jwt(user)
    reset_url = request.build_absolute_uri(
        reverse('reset-password', kwargs={'token': token})
    )
    subject = 'Reset your password'
    message = f"Hi {user.username}, reset your password here:\n{reset_url}"
    send_mail(subject, message, 'abdo.moh4443@gmail.com', [user.email])

MODEL_PATH = os.path.join(settings.BASE_DIR, 'cards', 'ml_models', 'click_model.pkl')

def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    else:
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

def activate_premium(user):
    user.account_type = 'premium'
    user.premium_expiry = now() + timedelta(days=30) 
    user.save()