"""setup関数とStateRepositoryに関するテスト"""

import pytest

from ttflow import setup
from ttflow.errors import UnknownRepositoryError
from ttflow.state_repository.buffer_cache_proxy import BufferCacheStateRepositoryProxy
from ttflow.state_repository.on_memory_state import OnMemoryStateRepository


class TestSetup:
    """setup()のリポジトリ指定"""

    def test_onmemory(self):
        client = setup(state_repository="onmemory")
        assert client is not None
        assert isinstance(client._global.state, BufferCacheStateRepositoryProxy)

    def test_local_file(self, tmp_path):
        path = tmp_path / "state.json"
        client = setup(state_repository=f"local:{path}")
        assert client is not None

    def test_不明なリポジトリでエラー(self):
        with pytest.raises(UnknownRepositoryError):
            setup(state_repository="unknown:something")


class TestOnMemoryStateRepository:
    """OnMemoryStateRepositoryの基本動作"""

    def test_save_and_read(self):
        repo = OnMemoryStateRepository()
        repo.save_state("key", {"nested": [1, 2, 3]})
        assert repo.read_state("key") == {"nested": [1, 2, 3]}

    def test_readのデフォルト値(self):
        repo = OnMemoryStateRepository()
        assert repo.read_state("nonexistent") is None
        assert repo.read_state("nonexistent", "default") == "default"

    def test_clear_state(self):
        repo = OnMemoryStateRepository()
        repo.save_state("key", "value")
        repo.clear_state()
        assert repo.read_state("key") is None

    def test_deep_copy_on_save(self):
        """保存時にディープコピーされる（ミュータブルオブジェクトの参照共有を防ぐ）"""
        repo = OnMemoryStateRepository()
        data = {"list": [1, 2]}
        repo.save_state("key", data)
        data["list"].append(3)  # 元のオブジェクトを変更
        assert repo.read_state("key") == {"list": [1, 2]}  # 影響なし

    def test_deep_copy_on_read(self):
        """読み出し時にディープコピーされる"""
        repo = OnMemoryStateRepository()
        repo.save_state("key", {"list": [1, 2]})
        data = repo.read_state("key")
        data["list"].append(3)  # 読み出した値を変更
        assert repo.read_state("key") == {"list": [1, 2]}  # 影響なし

    def test_lock_is_noop(self):
        repo = OnMemoryStateRepository()
        assert repo.is_locked() is False
        repo.lock_state()
        assert repo.is_locked() is False  # OnMemoryはロック非対応
        repo.unlock_state()


class TestBufferCacheProxy:
    """BufferCacheStateRepositoryProxyの動作"""

    def _make_proxy(self):
        inner = OnMemoryStateRepository()
        proxy = BufferCacheStateRepositoryProxy(inner)
        return proxy, inner

    def test_バッファモード外では直接書き込み(self):
        proxy, inner = self._make_proxy()
        proxy.save_state("key", "value")
        assert inner.read_state("key") == "value"

    def test_バッファモード内では書き込みがバッファされる(self):
        proxy, inner = self._make_proxy()
        with proxy.buffering():
            proxy.save_state("key", "value")
            # バッファ中は内部リポジトリに書き込まれない
            assert inner.read_state("key") is None
            # プロキシからは読める
            assert proxy.read_state("key") == "value"
        # buffering終了でflushされる
        assert inner.read_state("key") == "value"

    def test_バッファモード内の読み取りキャッシュ(self):
        proxy, inner = self._make_proxy()
        inner.save_state("key", "original")
        with proxy.buffering():
            # 初回読み取りでキャッシュ
            assert proxy.read_state("key") == "original"
            # 内部リポジトリを直接変更しても
            inner.save_state("key", "modified")
            # キャッシュが返る
            assert proxy.read_state("key") == "original"

    def test_unlock時にキャッシュがクリアされる(self):
        proxy, inner = self._make_proxy()
        with proxy.buffering():
            proxy.save_state("key", "cached")
        proxy.unlock_state()
        # unlockでキャッシュがクリアされるので、次回読み取りは内部リポジトリから
        # ただしバッファモード外なので直接読み取り
        assert proxy.read_state("key") == "cached"  # flushされているので読める

    def test_clear_stateはキャッシュも内部も消す(self):
        proxy, inner = self._make_proxy()
        inner.save_state("key", "value")
        proxy.clear_state()
        assert inner.read_state("key") is None

    def test_バッファモード内のdeep_copy(self):
        """バッファモード内でもディープコピーが行われる"""
        proxy, _ = self._make_proxy()
        with proxy.buffering():
            proxy.save_state("key", {"list": [1, 2]})
            data = proxy.read_state("key")
            data["list"].append(3)
            assert proxy.read_state("key") == {"list": [1, 2]}


class TestLocalFileStateRepository:
    """LocalFileStateRepositoryの基本動作"""

    def test_ファイルが存在しない場合デフォルト値(self, tmp_path):
        from ttflow.state_repository.local_file_state import LocalFileStateRepository

        repo = LocalFileStateRepository(state_file=tmp_path / "state.json")
        assert repo.read_state("key") is None
        assert repo.read_state("key", "default") == "default"

    def test_save_and_read(self, tmp_path):
        from ttflow.state_repository.local_file_state import LocalFileStateRepository

        repo = LocalFileStateRepository(state_file=tmp_path / "state.json")
        repo.save_state("key", {"data": [1, 2, 3]})
        assert repo.read_state("key") == {"data": [1, 2, 3]}

    def test_ディレクトリが自動生成される(self, tmp_path):
        from ttflow.state_repository.local_file_state import LocalFileStateRepository

        repo = LocalFileStateRepository(
            state_file=tmp_path / "nested" / "dir" / "state.json"
        )
        repo.save_state("key", "value")
        assert repo.read_state("key") == "value"

    def test_clear_state(self, tmp_path):
        from ttflow.state_repository.local_file_state import LocalFileStateRepository

        repo = LocalFileStateRepository(state_file=tmp_path / "state.json")
        repo.save_state("key", "value")
        repo.clear_state()
        assert repo.read_state("key") is None

    def test_複数キーの永続化(self, tmp_path):
        from ttflow.state_repository.local_file_state import LocalFileStateRepository

        repo = LocalFileStateRepository(state_file=tmp_path / "state.json")
        repo.save_state("key1", "val1")
        repo.save_state("key2", "val2")
        assert repo.read_state("key1") == "val1"
        assert repo.read_state("key2") == "val2"
