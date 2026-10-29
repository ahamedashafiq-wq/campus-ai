from functools import lru_cache

from app.config import get_settings
from app.storage.base import StorageBackend
from app.storage.local import LocalStorage


@lru_cache
def get_storage() -> StorageBackend:
    settings = get_settings()
    if settings.storage_backend == "s3":
        from app.storage.s3 import S3Storage

        return S3Storage(
            bucket=settings.s3_bucket,
            region=settings.s3_region,
            access_key=settings.s3_access_key_id,
            secret_key=settings.s3_secret_access_key,
            endpoint_url=settings.s3_endpoint_url or None,
        )
    return LocalStorage(settings.local_storage_path)
