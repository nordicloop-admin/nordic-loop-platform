from rest_framework import serializers
from .models import Company
from django.contrib.auth import get_user_model

User = get_user_model()

class ContactSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    position = serializers.CharField()

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"

    def validate_vat_number(self, value):
        # Check if VAT number already exists
        if Company.objects.filter(vat_number=value).exists():
            raise serializers.ValidationError("A company with this VAT number already exists.")
        return value

    def validate_email(self, value):
        # Check if email already exists
        if Company.objects.filter(email=value).exists():
            raise serializers.ValidationError("A company with this email already exists.")
        return value


class AdminCompanyListSerializer(serializers.ModelSerializer):
    """
    Admin serializer for company list view with specific field mapping
    """
    companyName = serializers.CharField(source='official_name', read_only=True)
    vatNumber = serializers.CharField(source='vat_number', read_only=True)
    companyEmail = serializers.EmailField(source='email', read_only=True)
    registrationDate = serializers.DateField(source='registration_date', read_only=True)
    contacts = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            'id',
            'companyName', 
            'vatNumber',
            'country',
            'sector',
            'companyEmail',
            'status',
            'registrationDate',
            'contacts'
        ]

    def get_contacts(self, obj):
        """
        Construct contacts array from User model (normalized structure)
        Data has been migrated from Company fields to User model
        """
        contacts = []

        # Get contacts from User model (normalized structure)
        user_contacts = User.objects.filter(
            company=obj,
            contact_type__in=['primary', 'secondary']
        ).order_by('contact_type')  # primary comes before secondary alphabetically

        for user in user_contacts:
            contact = {
                'name': f"{user.first_name} {user.last_name}".strip(),
                'email': user.email,
                'position': user.position or ""
            }
            contacts.append(contact)

        return contacts


class AdminCompanyDetailSerializer(AdminCompanyListSerializer):
    """
    Admin serializer for company detail view - extends list serializer
    """
    # Add any additional fields for detail view if needed
    website = serializers.URLField(read_only=True)

    class Meta(AdminCompanyListSerializer.Meta):
        fields = AdminCompanyListSerializer.Meta.fields + ['website']