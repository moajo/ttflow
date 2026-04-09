from typing import Any

from ..errors import InvalidStateError
from ..system_states.run_state import _execute_once
from .context import Context
from .event import _enque_event
from .global_env import Global


# ステートを書き込む。再実行時は何もしない
def set_state(g: Global, c: Context, state_name: str, value: Any) -> None:
    @_execute_once(g, c)
    def a():
        # ステートを書き込み、変更があったら差分イベントを発行する
        current_state = g.state.read_state(state_name)
        g.state.save_state(state_name, value)
        if current_state != value:
            # トレース記録
            if g.trace_recorder is not None:
                g.trace_recorder.record_state_change(state_name, current_state, value)
            _enque_event(
                g,
                f"state_changed_{state_name}",
                {"old": current_state, "new": value},
            )

    return a()


def get_state(g: Global, c: Context, state_name: str, default: Any = None) -> Any:
    """ステートを取得する。再実行時はキャッシュする"""

    @_execute_once(g, c)
    def a():
        return g.state.read_state(state_name, default=default)

    return a()


def add_list_state(
    g: Global,
    c: Context,
    state_name: str,
    value: Any,
    max_length: int | None = None,
) -> None:
    values = get_state(g, c, state_name, default=[])
    if not isinstance(values, list):
        raise InvalidStateError(f"state {state_name} is not list")
    values = [a for a in values]
    values.append(value)
    if max_length is not None:
        values = values[-max_length:]
    set_state(g, c, state_name, values)


def _add_list_state_raw(
    g: Global,
    state_name: str,
    value: Any,
    max_length: int | None = None,
) -> None:
    values = g.state.read_state(state_name, [])
    if not isinstance(values, list):
        raise InvalidStateError(f"state {state_name} is not list")
    values.append(value)
    if max_length is not None:
        values = values[-max_length:]
    g.state.save_state(state_name, values)
