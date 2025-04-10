from django.db import migrations, models
from django.db.models import Q


def forward_func(apps, schema_editor):
    Company = apps.get_model('accounts', 'Company')
    CustomUser = apps.get_model('users', 'CustomUser')
    
    # Get all companies with null users
    companies_without_users = Company.objects.filter(user__isnull=True)
    
    for company in companies_without_users:
        # Create a new user for each company without one
        # Use a default email based on company name since email field doesn't exist yet
        default_email = f"{company.official_name.lower().replace(' ', '_')}@example.com"
        user = CustomUser.objects.create(
            email=default_email,
            name=company.official_name,
            is_active=False  # Set to False initially for safety
        )
        company.user = user
        company.save()

def reverse_func(apps, schema_editor):
    # No reverse operation needed - we don't want to delete users
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_company_approval_date_company_status_and_more'),
    ]

    operations = [
        migrations.RunPython(forward_func, reverse_func),
        migrations.AlterField(
            model_name='company',
            name='user',
            field=models.OneToOneField(
                on_delete=models.CASCADE,
                related_name='company',
                to='users.CustomUser'
            ),
        ),
    ]
