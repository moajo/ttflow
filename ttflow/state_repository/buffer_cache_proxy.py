import json
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from .base import StateRepository


# バッファ内で削除を表すトゥームストーン
class _Deleted:
    """delete_state されたキーをバッファ内で表すための型。シングルトン `_DELETED` のみ使う"""

    _instance: "_Deleted | None" = None

    def __new__(cls) -> "_Deleted":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


_DELETED = _Deleted()

# cache / writes に格納される値の型: 通常のJSON値、または削除トゥームストーン
_BufferedValue = Any  # JSON値 | _Deleted


class BufferCacheStateRepositoryProxy(StateRepository):
    """SRに対する読み出しをキャッシュし、書き込みをバッファするプロキシ。

    - read_state の結果は cache に入れて、同じキーへの再readを高速化する
    - save_state / delete_state は writes に積み、_flush() で本物のリポジトリに反映する
    - read のみ行ったキー（writes に入っていないキー）は flush 時に書き戻されない
    """

    def __init__(self, state_repository: StateRepository):
        self.state_repository = state_repository
        # read結果のキャッシュ。flush対象ではない。値は通常のJSON値、または削除トゥームストーン `_DELETED`
        self.cache: dict[str, _BufferedValue] = {}
        # 書き込みバッファ。flush時にこちらだけが反映される。値は通常のJSON値、または `_DELETED`
        self.writes: dict[str, _BufferedValue] = {}
        self.enabled = False  # バッファモードが有効かどうか

    def save_state(self, name: str, value: Any) -> None:
        if self.enabled:
            # writes と cache は独立したcopyにする（片方をmutateしてももう片方に影響しないように）
            self.writes[name] = json.loads(json.dumps(value))
            self.cache[name] = json.loads(json.dumps(value))
            return
        self.state_repository.save_state(name, value)

    def delete_state(self, name: str) -> None:
        if self.enabled:
            self.writes[name] = _DELETED
            self.cache[name] = _DELETED
            return
        self.state_repository.delete_state(name)

    def clear_state(self) -> None:
        self.cache = {}
        self.writes = {}
        self.state_repository.clear_state()

    def read_state(self, name: str, default: Any = None) -> Any:
        if self.enabled:
            if name in self.cache:
                cached = self.cache[name]
                if cached is _DELETED:
                    return default
                return json.loads(json.dumps(cached))
            v = self.state_repository.read_state(name, default=default)
            # mutationでキャッシュが汚れないよう、キャッシュにも返り値にも独立したcopyを渡す
            self.cache[name] = json.loads(json.dumps(v))
            return json.loads(json.dumps(v))
        return self.state_repository.read_state(name, default=default)

    def lock_state(self) -> None:
        self.state_repository.lock_state()

    def unlock_state(self) -> None:
        # ロック解除したらキャッシュは信用できなくなる
        self.cache = {}
        self.writes = {}
        self.state_repository.unlock_state()

    def is_locked(self) -> bool:
        return self.state_repository.is_locked()

    def _flush(self) -> None:
        """バッファされている書き込みを本物のリポジトリに反映する"""
        if not self.enabled:
            return
        for name, value in self.writes.items():
            if value is _DELETED:
                self.state_repository.delete_state(name)
            else:
                self.state_repository.save_state(name, value)
        self.writes = {}

    @contextmanager
    def buffering(self) -> Generator[None, None, None]:
        self.enabled = True
        try:
            yield
        finally:
            self._flush()
            self.enabled = False
