import json
from typing import Any

import boto3
from mypy_boto3_dynamodb.client import DynamoDBClient

from ..constants import STATE_KEY_SYSTEM_LOCK
from ..errors import StateLockedError
from .base import StateRepository


class DynamoDBStateRepository(StateRepository):
    """DynamoDBを使ったStateRepository

    テーブルスキーマ:
        pk (String, Partition Key): アイテムの一意キー
        value (String): JSON文字列

    stateアイテムのpkは "state:<name>" の形式。
    ロックアイテムのpkは "_system_lock"。
    """

    def __init__(self, table_name: str, region_name: str | None = None):
        self.table_name = table_name
        self._client: DynamoDBClient = boto3.client(
            "dynamodb", **({"region_name": region_name} if region_name else {})
        )

    def _state_key(self, name: str) -> str:
        return f"state:{name}"

    def save_state(self, name: str, value: Any) -> None:
        self._client.put_item(
            TableName=self.table_name,
            Item={
                "pk": {"S": self._state_key(name)},
                "value": {"S": json.dumps(value)},
            },
        )

    def read_state(self, name: str, default: Any = None) -> Any:
        response = self._client.get_item(
            TableName=self.table_name,
            Key={"pk": {"S": self._state_key(name)}},
        )
        if "Item" in response:
            return json.loads(response["Item"]["value"]["S"])
        return default

    def clear_state(self) -> None:
        paginator = self._client.get_paginator("scan")
        for page in paginator.paginate(
            TableName=self.table_name,
            ProjectionExpression="pk",
        ):
            for item in page.get("Items", []):
                self._client.delete_item(
                    TableName=self.table_name,
                    Key={"pk": item["pk"]},
                )

    def lock_state(self) -> None:
        """条件付き書き込みで排他ロックを取得する

        pkが存在しない場合のみ書き込みが成功する。
        既にロック済みの場合はStateLockedErrorを発生させる。
        """
        try:
            self._client.put_item(
                TableName=self.table_name,
                Item={
                    "pk": {"S": STATE_KEY_SYSTEM_LOCK},
                    "value": {"S": "locked"},
                },
                ConditionExpression="attribute_not_exists(pk)",
            )
        except self._client.exceptions.ConditionalCheckFailedException:
            raise StateLockedError("state is locked")

    def unlock_state(self) -> None:
        self._client.delete_item(
            TableName=self.table_name,
            Key={"pk": {"S": STATE_KEY_SYSTEM_LOCK}},
        )

    def is_locked(self) -> bool:
        response = self._client.get_item(
            TableName=self.table_name,
            Key={"pk": {"S": STATE_KEY_SYSTEM_LOCK}},
        )
        return "Item" in response
