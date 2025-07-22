from django.db import models

from datetime import date, timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils.timezone import now

PHONE_REGEX = RegexValidator(regex=r'^01[0125][0-9]{8}$')

ACCOUNT_TYPES = (
    ('free', 'Free'),
    ('premium', 'Premium'),
)

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    profile_picture = models.ImageField(default='default.jpg', upload_to='profile_pictures/', blank=True, null=True)
    verified = models.BooleanField(default=False)
    address = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(default=date(2000, 1, 1))
    phone = models.CharField(validators=[PHONE_REGEX], max_length=11, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, default='free')
    premium_expiry = models.DateTimeField(null=True, blank=True)
    is_subscription_cancelled = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_premium(self):
        if self.account_type == 'premium' and self.premium_expiry and now() < self.premium_expiry:
            return True
        return False
    
    def cancel_subscription(self):
        if self.account_type == 'premium':
            self.is_subscription_cancelled = True
            self.save()
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.account_type = 'premium'
            self.premium_expiry = now() + timedelta(days=30)
            self.is_subscription_cancelled = False

        if self.premium_expiry and now() > self.premium_expiry:
            self.account_type = 'free'
            self.is_subscription_cancelled = False
        else:
            self.account_type = 'premium'

        super().save(*args, **kwargs)
    
    def activate_premium(self):
        self.account_type = 'premium'
        self.premium_expiry = now() + timedelta(days=30)
        self.save()

    def __str__(self):
        return self.username