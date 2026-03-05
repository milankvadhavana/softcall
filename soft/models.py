# accounts/models.py — COMPLETE FIXED FILE
# Fix: added updated_at field to CustomUser (NOT NULL constraint fix)

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff',     True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role',         'superadmin')
        extra_fields.setdefault('status',       'active')
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = (
        ('superadmin', 'Superadmin'),
        ('admin',      'Admin'),
        ('user',       'User'),
    )

    STATUS_CHOICES = (
        ('active',    'Active'),
        ('inactive',  'Inactive'),
        ('suspended', 'Suspended'),
    )

    # Common fields
    name       = models.CharField(max_length=150)
    email      = models.EmailField(unique=True)
    mobile     = models.CharField(max_length=15, unique=True)
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    # Admin-specific fields
    company    = models.CharField(max_length=255, blank=True, null=True)
    plan_start = models.DateField(blank=True, null=True)
    plan_end   = models.DateField(blank=True, null=True)

    # Relationship
    created_by = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='users_created'
    )

    # ✅ FIX: added auto timestamps — these were in DB but missing from model
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)   # ← THIS was missing

    # Django required fields
    is_staff     = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active    = models.BooleanField(default=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['name', 'mobile']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.name} ({self.role})"

    @property
    def is_plan_active(self):
        if self.role != 'admin':
            return True
        if not self.plan_end:
            return False
        return timezone.now().date() <= self.plan_end

    @property
    def is_account_active(self):
        if self.role == 'admin':
            return self.status == 'active' and self.is_plan_active
        return self.status == 'active'

    class Meta:
        verbose_name        = 'User'
        verbose_name_plural = 'Users'


class ContactData(models.Model):
    added_by = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='contacts_added',
        limit_choices_to={'role': 'admin'}
    )
    assigned_to = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='contacts_assigned',
        limit_choices_to={'role': 'user'}
    )
    name           = models.CharField(max_length=150)
    contact_number = models.CharField(max_length=15)
    email          = models.EmailField(blank=True, null=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} → {self.assigned_to.name}"

    class Meta:
        verbose_name        = 'Contact'
        verbose_name_plural = 'Contacts'
        ordering            = ['-created_at']