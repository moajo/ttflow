from typing import Any, Optional

from ..system_states.run_state import _execute_once
from .context import Context
from .event import _enque_event
from .global_env import Global


# ステートを書き込む。再実行時は何もしない
def set_state(g: Global, c: Context, state_name: str, value):
    @_execute_once(g, c)
    def a():
        # ステートを書き込み、変更があったら差分イベントを発行する
        current_state = g.state.read_state(state_name)
        g.state.save_state(state_name, value)
        if current_state != value:
            _enque_event(
                g,
                f"state_changed_{state_name}",
                {"old": current_state, "new": value},
            )

    return a()


def get_state(g: Global, c: Context, state_name: str, default: Any = None):
    """ステートを取得する。再実行時はキャッシュする

    Args:
        g (Global): _description_
        c (Context): _description_
        state_name (str): _description_
        default (Any, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """

    @_execute_once(g, c)
    def a():
        return g.state.read_state(state_name, default=default)

    return a()


def add_list_state(
    g: Global,
    c: Context,
    state_name: str,
    value,
    max_length: Optional[int] = None,
):
    values = get_state(g, c, state_name, [])
    if values is not list:
        raise Exception(f"state {state_name} is not list")
    values.append(value)
    if max_length is not None:
        values = values[-max_length:]
    set_state(g, c, state_name, values)


def _add_list_state_raw(
    g: Global,
    state_name: str,
    value,
    max_length: Optional[int] = None,
):
    values = g.state.read_state(state_name, [])
    if type(values) != list:
        raise Exception(f"state {state_name} is not list")
    values.append(value)
    if max_length is not None:
        values = values[-max_length:]
    g.state.save_state(state_name, values)
