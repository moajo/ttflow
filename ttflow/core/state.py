import functools
import importlib
import time
from pathlib import Path
from typing import Optional,Any
import sys

from .context import Context
from .global_env import _global
from .event import _enque_event


# ステートを書き込む。再実行時は何もしない
def set_state(c: Context,state_name:str,value):
    s= _global.state
    c._use()
    set_state_id = f"{c.run_id}:{c.used_count}"
    set_state_cache = s.read_state("_set_state_cache",default={})
    if set_state_id in set_state_cache:
        return
    set_state_cache[set_state_id] = value
    s.save_state("_set_state_cache",set_state_cache)
    write_state_with_changed_event(state_name,value)

# ステートを書き込み、変更があったら差分イベントを発行する
def write_state_with_changed_event(state_name:str,value):
    s= _global.state
    current_state = s.read_state(state_name)
    s.save_state(state_name, value)
    if current_state != value:
        _enque_event(f"state_changed_{state_name}",{
            "old":current_state,
            "new":value
        })


# ステートを取得する。再実行時はキャッシュする
def get_state(c: Context,state_name:str,default:Any=None):
    s= _global.state
    c._use()
    get_state_id = f"{c.run_id}:{c.used_count}"
    get_state_cache = s.read_state("_get_state_cache",default={})
    if get_state_id in get_state_cache:
        return get_state_cache[get_state_id]

    get_state_cache[get_state_id] = s.read_state(state_name,default=default)
    s.save_state("_get_state_cache",get_state_cache)
    return get_state_cache[get_state_id]
