import os
import uuid
from datetime import datetime
from typing import Optional, Tuple, Any, Dict, List
import logging

import boto3
from botocore.client import Config
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

logger = logging.getLogger(__name__)

class R2StorageService:
    """Cloudflare R2 storage service mirroring FirebaseStorageService interface."""

    def __init__(self):
        self._client = None
        self._bucket = getattr(settings, 'CLOUDFLARE_R2_BUCKET', None)
        self._public_base = getattr(settings, 'R2_PUBLIC_BASE_URL', '').rstrip('/')
        self._endpoint_url = f"https://{getattr(settings, 'CLOUDFLARE_ACCOUNT_ID', '')}.r2.cloudflarestorage.com" if getattr(settings, 'CLOUDFLARE_ACCOUNT_ID', '') else None
        self._initialize()

    def _initialize(self):
        if not self._bucket:
            logger.warning("R2 bucket not configured; uploads will fail until CLOUDFLARE_R2_BUCKET is set.")
        try:
            access_key = getattr(settings, 'CLOUDFLARE_R2_ACCESS_KEY_ID', None)
            secret_key = getattr(settings, 'CLOUDFLARE_R2_SECRET_ACCESS_KEY', None)
            if not (access_key and secret_key):
                logger.warning("R2 credentials missing; ensure CLOUDFLARE_R2_ACCESS_KEY_ID and CLOUDFLARE_R2_SECRET_ACCESS_KEY are set.")
                return
            # S3 compatible client
            # Cloudflare R2 uses 'auto' region internally; omit region_name to avoid lint warning.
            self._client = boto3.client(
                's3',
                endpoint_url=self._endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=Config(signature_version='s3v4')
            )
        except Exception as e:
            logger.error(f"Failed to initialize R2 client: {e}")

    @property
    def client(self):
        return self._client

    def upload_image(self, image_file: Any, folder: str = "material_images", user_id: Optional[int] = None) -> Tuple[bool, str, Optional[str]]:
        if not self.client or not self._bucket:
            return False, "R2 not configured", None
        try:
            filename = self._generate_filename(getattr(image_file, 'name', 'image.jpg'), user_id)
            if user_id:
                key = f"{folder}/user_{user_id}/{filename}"
            else:
                key = f"{folder}/{filename}"

            # Reset pointer
            if hasattr(image_file, 'seek'):
                image_file.seek(0)

            # Read bytes
            if isinstance(image_file, (InMemoryUploadedFile, TemporaryUploadedFile)):
                body = image_file.read()
                content_type = image_file.content_type
            else:
                body = image_file.read()
                content_type = None

            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            # Public read (optional) - R2 handles access policies; omit ACL if using bucket-wide public policy
            # extra_args['ACL'] = 'public-read'

            self.client.put_object(Bucket=self._bucket, Key=key, Body=body, **extra_args)

            public_url = self._build_public_url(key)
            logger.info(f"Uploaded image to R2: {key}")
            return True, "Image uploaded successfully", public_url
        except Exception as e:
            logger.error(f"Failed to upload image to R2: {e}")
            return False, f"Upload failed: {e}", None

    def delete_image(self, image_url: str) -> Tuple[bool, str]:
        key = self._extract_key(image_url)
        if not key:
            return False, "Invalid R2 image URL"
        try:
            self.client.delete_object(Bucket=self._bucket, Key=key)
            logger.info(f"Deleted image from R2: {key}")
            return True, "Image deleted successfully"
        except Exception as e:
            logger.error(f"Failed to delete image from R2: {e}")
            return False, f"Delete failed: {e}"

    def get_image_metadata(self, image_url: str) -> Optional[Dict[str, Any]]:
        key = self._extract_key(image_url)
        if not key:
            return None
        try:
            head = self.client.head_object(Bucket=self._bucket, Key=key)
            return {
                'name': key,
                'size': head.get('ContentLength'),
                'content_type': head.get('ContentType'),
                'etag': head.get('ETag'),
                'last_modified': head.get('LastModified'),
                'public_url': self._build_public_url(key)
            }
        except Exception as e:
            logger.error(f"Failed to get R2 image metadata: {e}")
            return None

    def update_image(self, old_image_url: str, new_image_file: Any, folder: str = "material_images", user_id: Optional[int] = None) -> Tuple[bool, str, Optional[str]]:
        success, message, new_url = self.upload_image(new_image_file, folder, user_id)
        if not success:
            return False, f"Failed to upload new image: {message}", None
        if old_image_url:
            self.delete_image(old_image_url)  # Ignore errors
        return True, "Image updated successfully", new_url

    def list_user_images(self, user_id: int, folder: str = "material_images") -> List[Dict[str, Any]]:
        prefix = f"{folder}/user_{user_id}/"
        images: List[Dict[str, Any]] = []
        try:
            paginator = self.client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
                for obj in page.get('Contents', []):
                    images.append({
                        'name': obj['Key'],
                        'size': obj['Size'],
                        'public_url': self._build_public_url(obj['Key']),
                        'last_modified': obj['LastModified']
                    })
            return images
        except Exception as e:
            logger.error(f"Failed to list R2 images: {e}")
            return []

    def get_storage_stats(self) -> Dict[str, Any]:
        # R2 does not offer direct bucket size; we approximate by listing (costly for large buckets)
        try:
            paginator = self.client.get_paginator('list_objects_v2')
            total_size = 0
            total_files = 0
            for page in paginator.paginate(Bucket=self._bucket):
                for obj in page.get('Contents', []):
                    total_files += 1
                    total_size += obj['Size']
            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.error(f"Failed to get R2 storage stats: {e}")
            return {}

    def _generate_filename(self, original_filename: str, user_id: Optional[int]) -> str:
        name, ext = os.path.splitext(original_filename or 'image.jpg')
        if not ext:
            ext = '.jpg'
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if user_id:
            filename = f"{name}_{user_id}_{timestamp}_{unique_id}{ext}"
        else:
            filename = f"{name}_{timestamp}_{unique_id}{ext}"
        filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
        return filename

    def _build_public_url(self, key: str) -> str:
        if self._public_base:
            return f"{self._public_base}/{key}"
        # Fallback to R2 direct URL pattern (not cached) - encourage setting public base
        return f"{self._endpoint_url}/{self._bucket}/{key}" if self._endpoint_url else key

    def _extract_key(self, image_url: str) -> Optional[str]:
        if not image_url:
            return None
        # If URL starts with public base
        if self._public_base and image_url.startswith(self._public_base):
            return image_url[len(self._public_base)+1:]
        # If direct endpoint style
        if self._endpoint_url and self._bucket and self._endpoint_url in image_url and f"/{self._bucket}/" in image_url:
            parts = image_url.split(f"/{self._bucket}/", 1)
            if len(parts) == 2:
                return parts[1]
        # If it's already a key (no http)
        if not image_url.startswith('http'):
            return image_url
        return None

# Singleton
r2_storage_service = R2StorageService()
