from typing import Any

from ..system_states.event_log import _get_event_logs
from ..system_states.run_state import _is_already_executed, _mark_as_executed
from .context import Context
from .global_env import Global

# ワークフローの中断
# ワークフローは中断時にPauseExceptionを投げる。
# その場合、stateに中断情報が保存される。
# 中断ワークフローが再実行される場合、run_idが同じになるのでrun_idに対して処理が冪等になっていれば、何度中断しても問題ない。


class PauseException(Exception):
    def __init__(self, pause_id: str):
        super().__init__()
        self.pause_id = pause_id


def _wait_event(g: Global, c: Context, event_name: str):
    c._use()
    pause_id = f"{c.run_id}:{c.used_count}"

    # 初回なので中断情報を保存する
    if c.paused_info is None:
        raise PauseException(pause_id)

    # 既にpaused、先に進むか判断する
    event_log = _get_event_logs(g)
    target_events = [
        a
        for a in event_log
        if a["event_name"] == event_name and a["timestamp"] > c.paused_info["timestamp"]
    ]
    if len(target_events) == 0:
        raise PauseException(pause_id)


def _pause_once(g: Global, c: Context):
    """一度だけ中断します。次回無条件で再開します"""
    cache = _is_already_executed(g, c)
    if cache is not None:
        return cache.value
    token = c.get_run_state_token()  # fを実行する前に計算しておく必要がある。変わってしまうので
    _mark_as_executed(g, c, token, None)
    raise PauseException(c.get_run_state_token())
