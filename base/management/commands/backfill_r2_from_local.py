import os
import io
import hashlib
from django.core.management.base import BaseCommand
from django.conf import settings
from base.models import ImageMigrationRecord
from base.services.r2_storage_service import r2_storage_service
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Backfill existing local MEDIA_ROOT files into R2 preserving relative paths"

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='List files that would be migrated')
        parser.add_argument('--folder', default='', help='Restrict to subfolder under MEDIA_ROOT')
        parser.add_argument('--limit', type=int, default=None, help='Max number of files to process')
        parser.add_argument('--verify', action='store_true', help='Verify size after upload')
        parser.add_argument('--extensions', default='jpg,jpeg,png,gif,webp', help='Comma-separated allowed extensions')

    def handle(self, *args, **options):
        if not getattr(settings, 'CLOUDFLARE_R2_BUCKET', ''):
            self.stderr.write(self.style.ERROR('R2 not configured. Aborting.'))
            return
        media_root = settings.MEDIA_ROOT
        subfolder = options['folder'].strip('/')
        root_path = os.path.join(media_root, subfolder) if subfolder else media_root
        allowed_exts = {e.lower().strip() for e in options['extensions'].split(',') if e.strip()}
        dry_run = options['dry_run']
        limit = options['limit']
        verify = options['verify']
        count = 0

        self.stdout.write(self.style.NOTICE(f'Scanning local media path: {root_path}'))

        for dirpath, _, filenames in os.walk(root_path):
            for fname in filenames:
                ext = fname.rsplit('.', 1)[-1].lower() if '.' in fname else ''
                if allowed_exts and ext not in allowed_exts:
                    continue
                rel_dir = os.path.relpath(dirpath, media_root)
                rel_path = os.path.join(rel_dir, fname) if rel_dir != '.' else fname
                # Skip if already migrated
                if ImageMigrationRecord.objects.filter(original_local_path=rel_path, status__in=['migrated','verified']).exists():
                    continue
                full_path = os.path.join(dirpath, fname)
                if limit and count >= limit:
                    break
                count += 1

                if dry_run:
                    self.stdout.write(f"DRY RUN: Would migrate {rel_path}")
                    self._ensure_record(rel_path)
                    continue
                try:
                    success, r2_url = self._migrate_local(full_path, rel_path, verify)
                    if success:
                        self.stdout.write(self.style.SUCCESS(f"Migrated: {rel_path} -> {r2_url}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"Failed to migrate {rel_path}"))
                except Exception as e:
                    logger.exception("Unexpected error during local migration")
                    rec = self._ensure_record(rel_path)
                    rec.status = 'failed'
                    rec.last_error = str(e)
                    rec.save()
            if limit and count >= limit:
                break

        self.stdout.write(self.style.SUCCESS(f"Processed {count} files."))

    def _ensure_record(self, rel_path):
        rec, _ = ImageMigrationRecord.objects.get_or_create(
            original_local_path=rel_path,
            original_firebase_url='',  # not used in local migration
            object_model='local-file',
            object_id=rel_path,
            field_name='local_media',
            defaults={'status': 'pending'}
        )
        return rec

    def _migrate_local(self, full_path, rel_path, verify):
        rec = self._ensure_record(rel_path)
        rec.attempts += 1
        try:
            with open(full_path, 'rb') as f:
                data = f.read()
            checksum = hashlib.sha256(data).hexdigest()
            rec.checksum = checksum
            rec.size_bytes = len(data)
            file_like = io.BytesIO(data)
            file_like.name = os.path.basename(rel_path)
            # Use same relative path folder root; R2 folder root could be 'media'
            folder, filename = os.path.split(rel_path)
            folder = folder.replace('\\', '/').strip('/') or 'media'
            success, msg, r2_url = r2_storage_service.upload_image(file_like, folder=folder, user_id=None)
            if not success:
                rec.status = 'failed'
                rec.last_error = msg
                rec.save()
                return False, None
            rec.r2_url = r2_url
            if verify:
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
