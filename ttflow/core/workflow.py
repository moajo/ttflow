import functools
from typing import Any, Optional

from ..system_states.completed import add_completed_runs_log
from .context import Context
from .global_env import Global
from .pause import PauseException, _save_paused_workflow
from .trigger import NullTrigger, Trigger


class Workflow:
    def __init__(self, trigger: Trigger, f):
        self.trigger = trigger
        self.f = f


def _add_workflow(g: Global, wf: Workflow):
    g.registerer.workflows.append(wf)


def _get_workflows(g: Global) -> list[Workflow]:
    return g.registerer.workflows


def exec_workflow(g: Global, c: Context, wf: Workflow, args: Any) -> bool:
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
    s = g.state
    try:
        wf.f(c, args)
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
    add_completed_runs_log(g, c)
    return True
    # TODO: そのうちワークフロー実行後イベントを実装


def workflow(g: Global, trigger: Optional[Trigger] = None):
    def _decorator(f):
        wf = Workflow(trigger if trigger is not None else NullTrigger(), f)
        _add_workflow(g, wf)

        @functools.wraps(f)
        def hoge_wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        return hoge_wrapper

    return _decorator
