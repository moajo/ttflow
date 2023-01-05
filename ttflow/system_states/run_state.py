import functools
from dataclasses import dataclass
from typing import Any, Optional

from ..core.context import Context
from ..core.global_env import Global

# run_idに紐づくrunの実行状態を保持する
# TODO: この状態は、run_idに紐づくrunが完了したときに削除される


def _log_key(run_id):
    return f"_run_state:{run_id}"


@dataclass
class ExecutedCache:
    value: Any


def _is_already_executed(g: Global, c: Context) -> Optional[ExecutedCache]:
    c._use()
    run_state_token = c.get_run_state_token()
    run_states = g.state.read_state(_log_key(c.run_id), default=[])
    for a in run_states:
        if a["token"] == run_state_token:
            c.used_count = a["last_used_count"]
            return ExecutedCache(a["value"])
    return None


def _mark_as_executed(g: Global, c: Context, run_state_token: str, value: Any):
    run_states = g.state.read_state(_log_key(c.run_id), default=[])

    # 既に記録済みの場合は何もしない
    tokens = [a["token"] for a in run_states]
    if run_state_token in tokens:
        return value

    run_states.append(
        {
            "token": run_state_token,  # f実行前のトークン。キャッシュキーになる
            "value": value,
            "last_used_count": c.used_count,  # f実行後の値。キャッシュ時はこの値を復元する
        }
    )
    g.state.save_state(_log_key(c.run_id), run_states)
    return value


def _delete_run_state(g: Global, run_id: str):
    g.state.save_state(_log_key(run_id), [])


def _execute_once(g: Global, c: Context):
    """fを実行する前に、実行済みかどうかをチェックし、実行済みならキャッシュを返す。
    fが例外を投げる場合はキャッシュできないので注意
    """

    def _decorator(f):
        @functools.wraps(f)
        def _wrapper(*args, **kwargs):
            cache = _is_already_executed(g, c)
            if cache is not None:
                return cache.value
            token = c.get_run_state_token()  # fを実行する前に計算しておく必要がある。変わってしまうので
            res = f(*args, **kwargs)
            return _mark_as_executed(g, c, token, res)

        return _wrapper

    return _decorator
