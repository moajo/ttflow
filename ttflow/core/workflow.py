import functools
import importlib
import time
from pathlib import Path
from typing import Optional,Any
import sys

from .context import Context
from .pause import PauseException,_save_paused_workflow
from ..system_states.completed import add_completed_runs_log
from .. import utils
from .global_env import _global,reset_global_registerer,_get_state
from .trigger import Trigger,NullTrigger
from .event import _enque_event
from .state import write_state_with_changed_event


class Workflow:
    def __init__(self, trigger:Trigger, f):
        self.trigger = trigger
        self.f = f


def _add_workflow(wf:Workflow):
    _global.registerer.workflows.append(wf)

def _get_workflows()->list[Workflow]:
    return _global.registerer.workflows

def exec_workflow(c:Context,wf:Workflow,args:Any)->bool:
    """workflowを実行する
    中断する場合、paused_workflowsステートにその状態を保存する
    完了したらcompleted_runs_logステートに記録する

    Args:
        c (Context): _description_
        wf (Workflow): _description_
        args (Any): _description_

    Returns:
        bool: _description_
    """
    s= _get_state()
    try:
        wf.f(c,args)
    except PauseException as e:
        print("ワークフローを中断します")
        _save_paused_workflow(
            s,
            workflow_name=wf.f.__name__,
            run_id=c.run_id,
            pause_id=e.pause_id,
            args=args,
        )
        return False
    add_completed_runs_log(c)
    return True
    #TODO: そのうちワークフロー実行後イベントを実装

def workflow(trigger:Optional[Trigger]=None):
    def _decorator(f):
        wf = Workflow(trigger if trigger is not None else NullTrigger(),f)
        _add_workflow(wf)
        @functools.wraps(f)
        def hoge_wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return hoge_wrapper
    return _decorator

def load_workflows(workflow_dir:Path):
    print("ワークフローをロードします")
    try:
        sys.path.insert(1, str(workflow_dir))
        m=importlib.import_module('index')
        reset_global_registerer()
        importlib.reload(m)
        sys.path.remove(str(workflow_dir))
        write_state_with_changed_event("workflow_loaded_successfull", True)

        # デプロイイベントの対応
        h = utils.get_dir_hash(str(workflow_dir))
        s= _global.state
        current_hash = s.read_state("workflows_hash")
        if current_hash != h:
            _enque_event("workflows_changed",None)
            s.save_state("workflows_hash", h)
        return True
    except Exception as e:
        print("ワークフローの読み込みに失敗しました",e)
        write_state_with_changed_event("workflow_loaded_successfull", False)
        return False
