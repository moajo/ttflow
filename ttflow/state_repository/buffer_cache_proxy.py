import json
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from .base import StateRepository


class BufferCacheStateRepositoryProxy(StateRepository):
    """SRに対する読み出しをキャッシュし、書き込みをバッファするプロキシ
    flush()するとバッファを書き込みます
    """

    def __init__(self, state_repository: StateRepository):
        self.state_repository = state_repository
        self.state: dict[str, Any] = {}
        self.enabled = False  # バッファモードが有効かどうか

    def save_state(self, name: str, value: Any) -> None:
        if self.enabled:
            self.state[name] = json.loads(json.dumps(value))
            return
        self.state_repository.save_state(name, value)

    def clear_state(self) -> None:
        self.state = {}
        self.state_repository.clear_state()

    def read_state(self, name: str, default: Any = None) -> Any:
        if self.enabled:
            if name not in self.state:
                self.state[name] = self.state_repository.read_state(
                    name, default=default
                )
            return json.loads(json.dumps(self.state[name]))
        return self.state_repository.read_state(name, default=default)

    def lock_state(self) -> None:
        self.state_repository.lock_state()

    def unlock_state(self) -> None:
        self.state = {}  # ロック解除したらキャッシュは信用できなくなる
        self.state_repository.unlock_state()

    def is_locked(self) -> bool:
        return self.state_repository.is_locked()

    def _flush(self) -> None:
        """書き込みをバッファしている場合、それをflushします"""
        if not self.enabled:
            return
        for name, value in self.state.items():
            self.state_repository.save_state(name, value)

    @contextmanager
    def buffering(self) -> Generator[None, None, None]:
        self.enabled = True
        try:
            yield
        finally:
            self._flush()
            self.enabled = False
