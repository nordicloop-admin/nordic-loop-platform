"""
Management command to clone/export User and Company data between databases.

Supports three main modes:
1. export -> writes JSON files for users and companies
2. import -> reads JSON files and loads into target (default/secondary)
3. direct  -> clones directly from one configured DB alias to another (no disk)

Examples:
  python manage.py clone_user_company_data --mode export --output /tmp
  python manage.py clone_user_company_data --mode import --input /tmp --target secondary
  python manage.py clone_user_company_data --mode direct --source default --target secondary

Prerequisites:
  - Define SECONDARY_DATABASE_URL in environment for a 'secondary' DB alias (already supported in settings)

Safety:
  - Import and direct modes require --confirm to actually write
  - Dry run by default (shows counts)
"""
import json
import os
from datetime import datetime
from django.utils import timezone
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import connections, transaction
from company.models import Company

User = get_user_model()

SAFE_USER_FIELDS = [
    'id','username','email','first_name','last_name','name','company_id','can_place_ads','can_place_bids',
    'role','is_primary_contact','contact_type','position','bank_country','bank_currency','bank_account_holder',
    'bank_account_number','bank_routing_number','payout_frequency','payout_method','is_staff','is_superuser',
    'is_active','date_joined','last_login'
]

SAFE_COMPANY_FIELDS = [
    'id','official_name','vat_number','email','sector','country','website','registration_date','status',
    'stripe_account_id','stripe_capabilities_complete','stripe_onboarding_complete','payment_ready','last_payment_check'
]

class Command(BaseCommand):
    help = 'Clone/export User and Company data between databases or to JSON files'

    def add_arguments(self, parser):
        parser.add_argument('--mode', choices=['export','import','direct'], required=True, help='Operation mode')
        parser.add_argument('--output', type=str, help='Directory to write JSON export')
        parser.add_argument('--input', type=str, help='Directory containing JSON files to import')
        parser.add_argument('--source', type=str, default='default', help='Source DB alias (for direct mode)')
        parser.add_argument('--target', type=str, default='secondary', help='Target DB alias (for import/direct modes)')
        parser.add_argument('--confirm', action='store_true', help='Actually perform write operations (otherwise dry-run)')
        parser.add_argument('--batch-size', type=int, default=500, help='Batch size for bulk operations')

    def handle(self, *args, **opts):
        mode = opts['mode']
        if mode == 'export':
            self.do_export(opts)
        elif mode == 'import':
            self.do_import(opts)
        else:
            self.do_direct(opts)

    def do_export(self, opts):
        out_dir = opts.get('output') or './export_data'
        os.makedirs(out_dir, exist_ok=True)
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')

        companies = Company.objects.all().values(*SAFE_COMPANY_FIELDS)
        users = User.objects.all().values(*SAFE_USER_FIELDS)

        company_path = os.path.join(out_dir, f'companies_{timestamp}.json')
        user_path = os.path.join(out_dir, f'users_{timestamp}.json')

        with open(company_path,'w') as cf:
            json.dump(list(companies), cf, default=str, indent=2)
        with open(user_path,'w') as uf:
            json.dump(list(users), uf, default=str, indent=2)

        self.stdout.write(self.style.SUCCESS(f'Exported {companies.count()} companies -> {company_path}'))
        self.stdout.write(self.style.SUCCESS(f'Exported {users.count()} users -> {user_path}'))

    def do_import(self, opts):
        in_dir = opts.get('input')
        if not in_dir or not os.path.isdir(in_dir):
            raise CommandError('Valid --input directory required for import mode')
        target = opts['target']
        if target not in connections:
            raise CommandError(f'Target DB alias {target} not configured')

        # Find latest files
        company_file = self._latest_file(in_dir, 'companies_')
        user_file = self._latest_file(in_dir, 'users_')
        if not (company_file and user_file):
            raise CommandError('Could not find companies_*.json and users_*.json in input directory')

        with open(company_file) as cf:
            companies = json.load(cf)
        with open(user_file) as uf:
            users = json.load(uf)

        self.stdout.write(f'Ready to import {len(companies)} companies and {len(users)} users into {target}')
        if not opts['confirm']:
            self.stdout.write(self.style.WARNING('Dry run only. Re-run with --confirm to execute.'))
            return

        using = target
        with transaction.atomic(using=using):
            # Insert companies (respect ids)
            self._bulk_insert(Company, companies, SAFE_COMPANY_FIELDS, using)
            # Insert users
            self._bulk_insert(User, users, SAFE_USER_FIELDS, using)
        self.stdout.write(self.style.SUCCESS('Import completed.'))

    def do_direct(self, opts):
        source = opts['source']
        target = opts['target']
        if source not in connections:
            raise CommandError(f'Source DB alias {source} not configured')
        if target not in connections:
            raise CommandError(f'Target DB alias {target} not configured')

        companies = Company.objects.using(source).all().values(*SAFE_COMPANY_FIELDS)
        users = User.objects.using(source).all().values(*SAFE_USER_FIELDS)
        self.stdout.write(f'Cloning {companies.count()} companies and {users.count()} users from {source} -> {target}')
        if not opts['confirm']:
            self.stdout.write(self.style.WARNING('Dry run only. Re-run with --confirm to execute.'))
            return

        using = target
        with transaction.atomic(using=using):
            self._bulk_insert(Company, list(companies), SAFE_COMPANY_FIELDS, using)
            self._bulk_insert(User, list(users), SAFE_USER_FIELDS, using)
        self.stdout.write(self.style.SUCCESS('Direct clone completed.'))

    def _bulk_insert(self, model_cls, rows, allowed_fields, using):
        if not rows:
            return
        objs = []
        for row in rows:
            data = {f: row.get(f) for f in allowed_fields if f in row}
            objs.append(model_cls(**data))
        model_cls.objects.using(using).bulk_create(objs, ignore_conflicts=True)

    def _latest_file(self, dir_path, prefix):
        candidates = [f for f in os.listdir(dir_path) if f.startswith(prefix) and f.endswith('.json')]
        if not candidates:
            return None
        candidates.sort(reverse=True)
        return os.path.join(dir_path, candidates[0])
