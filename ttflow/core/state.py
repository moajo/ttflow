from typing import Any

from .context import Context
from .event import _enque_event
from .global_env import Global


# ステートを書き込む。再実行時は何もしない
def set_state(g: Global, c: Context, state_name: str, value):
    c._use()
    set_state_id = f"{c.run_id}:{c.used_count}"
    set_state_cache = g.state.read_state("_set_state_cache", default={})
    if set_state_id in set_state_cache:
        return
    set_state_cache[set_state_id] = value
    g.state.save_state("_set_state_cache", set_state_cache)
    write_state_with_changed_event(g, state_name, value)


# ステートを書き込み、変更があったら差分イベントを発行する
def write_state_with_changed_event(g: Global, state_name: str, value):
    s = g.state
    current_state = s.read_state(state_name)
    s.save_state(state_name, value)
    if current_state != value:
        _enque_event(
            g,
            f"state_changed_{state_name}",
            {"old": current_state, "new": value},
        )


# ステートを取得する。再実行時はキャッシュする
def get_state(g: Global, c: Context, state_name: str, default: Any = None):
    s = g.state
    c._use()
    get_state_id = f"{c.run_id}:{c.used_count}"
    get_state_cache = s.read_state("_get_state_cache", default={})
    if get_state_id in get_state_cache:
        return get_state_cache[get_state_id]

    get_state_cache[get_state_id] = s.read_state(state_name, default=default)
    s.save_state("_get_state_cache", get_state_cache)
    return get_state_cache[get_state_id]
