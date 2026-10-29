from app.storage.base import StorageBackend


class S3Storage(StorageBackend):
    """S3-compatible object storage. Requires boto3 and credentials at runtime."""

    def __init__(
        self,
        bucket: str,
        region: str,
        access_key: str,
        secret_key: str,
        endpoint_url: str | None = None,
    ) -> None:
        if not bucket or not access_key or not secret_key:
            raise RuntimeError("S3 storage is selected but credentials are missing")
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("boto3 is required for S3 storage") from exc
        self.bucket = bucket
        kwargs = {"region_name": region, "aws_access_key_id": access_key, "aws_secret_access_key": secret_key}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self.client = boto3.client("s3", **kwargs)

    def save(self, key: str, data: bytes, content_type: str) -> str:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return key

    def load(self, key: str) -> bytes:
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read()

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def health(self) -> dict:
        return {"backend": "s3", "configured": True, "bucket": self.bucket}
