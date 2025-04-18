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

    def create_company_user(self, email, name, company_data, password=None, **extra_fields):
        """Create a user associated with a company registration"""
        # Set is_active to False by default for company users (pending approval)
        extra_fields.setdefault('is_active', False)

        # Create the user
        user = self.create_user(
            email=email,
            name=name,
            password=password,
            **extra_fields
        )

        # Import here to avoid circular imports
        from accounts.models import Company

        # Create the company
        company = Company(
            vat_number=company_data.get('vat_number'),
            official_name=company_data.get('official_name'),
            business_address=company_data.get('business_address'),
            phone_number=company_data.get('phone_number'),
            email=company_data.get('email', email),
            website=company_data.get('website', None)
        )
        company.save()

        return user

    def approve_company(self, company_id, admin_user=None):
        """Approve a company and create a user account with the registration credentials"""
        from accounts.models import Company, Account
        from django.utils import timezone

        try:
            company = Company.objects.get(id=company_id)

            if company.status == 'approved':
                return company

            if company.status == 'rejected':
                raise ValueError('Cannot approve a rejected company')

            # Update company status
            company.status = 'approved'
            company.approval_date = timezone.now()

            # Find or create user with the company's email
            user = self.get_queryset().filter(email=company.email).first()

            if not user and company.email and company.password:
                # Create a new user with the registration credentials
                # Since the password is already hashed, we need to create the user manually

                user = self.model(
                    email=company.email,
                    name=company.official_name,
                    username=company.email,
                    is_active=True
                )

                # Set the password directly from the hashed password
                user.password = company.password
                user.save()

                # Create an account for the user
                account = Account(user=user)
                account.save()

                # Clear the password from the company record for security
                company.password = None
            elif user:
                # Activate existing user
                user.is_active = True
                user.save()

                # Create an account if it doesn't exist
                if not hasattr(user, 'account'):
                    account = Account(user=user)
                    account.save()

            company.save()
            return company

        except Company.DoesNotExist:
            raise ValueError(f'Company with ID {company_id} does not exist')

    def reject_company(self, company_id):
        """Reject a company"""
        from accounts.models import Company

        try:
            company = Company.objects.get(id=company_id)

            if company.status == 'rejected':
                return company

            # Update company status
            company.status = 'rejected'
            company.save()

            # Find and deactivate associated user
            user = self.get_queryset().filter(email=company.email).first()
            if user:
                user.is_active = False
                user.save()

            return company

        except Company.DoesNotExist:
            raise ValueError(f'Company with ID {company_id} does not exist')

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

