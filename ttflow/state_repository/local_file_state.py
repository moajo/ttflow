import json
from pathlib import Path
from typing import Any

from .base import StateRepository


class LocalFileStateRepository(StateRepository):
    def __init__(self, state_file: Path = Path("state.json")):
        self.state_file = state_file

    def save_state(self, name: str, value):
        state = {}
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                state = json.load(f)
        state[name] = value
        with open(self.state_file, "w") as f:
            json.dump(state, f, sort_keys=True, ensure_ascii=False, indent=2)

    def clear_state(self):
        with open(self.state_file, "w") as f:
            json.dump({}, f, sort_keys=True, ensure_ascii=False, indent=2)

    def read_state(self, name: str, default=None) -> Any:
        state = {}
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                state = json.load(f)
        return state.get(name, default)

    def lock_state(self):
        pass

    def unlock_state(self):
        pass

    def is_locked(self) -> bool:
        return False
