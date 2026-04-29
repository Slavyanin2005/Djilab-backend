import os

from django.conf import settings
from django.utils.text import slugify
from minio import Minio
from minio.error import S3Error

minio_host = settings.MINIO_URL.replace("http://", "").replace("https://", "")

minio_client = Minio(
    minio_host,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,
)


def init_bucket():
    try:
        if not minio_client.bucket_exists(settings.MINIO_BUCKET):
            minio_client.make_bucket(settings.MINIO_BUCKET)
            print(f"Бакет {settings.MINIO_BUCKET} создан.")
        else:
            print(f"Бакет {settings.MINIO_BUCKET} уже существует.")
    except S3Error as e:
        print(f"Ошибка MinIO: {e}")


def generate_unique_filename(original_filename, service_name):
    safe_name = slugify(service_name)
    if not safe_name:
        safe_name = "file"

    _, ext = os.path.splitext(original_filename)
    import uuid

    unique_name = f"{safe_name}_{uuid.uuid4().hex}{ext}"
    return unique_name


def upload_to_minio(file_obj, object_name):
    try:
        minio_client.put_object(
            settings.MINIO_BUCKET,
            object_name,
            file_obj,
            length=file_obj.size,
            content_type=file_obj.content_type,
        )
        return object_name
    except S3Error as e:
        print(f"Ошибка загрузки: {e}")
        return None


def delete_from_minio(object_name):
    try:
        minio_client.remove_object(settings.MINIO_BUCKET, object_name)
        return True
    except S3Error as e:
        print(f"Ошибка удаления: {e}")
        return False
