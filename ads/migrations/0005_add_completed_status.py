# Generated manually for adding 'completed' status to Ad model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0004_ad_custom_auction_duration_alter_ad_auction_duration_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ad',
            name='status',
            field=models.CharField(
                choices=[
                    ('active', 'Active'),
                    ('suspended', 'Suspended by Admin'),
                    ('completed', 'Completed')
                ],
                default='active',
                max_length=20
            ),
        ),
    ]
