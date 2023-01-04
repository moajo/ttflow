from typing import Any
import time

from ..state_repository.base import StateRepository
from .context import Context
from .global_env import _get_state

# ワークフローの中断
# ワークフローは中断時にPauseExceptionを投げる。
# その場合、paused_workflowsに中断情報が保存される。
# 中断ワークフローが再実行される場合、run_idが同じになるのでrun_idに対して処理が冪等になっていれば、何度中断しても問題ない。

class PauseException(Exception):
    def __init__(self, pause_id:str):
        super().__init__()
        self.pause_id = pause_id

def _save_paused_workflow(
    s:StateRepository,
    workflow_name:str,
    run_id:Any,
    pause_id:str,
    args:Any,
    ):
    paused_workflows = s.read_state("paused_workflows",default=[])
    if len([
        a for a in paused_workflows
        if a["pause_id"]==pause_id
    ]) ==0: # 既にポーズしてるなら重複登録はしない
        paused_workflows.append({
            "workflow_name":workflow_name,
            "run_id":run_id,
            "pause_id": pause_id,
            "args":args,
            "timestamp":time.time(),
        })
        s.save_state("paused_workflows", paused_workflows)
def _find_paused_workflow(s:StateRepository,pause_id:str):
    paused_workflows = s.read_state("paused_workflows",default=[])
    for p in paused_workflows:
        if p["pause_id"] == pause_id:
            return p
    return None

def _remove_paused_workflow(s:StateRepository,pause_id:str):
    paused_workflows = s.read_state("paused_workflows",default=[])
    for p in paused_workflows:
        if p["pause_id"] == pause_id:
            paused_workflows.remove(p)
            s.save_state("paused_workflows", paused_workflows)
            return

def _wait_event(c: Context,event_name:str):
    s= _get_state()
    c._use()
    pause_id = f"{c.run_id}:{c.used_count}"

    paused_wf = _find_paused_workflow(s,pause_id)
    if paused_wf is None:
        raise PauseException(pause_id)
    # 既にpaused、先に進むか判断する
    event_log = s.read_state("event_log",default=[])
    target_events = [
        a for a in event_log 
        if a["event_name"] == event_name and a["timestamp"] > paused_wf["timestamp"]
    ]
    if len(target_events) > 0:
        _remove_paused_workflow(s,pause_id)
        return
    else:
        raise PauseException(pause_id)


def iterate_paused_workflows():
    s= _get_state()
    paused_workflows = s.read_state("paused_workflows",default=[])
    for p in paused_workflows:
        yield p
