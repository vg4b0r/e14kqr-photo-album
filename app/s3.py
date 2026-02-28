import os
import boto3
from botocore.client import Config

def s3_client():
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "eu-north-1"
    return boto3.client(
        "s3",
        region_name=region,
        config=Config(signature_version="s3v4")
    )

def upload_fileobj(fileobj, bucket: str, key: str, content_type: str):
    s3 = s3_client()
    s3.upload_fileobj(
        Fileobj=fileobj,
        Bucket=bucket,
        Key=key,
        ExtraArgs={"ContentType": content_type}
    )

def delete_object(bucket: str, key: str):
    s3 = s3_client()
    s3.delete_object(Bucket=bucket, Key=key)

def presigned_get_url(bucket: str, key: str, expires_sec: int = 3600) -> str:
    s3 = s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_sec
    )