from django.db import models

# Create your models here.
from datetime import date, datetime, timedelta
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
    
    def save(self, *args, **kwargs):
        if self.account_type == 'premium' and self.premium_expiry:
            if now() > self.premium_expiry:
                self.account_type = 'free'
        else:
            self.account_type = 'premium'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username