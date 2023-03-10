from typing import Any, Optional

from ..system_states.logs import log
from .context import Context
from .event import _enque_event
from .global_env import Global
from .pause import _pause_once, _wait_event
from .state import add_list_state, get_state, set_state


class RunContext:
    def __init__(self, _global: Global, _context: Context):
        self._global = _global
        self._context = _context

    def get_context_data(self) -> Context:
        return self._context

    def get_state(self, state_name: str, default: Any = None):
        return get_state(self._global, self._context, state_name, default)

    def set_state(self, state_name: str, value):
        return set_state(self._global, self._context, state_name, value)

    def add_list_state(
        self,
        state_name: str,
        value,
        max_length: Optional[int] = None,
    ):
        return add_list_state(
            self._global, self._context, state_name, value, max_length=max_length
        )

    def log(self, message: str):
        return log(self._global, self._context, message)

    def wait_event(self, event_name: str):
        """指定したイベントが発行されるまで中断します

        Args:
            event_name (str): _description_
        """
        _wait_event(self._global, self._context, event_name)

    def pause_once(self):
        """一度だけ中断します。次回無条件で再開します"""
        _pause_once(self._global, self._context)

    def event(self, name: str, args: Any):
        """
        eventの発生をstateにキューイングします。
        次回のrun()で実行されます。

        Args:
            name (str): _description_
            args (Any): _description_
        """
        _enque_event(self._global, name, args)
