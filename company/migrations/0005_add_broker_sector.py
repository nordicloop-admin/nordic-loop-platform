# Generated manually for broker feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0004_remove_contact_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='company',
            name='sector',
            field=models.CharField(
                choices=[
                    ('manufacturing  & Production', 'Manufacturing & Production'),
                    ('construction', 'Construction & Demolition'),
                    ('retail', 'Wholesale & Retail'),
                    ('packaging', 'Packaging & Printing'),
                    ('recycling', 'Recycling & Waste Management'),
                    ('Energy & Utilities', 'Energy & Utilities'),
                    ('broker', 'Broker'),
                    ('Other', 'Other')
                ],
                default='manufacturing  & Production',
                max_length=255
            ),
        ),
    ]
