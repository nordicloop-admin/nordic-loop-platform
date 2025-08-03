# Generated manually for broker feature

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0012_ad_status_ad_suspended_by_admin'),
    ]

    operations = [
        migrations.AddField(
            model_name='ad',
            name='allow_broker_bids',
            field=models.BooleanField(default=True, help_text='Allow brokers to place bids on this material'),
        ),
    ]
