import functools
import logging
from typing import Any, Optional

from ..system_states.completed import add_completed_runs_log, add_failed_runs_log
from ..system_states.run_state import _delete_run_state
from .context import Context
from .global_env import Global, Workflow
from .pause import PauseException, _save_paused_workflow
from .trigger import EventTrigger, NullTrigger, Trigger

logger = logging.getLogger(__name__)


def _find_workflow(g: Global, workflow_name: str) -> Optional[Workflow]:
    for wf in g.workflows:
        if wf.f.__name__ == workflow_name:
            return wf
    return None


def _find_event_triggered_workflows(g: Global, event_name: str):
    for wf in g.workflows:
        if isinstance(wf.trigger, EventTrigger) and wf.trigger.event_name == event_name:
            yield wf


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
    try:
        wf.f(c, args)
    except PauseException as e:
        logger.info("ワークフローを中断します")
        _save_paused_workflow(
            g,
            workflow_name=wf.f.__name__,
            run_id=c.run_id,
            pause_id=e.pause_id,
            args=args,
        )
        print(f"{wf.f.__name__}: 中断します")
        return False
    except Exception as e:
        logger.error(f"ワークフローが失敗しました: {e}")
        print(f"{wf.f.__name__}: error: {e}")
        add_failed_runs_log(g, c)
        return False
    add_completed_runs_log(g, c)
    _delete_run_state(g, c.run_id)
    print(f"{wf.f.__name__}: 正常終了しました")
    return True
    # TODO: そのうちワークフロー実行後イベントを実装


def workflow(g: Global, trigger: Optional[Trigger] = None):
    def _decorator(f):
        wf = Workflow(trigger if trigger is not None else NullTrigger(), f)
        g.workflows.append(wf)

        @functools.wraps(f)
        def hoge_wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        return hoge_wrapper

    return _decorator
