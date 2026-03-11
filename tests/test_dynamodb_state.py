"""DynamoDBStateRepositoryに関するテスト

実際のDynamoDBへの接続は行わず、スタブを使ってロジックをテストする。
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from ttflow.errors import StateLockedError
from ttflow.state_repository.dynamodb import DynamoDBStateRepository

# boto3.clientをモックしてDynamoDBStateRepositoryを生成するヘルパー
_PATCH_TARGET = "ttflow.state_repository.dynamodb.boto3.client"


def _make_repo():
    with patch(_PATCH_TARGET) as mock_client_fn:
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        # ConditionalCheckFailedExceptionをモック
        mock_client.exceptions.ConditionalCheckFailedException = type(
            "ConditionalCheckFailedException", (Exception,), {}
        )
        repo = DynamoDBStateRepository(table_name="test-table")
        return repo, mock_client


class TestDynamoDBStateRepository:
    """基本的なCRUD操作"""

    def test_save_stateでput_itemが呼ばれる(self):
        repo, mock_client = _make_repo()

        repo.save_state("my_key", {"hello": "world"})

        mock_client.put_item.assert_called_once()
        call_args = mock_client.put_item.call_args
        assert call_args.kwargs["TableName"] == "test-table"
        item = call_args.kwargs["Item"]
        assert item["pk"]["S"] == "state:my_key"
        assert json.loads(item["value"]["S"]) == {"hello": "world"}

    def test_read_stateでアイテムが存在する場合(self):
        repo, mock_client = _make_repo()
        mock_client.get_item.return_value = {
            "Item": {
                "pk": {"S": "state:my_key"},
                "value": {"S": json.dumps(42)},
            }
        }

        result = repo.read_state("my_key")
        assert result == 42

    def test_read_stateでアイテムが存在しない場合はデフォルト値(self):
        repo, mock_client = _make_repo()
        mock_client.get_item.return_value = {}

        result = repo.read_state("missing", default="default_val")
        assert result == "default_val"

    def test_clear_stateで全アイテムが削除される(self):
        repo, mock_client = _make_repo()
        mock_client.get_paginator.return_value.paginate.return_value = [
            {
                "Items": [
                    {"pk": {"S": "state:key1"}},
                    {"pk": {"S": "state:key2"}},
                ],
            }
        ]

        repo.clear_state()

        assert mock_client.delete_item.call_count == 2


class TestDynamoDBLock:
    """条件付き書き込みによるロック機構"""

    def test_lock_stateで条件付き書き込みが行われる(self):
        repo, mock_client = _make_repo()

        repo.lock_state()

        mock_client.put_item.assert_called_once()
        call_args = mock_client.put_item.call_args
        assert call_args.kwargs["Item"]["pk"]["S"] == "_system_lock"
        assert "ConditionExpression" in call_args.kwargs

    def test_lock_state中に再度lockするとStateLockedError(self):
        repo, mock_client = _make_repo()
        mock_client.put_item.side_effect = (
            mock_client.exceptions.ConditionalCheckFailedException("already locked")
        )

        with pytest.raises(StateLockedError):
            repo.lock_state()

    def test_unlock_stateでロックアイテムが削除される(self):
        repo, mock_client = _make_repo()

        repo.unlock_state()

        mock_client.delete_item.assert_called_once()
        call_args = mock_client.delete_item.call_args
        assert call_args.kwargs["Key"]["pk"]["S"] == "_system_lock"

    def test_is_lockedでロックアイテムが存在する場合True(self):
        repo, mock_client = _make_repo()
        mock_client.get_item.return_value = {"Item": {"pk": {"S": "_system_lock"}}}

        assert repo.is_locked() is True

    def test_is_lockedでロックアイテムが存在しない場合False(self):
        repo, mock_client = _make_repo()
        mock_client.get_item.return_value = {}

        assert repo.is_locked() is False


class TestDynamoDBIntegration:
    """DynamoDBバックエンドでのワークフロー実行テスト（スタブ使用）"""

    def test_ワークフローが正常に実行できる(self):
        from ttflow import RunContext
        from ttflow.core.global_env import Global
        from ttflow.state_repository.buffer_cache_proxy import (
            BufferCacheStateRepositoryProxy,
        )
        from ttflow.ttflow import Client

        repo, mock_dynamo = _make_repo()
        proxy = BufferCacheStateRepositoryProxy(repo)
        g = Global(state=proxy)
        client = Client(g)

        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.log("hello from dynamodb")

        results = client.run("wf")
        assert results[0].status == "succeeded"
        assert results[0].logs == ["hello from dynamodb"]
        # save_stateが呼ばれている（状態の永続化）
        assert mock_dynamo.put_item.call_count > 0
