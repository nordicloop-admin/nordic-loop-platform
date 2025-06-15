from rest_framework import serializers
from company.models import Company

class ContactSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    position = serializers.CharField()

class CompanyAdminSerializer(serializers.ModelSerializer):
    contacts = serializers.SerializerMethodField()
    companyName = serializers.CharField(source='official_name')
    vatNumber = serializers.CharField(source='vat_number')
    companyEmail = serializers.EmailField(source='email')
    companyPhone = serializers.CharField(source='website', required=False)  # Placeholder, adjust if phone field exists
    status = serializers.CharField()
    createdAt = serializers.DateField(source='registration_date')
    sector = serializers.CharField()
    country = serializers.CharField()
    id = serializers.CharField(source='pk')

    class Meta:
        model = Company
        fields = [
            'id', 'companyName', 'vatNumber', 'country', 'sector', 'companyEmail', 'companyPhone',
            'contacts', 'status', 'createdAt'
        ]

    def get_contacts(self, obj):
        contacts = []
        if obj.primary_first_name or obj.primary_last_name or obj.primary_email:
            contacts.append({
                'name': f"{obj.primary_first_name or ''} {obj.primary_last_name or ''}".strip(),
                'email': obj.primary_email or '',
                'position': obj.primary_position or ''
            })
        if obj.secondary_first_name or obj.secondary_last_name or obj.secondary_email:
            contacts.append({
                'name': f"{obj.secondary_first_name or ''} {obj.secondary_last_name or ''}".strip(),
                'email': obj.secondary_email or '',
                'position': obj.secondary_position or ''
            })
        return contacts

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'