import json
from typing import Any

import boto3
import botostubs

from .base import StateRepository


class S3StateRepository(StateRepository):
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name

    def save_state(self, name: str, value):
        client: botostubs.S3 = boto3.client("s3", region_name="us-east-1")
        client.put_object(
            Bucket=self.bucket_name,
            Key=name,
            Body=json.dumps(value).encode("utf-8"),
        )

    def clear_state(self):
        s3 = boto3.resource("s3")
        bucket = s3.Bucket(self.bucket_name)
        bucket.objects.all().delete()

    def read_state(self, name: str, default=None) -> Any:
        client: botostubs.S3 = boto3.client("s3", region_name="us-east-1")
        try:
            response = client.get_object(
                Bucket=self.bucket_name,
                Key=name,
            )
            if "Body" not in response:
                return default
            body = response["Body"].read()
            return json.loads(body.decode("utf-8"))
        except client.exceptions.NoSuchKey:
            return default
