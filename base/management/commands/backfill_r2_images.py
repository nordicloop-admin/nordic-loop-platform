import io
import hashlib
from typing import List
from django.core.management.base import BaseCommand
from django.apps import apps
from django.conf import settings
from base.models import ImageMigrationRecord
from base.services.r2_storage_service import r2_storage_service
from base.services.firebase_service import firebase_storage_service
import logging
import requests

logger = logging.getLogger(__name__)

IMAGE_FIELD_CLASS = 'base.fields.FirebaseImageField'

class Command(BaseCommand):
    help = "Backfill existing Firebase image URLs into R2 storage and record migration mapping"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Do not upload, just list pending images')
        parser.add_argument('--batch-size', type=int, default=200, help='Process this many records per batch')
        parser.add_argument('--max', type=int, default=None, help='Max total records to process')
        parser.add_argument('--verify', action='store_true', help='After upload, verify size match')

    def handle(self, *args, **options):
        if not getattr(settings, 'CLOUDFLARE_R2_BUCKET', ''):
            self.stderr.write(self.style.ERROR('R2 not configured. Aborting.'))
            return
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        max_total = options['max']
        verify = options['verify']

        self.stdout.write(self.style.NOTICE('Scanning models for FirebaseImageField usage...'))
        targets = self._collect_targets()
        total = 0
        for model, field in targets:
            qs = model.objects.exclude(**{f"{field.name}__isnull": True}).exclude(**{field.name: ''})
            for obj in qs.iterator():
                firebase_url = getattr(obj, field.name)
                if not firebase_url or 'firebasestorage.googleapis.com' not in firebase_url:
                    continue
                # Skip if already migrated
                if ImageMigrationRecord.objects.filter(original_firebase_url=firebase_url, status__in=['migrated','verified']).exists():
                    continue
                if max_total and total >= max_total:
                    break
                total += 1
                if dry_run:
                    self.stdout.write(f"DRY RUN: Would migrate {firebase_url}")
                    self._ensure_record(firebase_url, model, obj, field)
                    continue
                try:
                    success, r2_url = self._migrate(firebase_url, model, obj, field, verify)
                    if success:
                        self.stdout.write(self.style.SUCCESS(f"Migrated -> {r2_url}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"Migration failed for {firebase_url}"))
                except Exception as e:
                    logger.exception("Unexpected error during migration")
                    rec = self._ensure_record(firebase_url, model, obj, field)
                    rec.status = 'failed'
                    rec.last_error = str(e)
                    rec.attempts += 1
                    rec.save()
            if max_total and total >= max_total:
                break
        self.stdout.write(self.style.SUCCESS(f"Processed {total} records."))

    def _collect_targets(self) -> List:
        targets = []
        for model in apps.get_models():
            for field in model._meta.get_fields():
                if hasattr(field, 'get_internal_type') and field.get_internal_type() == 'URLField':
                    # heuristic: check class path
                    if field.__class__.__module__.startswith('base.fields'):
                        targets.append((model, field))
        return targets

    def _ensure_record(self, firebase_url, model, obj, field):
        rec, _ = ImageMigrationRecord.objects.get_or_create(
            original_firebase_url=firebase_url,
            object_model=model._meta.label,
            object_id=str(obj.pk),
            field_name=field.name,
            defaults={'status': 'pending'}
        )
        return rec

    def _migrate(self, firebase_url, model, obj, field, verify):
        rec = self._ensure_record(firebase_url, model, obj, field)
        rec.attempts += 1
        try:
            # Download image bytes
            resp = requests.get(firebase_url, timeout=20)
            if resp.status_code != 200:
                rec.status = 'failed'
                rec.last_error = f"HTTP {resp.status_code}"
                rec.save()
                return False, None
            data = resp.content
            checksum = hashlib.sha256(data).hexdigest()
            rec.checksum = checksum
            rec.size_bytes = len(data)
            # Upload to R2 using same relative path logic (no user id context here, treat as raw)
            # Use folder 'backfill' to avoid collisions; or parse from URL later if needed.
            file_like = io.BytesIO(data)
            file_like.name = 'migrated_image'
            success, msg, r2_url = r2_storage_service.upload_image(file_like, folder='backfill', user_id=None)
            if not success:
                rec.status = 'failed'
                rec.last_error = msg
                rec.save()
                return False, None
            rec.r2_url = r2_url
            if verify:
                # HEAD R2 metadata
                meta = r2_storage_service.get_image_metadata(r2_url)
                if meta and meta.get('size') == len(data):
                    rec.status = 'verified'
                else:
                    rec.status = 'migrated'
            else:
                rec.status = 'migrated'
            rec.save()
            return True, r2_url
        except Exception as e:
            rec.status = 'failed'
            rec.last_error = str(e)
            rec.save()
            return False, None
