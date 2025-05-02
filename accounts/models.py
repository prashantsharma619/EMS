from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django_countries.fields import CountryField
from django.core import signing
import secrets
from datetime import timedelta
from django.utils import timezone


class RoleChoices(models.TextChoices):
    SUPER_ADMIN = '1', 'Super Admin'
    EMPLOYEE = '2', 'Employee'
    MANAGER = '3', 'Manager'

class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', RoleChoices.SUPER_ADMIN)

        return self.create_user(email, first_name, last_name, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    country_code = CountryField(blank=True, null=True)

    role = models.CharField(max_length=2, choices=RoleChoices.choices, default=RoleChoices.EMPLOYEE)

    device_id = models.CharField(max_length=255, blank=True, null=True)
    device_type = models.CharField(max_length=10, choices=[('android', 'Android'), ('ios', 'iOS'), ('web', 'Web')], blank=True, null=True)
    app_info = models.JSONField(blank=True, null=True)

    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    def get_hashed_id(self):
        return signing.dumps(self.pk)


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    @classmethod
    def create_token(cls, user):
        # Delete any existing tokens for this user
        cls.objects.filter(user=user).delete()
        
        # Create new token
        token = secrets.token_urlsafe(48)
        expires_at = timezone.now() + timedelta(hours=24)
        return cls.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at