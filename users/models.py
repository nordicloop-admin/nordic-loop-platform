from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
import uuid

class CustomUserManager(UserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not name:
            raise ValueError('The Name field must be set')
            
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            name=name,
            username=email,  # Using email as username
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(
            email=email,
            name=name,
            password=password,
            **extra_fields
        )

class CustomUser(AbstractUser):
    objects = CustomUserManager()
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, default='Anonymous User')
    subscription_status = models.CharField(max_length=20, default='basic')
    
    username = models.CharField(
        max_length=150,
        unique=True,
        null=True,  
        blank=True 
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']  # Ensure this matches fields needed for createsuperuser

    def save(self, *args, **kwargs):
        if not self.username:
            # Generate a unique username if one isn't set
            while True:
                username = f"user_{uuid.uuid4().hex[:8]}"
                if not CustomUser.objects.filter(username=username).exists():
                    self.username = username
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.email})"

