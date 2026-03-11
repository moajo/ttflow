"""ロック機構に関するテスト"""

import pytest

from ttflow import Client, RunContext
from ttflow.core.global_env import Global
from ttflow.errors import StateLockedError
from ttflow.state_repository.base import StateRepository
from ttflow.state_repository.buffer_cache_proxy import BufferCacheStateRepositoryProxy


class LockableMemoryRepository(StateRepository):
    """ロック機能付きのオンメモリリポジトリ（テスト用）"""

    def __init__(self):
        self.state = {}
        self._locked = False

    def save_state(self, name, value):
        self.state[name] = value

    def read_state(self, name, default=None):
        return self.state.get(name, default)

    def clear_state(self):
        self.state = {}

    def lock_state(self):
        self._locked = True

    def unlock_state(self):
        self._locked = False

    def is_locked(self):
        return self._locked


class TestLock:
    def _make_lockable_client(self):
        repo = LockableMemoryRepository()
        proxy = BufferCacheStateRepositoryProxy(repo)
        g = Global(state=proxy)
        return Client(g), repo

    def test_ロック中にrunするとエラー(self):
        client, repo = self._make_lockable_client()

        @client.workflow()
        def wf(c: RunContext, args: dict):
            pass

        repo._locked = True
        with pytest.raises(StateLockedError):
            client.run("wf")

    def test_run完了後にロックが解除される(self):
        client, repo = self._make_lockable_client()

        @client.workflow()
        def wf(c: RunContext, args: dict):
            pass

        client.run("wf")
        assert repo._locked is False

    def test_ワークフロー失敗時もロックが解除される(self):
        client, repo = self._make_lockable_client()

        @client.workflow()
        def wf(c: RunContext, args: dict):
            raise RuntimeError("boom")

        client.run("wf")
        assert repo._locked is False
