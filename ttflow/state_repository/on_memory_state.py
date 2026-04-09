import json
from typing import Any

from .base import StateRepository


class OnMemoryStateRepository(StateRepository):
    def __init__(self):
        self.state: dict[str, Any] = {}

    def save_state(self, name: str, value: Any) -> None:
        self.state[name] = json.loads(json.dumps(value))

    def delete_state(self, name: str) -> None:
        self.state.pop(name, None)

    def clear_state(self) -> None:
        self.state = {}

    def read_state(self, name: str, default: Any = None) -> Any:
        value = self.state.get(name, default)
        return json.loads(json.dumps(value))

    def lock_state(self) -> None:
        pass

    def unlock_state(self) -> None:
        pass

    def is_locked(self) -> bool:
        return False
