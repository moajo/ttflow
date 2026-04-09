"""ロック機構に関するテスト"""

import threading
import time

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

    def delete_state(self, name):
        self.state.pop(name, None)

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


class TestLockContention:
    """ロック競合に関するテスト"""

    def _make_lockable_client(self):
        repo = LockableMemoryRepository()
        proxy = BufferCacheStateRepositoryProxy(repo)
        g = Global(state=proxy)
        return Client(g), repo

    def test_ワークフロー実行中に別スレッドからrunすると競合エラー(self):
        """ワークフロー実行中に並行してrun()を呼ぶとStateLockedErrorが発生する"""
        client, repo = self._make_lockable_client()
        barrier = threading.Barrier(2, timeout=5)
        contention_error = []

        @client.workflow()
        def slow_wf(c: RunContext, args: dict):
            # 別スレッドの準備を待つ
            barrier.wait()
            time.sleep(0.1)

        def concurrent_run():
            try:
                # メインスレッドのワークフローがロックを取得するのを待つ
                barrier.wait()
                client.run("slow_wf")
            except StateLockedError:
                contention_error.append(True)

        thread = threading.Thread(target=concurrent_run)
        thread.start()
        client.run("slow_wf")
        thread.join(timeout=5)

        assert len(contention_error) == 1, "並行runでStateLockedErrorが発生するべき"

    def test_競合エラー後もロック状態は正常に復帰する(self):
        """競合でStateLockedErrorが発生した後、元のrunが完了すればロックは解放される"""
        client, repo = self._make_lockable_client()
        barrier = threading.Barrier(2, timeout=5)

        @client.workflow()
        def wf(c: RunContext, args: dict):
            barrier.wait()
            time.sleep(0.1)

        def concurrent_run():
            barrier.wait()
            try:
                client.run("wf")
            except StateLockedError:
                pass

        thread = threading.Thread(target=concurrent_run)
        thread.start()
        client.run("wf")
        thread.join(timeout=5)

        # 元のrun完了後、ロックは解放されている
        assert repo._locked is False

    def test_競合後に再度runが成功する(self):
        """ロック競合が発生した後でも、ロック解放後は再度run()が成功する"""
        client, repo = self._make_lockable_client()
        execution_count = []

        @client.workflow()
        def wf(c: RunContext, args: dict):
            execution_count.append(1)

        # 最初のrun
        client.run("wf")
        count_after_first = len(execution_count)
        assert count_after_first >= 1

        # ロック済み状態をシミュレート→競合エラー
        repo._locked = True
        with pytest.raises(StateLockedError):
            client.run("wf")
        # 競合エラー時は実行されない
        assert len(execution_count) == count_after_first

        # ロック解放後に再度run→成功
        repo._locked = False
        client.run("wf")
        assert len(execution_count) > count_after_first

    def test_複数回の順次実行でロックが正しく管理される(self):
        """連続してrun()を呼んでも毎回ロック取得→解放が正しく行われる"""
        client, repo = self._make_lockable_client()
        execution_count = []

        @client.workflow()
        def wf(c: RunContext, args: dict):
            # ワークフロー実行中はロックされている
            assert repo._locked is True
            execution_count.append(1)

        for _ in range(5):
            assert repo._locked is False
            client.run("wf")
            assert repo._locked is False

        assert len(execution_count) == 5

    def test_ワークフロー内からのロック状態確認(self):
        """ワークフロー実行中にis_locked()がTrueを返すことを確認"""
        client, repo = self._make_lockable_client()
        lock_states = []

        @client.workflow()
        def wf(c: RunContext, args: dict):
            lock_states.append(repo.is_locked())

        lock_states.append(repo.is_locked())  # 実行前: False
        client.run("wf")
        lock_states.append(repo.is_locked())  # 実行後: False

        assert lock_states == [False, True, False]
