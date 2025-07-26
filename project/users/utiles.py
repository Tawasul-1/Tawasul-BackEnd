import jwt
from datetime import datetime, timedelta, timezone
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
import joblib
import os
from django.conf import settings
from django.utils.timezone import now
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives

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

    # Build activation URL
    activation_url = f"{settings.TAWASUL_URL}/verify-email/{token}"

    # Email content
    subject = "مرحبًا بك في تواصل - فعّل حسابك"

    # Context for HTML template
    context = {
        'user': user,
        'activation_url': activation_url,
        'support_email': 'support@tawasul.com',
        'expiry_hours': 24,
    }

    # Render HTML and plain text versions
    html_content = render_to_string('emails/account_activation.html', context)
    text_content = strip_tags(html_content)

    # Create and send email
    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        reply_to=[settings.EMAIL_HOST_USER],
    )
    email.attach_alternative(html_content, "text/html")

    # Optional headers for deliverability
    email.extra_headers = {
        'X-Priority': '1',
        'X-MC-Tags': 'account-activation',
    }

    email.send()



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
    reset_url = f"{settings.TAWASUL_URL}/new-password/{token}/"

    # Email subject
    subject = "إعادة تعيين كلمة المرور - تواصل"

    # Context to pass into HTML template
    context = {
        'user': user,
        'reset_url': reset_url,
        'support_email': 'support@tawasul.com',
        'expiry_hours': 1,
    }

    # Load HTML and plain text versions
    html_content = render_to_string('emails/password_reset_email.html', context)
    text_content = strip_tags(html_content)

    # Build and send email
    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        reply_to=[settings.EMAIL_HOST_USER],
    )
    email.attach_alternative(html_content, "text/html")

    # Add optional headers
    email.extra_headers = {
        'X-Priority': '1',
        'X-MC-Tags': 'password-reset',
    }

    email.send()

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