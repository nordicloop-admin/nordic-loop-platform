from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_user_payout_frequency_user_payout_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='passwordresetotp',
            name='purpose',
            field=models.CharField(choices=[('password_reset', 'Password Reset'), ('account_activation', 'Account Activation')], default='password_reset', max_length=30),
        ),
    ]
