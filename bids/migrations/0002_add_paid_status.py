# Generated manually for adding 'paid' status to Bid model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bids', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bid',
            name='status',
            field=models.CharField(
                choices=[
                    ('active', 'Active'),
                    ('outbid', 'Outbid'),
                    ('winning', 'Winning'),
                    ('won', 'Won'),
                    ('paid', 'Paid'),
                    ('lost', 'Lost'),
                    ('cancelled', 'Cancelled')
                ],
                default='active',
                max_length=20
            ),
        ),
    ]
