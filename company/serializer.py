from rest_framework import serializers
from .models import Company

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
        Construct contacts array from primary and secondary contact fields
        """
        contacts = []
        
        # Primary contact
        if obj.primary_first_name and obj.primary_last_name and obj.primary_email:
            primary_contact = {
                'name': f"{obj.primary_first_name} {obj.primary_last_name}",
                'email': obj.primary_email,
                'position': obj.primary_position or ""
            }
            contacts.append(primary_contact)
        
        # Secondary contact
        if obj.secondary_first_name and obj.secondary_last_name and obj.secondary_email:
            secondary_contact = {
                'name': f"{obj.secondary_first_name} {obj.secondary_last_name}",
                'email': obj.secondary_email,
                'position': obj.secondary_position or ""
            }
            contacts.append(secondary_contact)
        
        return contacts


class AdminCompanyDetailSerializer(AdminCompanyListSerializer):
    """
    Admin serializer for company detail view - extends list serializer
    """
    # Add any additional fields for detail view if needed
    website = serializers.URLField(read_only=True)
    
    class Meta(AdminCompanyListSerializer.Meta):
        fields = AdminCompanyListSerializer.Meta.fields + ['website']