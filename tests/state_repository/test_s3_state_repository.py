"""motoを使ったS3StateRepositoryのユニットテスト（AWSアクセス不要）"""

import boto3
import pytest
from moto import mock_aws

from ttflow.state_repository.s3 import S3StateRepository

BUCKET_NAME = "test-bucket"
PREFIX = "test-prefix"


@pytest.fixture()
def s3_repo():
    """モックS3環境でS3StateRepositoryを作成するfixture"""
    with mock_aws():
        # テスト用バケットを作成
        conn = boto3.client("s3", region_name="us-east-1")
        conn.create_bucket(Bucket=BUCKET_NAME)

        repo = S3StateRepository(BUCKET_NAME, prefix=PREFIX)
        yield repo


class TestS3StateRepository:
    def test_save_and_read_state(self, s3_repo):
        """状態の保存と読み取り"""
        s3_repo.save_state("key1", {"a": 1, "b": "hello"})
        result = s3_repo.read_state("key1")
        assert result == {"a": 1, "b": "hello"}

    def test_read_state_not_found_returns_default(self, s3_repo):
        """存在しないキーはデフォルト値を返す"""
        result = s3_repo.read_state("nonexistent")
        assert result is None

        result = s3_repo.read_state("nonexistent", default="fallback")
        assert result == "fallback"

    def test_save_and_read_japanese_key(self, s3_repo):
        """日本語キーでの保存と読み取り"""
        s3_repo.save_state("ほげ", {"a": 6})
        result = s3_repo.read_state("ほげ")
        assert result == {"a": 6}

    def test_save_overwrites_existing(self, s3_repo):
        """同じキーへの保存は上書きされる"""
        s3_repo.save_state("key1", "first")
        s3_repo.save_state("key1", "second")
        assert s3_repo.read_state("key1") == "second"

    def test_save_various_types(self, s3_repo):
        """様々な型の値を保存・読み取りできる"""
        s3_repo.save_state("str_val", "hello")
        assert s3_repo.read_state("str_val") == "hello"

        s3_repo.save_state("int_val", 42)
        assert s3_repo.read_state("int_val") == 42

        s3_repo.save_state("list_val", [1, 2, 3])
        assert s3_repo.read_state("list_val") == [1, 2, 3]

        s3_repo.save_state("null_val", None)
        assert s3_repo.read_state("null_val") is None

    def test_clear_state(self, s3_repo):
        """clear_stateで全状態が削除される"""
        s3_repo.save_state("key1", "value1")
        s3_repo.save_state("key2", "value2")
        s3_repo.clear_state()

        assert s3_repo.read_state("key1") is None
        assert s3_repo.read_state("key2") is None

    def test_lock_unlock_cycle(self, s3_repo):
        """ロック・アンロックのサイクル"""
        assert not s3_repo.is_locked()

        s3_repo.lock_state()
        assert s3_repo.is_locked()

        s3_repo.unlock_state()
        assert not s3_repo.is_locked()

    def test_unlock_when_not_locked(self, s3_repo):
        """ロックされていない状態でunlockしてもエラーにならない"""
        s3_repo.unlock_state()
        assert not s3_repo.is_locked()

    def test_multiple_lock_calls(self, s3_repo):
        """複数回lockしても正常に動作する"""
        s3_repo.lock_state()
        s3_repo.lock_state()
        assert s3_repo.is_locked()

        s3_repo.unlock_state()
        assert not s3_repo.is_locked()
