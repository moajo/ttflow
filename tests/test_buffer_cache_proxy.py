from ttflow.state_repository.buffer_cache_proxy import BufferCacheStateRepositoryProxy
from ttflow.state_repository.on_memory_state import OnMemoryStateRepository


def test_読み取りのみのキーはflushで書き戻されない():
    """default値だけ取得したキーがS3に空オブジェクトとしてPUTされるバグの回帰テスト"""
    backend = OnMemoryStateRepository()
    proxy = BufferCacheStateRepositoryProxy(backend)
    with proxy.buffering():
        assert proxy.read_state("missing", default=[]) == []
        assert proxy.read_state("missing2", default={"a": 1}) == {"a": 1}
    assert "missing" not in backend.state
    assert "missing2" not in backend.state


def test_save_stateはflushで反映される():
    backend = OnMemoryStateRepository()
    proxy = BufferCacheStateRepositoryProxy(backend)
    with proxy.buffering():
        proxy.save_state("k", [1, 2, 3])
    assert backend.state["k"] == [1, 2, 3]


def test_delete_stateはflushで反映される():
    backend = OnMemoryStateRepository()
    backend.save_state("k", [1, 2, 3])
    proxy = BufferCacheStateRepositoryProxy(backend)
    with proxy.buffering():
        proxy.delete_state("k")
        assert proxy.read_state("k", default=None) is None
    assert "k" not in backend.state


def test_バッファ中のreadは最新の書き込みを返す():
    backend = OnMemoryStateRepository()
    backend.save_state("k", "old")
    proxy = BufferCacheStateRepositoryProxy(backend)
    with proxy.buffering():
        assert proxy.read_state("k") == "old"
        proxy.save_state("k", "new")
        assert proxy.read_state("k") == "new"
        proxy.delete_state("k")
        assert proxy.read_state("k", default="default") == "default"


def test_読み取った値のmutationがキャッシュを汚染しない():
    """list/dict を read で取得→mutate しても、後続の read やバックエンドに影響しないこと"""
    backend = OnMemoryStateRepository()
    backend.save_state("k", [1, 2, 3])
    proxy = BufferCacheStateRepositoryProxy(backend)
    with proxy.buffering():
        v = proxy.read_state("k")
        v.append(999)
        # キャッシュは汚染されていない
        assert proxy.read_state("k") == [1, 2, 3]
    # バックエンドにも書き戻されていない
    assert backend.state["k"] == [1, 2, 3]


def test_save_stateで渡した値の後続mutationがバッファを汚染しない():
    backend = OnMemoryStateRepository()
    proxy = BufferCacheStateRepositoryProxy(backend)
    with proxy.buffering():
        v = [1, 2, 3]
        proxy.save_state("k", v)
        v.append(999)  # save後にmutate
    assert backend.state["k"] == [1, 2, 3]
