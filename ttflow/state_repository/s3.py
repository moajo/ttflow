import json
from typing import Any

import boto3
from mypy_boto3_s3.client import S3Client

from ..constants import STATE_KEY_SYSTEM_LOCK
from .base import StateRepository


class S3StateRepository(StateRepository):
    def __init__(self, bucket_name: str, prefix: str):
        self.bucket_name = bucket_name
        self.prefix = prefix
        self._client: S3Client = boto3.client("s3")

    def save_state(self, name: str, value):
        self._client.put_object(
            Bucket=self.bucket_name,
            Key=f"{self.prefix}/{name}",
            Body=json.dumps(value).encode("utf-8"),
        )

    def clear_state(self):
        s3 = boto3.resource("s3")
        bucket = s3.Bucket(self.bucket_name)
        bucket.objects.filter(Prefix=f"{self.prefix}/").delete()

    def read_state(self, name: str, default=None) -> Any:
        try:
            response = self._client.get_object(
                Bucket=self.bucket_name,
                Key=f"{self.prefix}/{name}",
            )
            if "Body" not in response:
                return default
            body = response["Body"].read()
            return json.loads(body.decode("utf-8"))
        except self._client.exceptions.NoSuchKey:
            return default

    def lock_state(self):
        self.save_state(STATE_KEY_SYSTEM_LOCK, "locked")

    def unlock_state(self):
        self._client.delete_object(
            Bucket=self.bucket_name,
            Key=f"{self.prefix}/_system_lock",
        )

    def is_locked(self) -> bool:
        return self.read_state(STATE_KEY_SYSTEM_LOCK, default=None) is not None
