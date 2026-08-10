import io
import uuid
from datetime import timedelta

from django.conf import settings
from minio import Minio
from minio.sse import SseS3


def _client_kwargs() -> dict:
    return {
        "access_key": settings.MINIO_ACCESS_KEY,
        "secret_key": settings.MINIO_SECRET_KEY,
        "secure": settings.MINIO_USE_HTTPS,
    }


def _client() -> Minio:
    return Minio(settings.MINIO_ENDPOINT, **_client_kwargs())


def _public_client() -> Minio:
    # Region set explicitly so the SDK skips the bucket-region network lookup,
    # which would fail if MINIO_PUBLIC_ENDPOINT is unreachable from the server.
    return Minio(settings.MINIO_PUBLIC_ENDPOINT, **_client_kwargs(), region="us-east-1")


def _ensure_bucket(client: Minio, bucket: str) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


def upload_document(file_bytes: bytes, original_name: str, content_type: str) -> str:
    """Upload file to MinIO and return the object key."""
    client = _client()
    bucket = settings.MINIO_BUCKET_NAME
    _ensure_bucket(client, bucket)

    ext = original_name.rsplit(".", 1)[-1] if "." in original_name else "bin"
    key = f"complementary/{uuid.uuid4().hex}.{ext}"

    client.put_object(
        bucket,
        key,
        io.BytesIO(file_bytes),
        length=len(file_bytes),
        content_type=content_type,
        sse=SseS3(),
    )
    return key


def get_presigned_url(key: str, expires_seconds: int = 3600) -> str:
    return _public_client().presigned_get_object(
        settings.MINIO_BUCKET_NAME, key, expires=timedelta(seconds=expires_seconds)
    )


def delete_document(key: str) -> None:
    """Supprime un objet du bucket MinIO (silencieux si inexistant)."""
    if not key:
        return
    try:
        _client().remove_object(settings.MINIO_BUCKET_NAME, key)
    except Exception:
        pass
