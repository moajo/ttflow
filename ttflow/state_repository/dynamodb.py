import json
from typing import Any

import boto3
import botostubs

from .base import StateRepository


class DynamoDBStateRepository(StateRepository):
    def __init__(self, table_name: str):
        self.table_name = table_name

    def save_state(self, name: str, value):
        client: botostubs.DynamoDB = boto3.client("dynamodb", region_name="us-east-1")
        client.put_item(
            TableName=self.table_name,
            Item={
                "key": {"S": name},
                "range": {"S": "none"},
                "value": {"S": json.dumps(value)},
            },
        )

    def clear_state(self):
        pass  # TODO: implement

    def read_state(self, name: str, default=None) -> Any:
        client: botostubs.DynamoDB = boto3.client("dynamodb", region_name="us-east-1")
        response = client.get_item(
            TableName=self.table_name,
            Key={
                "key": {"S": name},
                "range": {"S": "none"},
            },
        )
        if "Item" in response:
            return json.loads(response["Item"]["value"]["S"])
        else:
            return default
