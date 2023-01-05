from typing import Any

from ..system_states.run_state import _execute_once
from .context import Context
from .event import _enque_event
from .global_env import Global


# ステートを書き込む。再実行時は何もしない
def set_state(g: Global, c: Context, state_name: str, value):
    @_execute_once(g, c)
    def a():
        write_state_with_changed_event(g, state_name, value)

    return a()


# ステートを書き込み、変更があったら差分イベントを発行する
def write_state_with_changed_event(g: Global, state_name: str, value):
    current_state = g.state.read_state(state_name)
    g.state.save_state(state_name, value)
    if current_state != value:
        _enque_event(
            g,
            f"state_changed_{state_name}",
            {"old": current_state, "new": value},
        )


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
