# Generated migration for payments app

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators
import uuid
from decimal import Decimal


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('bids', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StripeAccount',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('stripe_account_id', models.CharField(max_length=255, unique=True)),
                ('account_status', models.CharField(choices=[('pending', 'Pending'), ('active', 'Active'), ('restricted', 'Restricted'), ('inactive', 'Inactive')], default='pending', max_length=20)),
                ('bank_account_last4', models.CharField(blank=True, max_length=4, null=True)),
                ('bank_name', models.CharField(blank=True, max_length=255, null=True)),
                ('bank_country', models.CharField(blank=True, max_length=2, null=True)),
                ('charges_enabled', models.BooleanField(default=False)),
                ('payouts_enabled', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='stripe_account', to='users.user')),
            ],
            options={
                'verbose_name': 'Stripe Account',
                'verbose_name_plural': 'Stripe Accounts',
            },
        ),
        migrations.CreateModel(
            name='PaymentIntent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('stripe_payment_intent_id', models.CharField(max_length=255, unique=True)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('commission_amount', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('seller_amount', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('commission_rate', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.00')), django.core.validators.MaxValueValidator(Decimal('100.00'))])),
                ('status', models.CharField(choices=[('requires_payment_method', 'Requires Payment Method'), ('requires_confirmation', 'Requires Confirmation'), ('requires_action', 'Requires Action'), ('processing', 'Processing'), ('requires_capture', 'Requires Capture'), ('canceled', 'Canceled'), ('succeeded', 'Succeeded')], default='requires_payment_method', max_length=30)),
                ('currency', models.CharField(default='SEK', max_length=3)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('bid', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payment_intent', to='bids.bid')),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_intents', to='users.user')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_payments', to='users.user')),
            ],
            options={
                'verbose_name': 'Payment Intent',
                'verbose_name_plural': 'Payment Intents',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('transaction_type', models.CharField(choices=[('payment', 'Payment'), ('commission', 'Commission'), ('payout', 'Payout'), ('refund', 'Refund')], max_length=20)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('currency', models.CharField(default='SEK', max_length=3)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('failed', 'Failed'), ('canceled', 'Canceled')], default='pending', max_length=20)),
                ('stripe_transfer_id', models.CharField(blank=True, max_length=255, null=True)),
                ('stripe_charge_id', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('payment_intent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='payments.paymentintent')),
                ('from_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='outgoing_transactions', to='users.user')),
                ('to_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='incoming_transactions', to='users.user')),
            ],
            options={
                'verbose_name': 'Transaction',
                'verbose_name_plural': 'Transactions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PayoutSchedule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('currency', models.CharField(default='SEK', max_length=3)),
                ('status', models.CharField(choices=[('scheduled', 'Scheduled'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('canceled', 'Canceled')], default='scheduled', max_length=20)),
                ('scheduled_date', models.DateField()),
                ('processed_date', models.DateField(blank=True, null=True)),
                ('stripe_payout_id', models.CharField(blank=True, max_length=255, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payout_schedules', to='users.user')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_payouts', to='users.user')),
                ('processed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_payouts', to='users.user')),
                ('transactions', models.ManyToManyField(blank=True, related_name='payout_schedules', to='payments.transaction')),
            ],
            options={
                'verbose_name': 'Payout Schedule',
                'verbose_name_plural': 'Payout Schedules',
                'ordering': ['-scheduled_date'],
            },
        ),
    ]
