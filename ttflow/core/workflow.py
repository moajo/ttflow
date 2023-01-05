import functools
import logging
from dataclasses import dataclass
from typing import Any, Optional, Union

from ..system_states.completed import add_completed_runs_log, add_failed_runs_log
from ..system_states.logs import _get_logs
from ..system_states.run_state import (
    _delete_run_state,
    _is_already_executed,
    _mark_as_executed,
)
from .context import Context
from .global_env import Global, Workflow
from .pause import PauseException, _save_paused_workflow
from .run_context import RunContext
from .trigger import EventTrigger, Trigger

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


@dataclass
class WorkflowRunResult:
    workflow_name: str
    run_id: str
    status: str  # succeeded, failed, paused
    error_message: Optional[str]
    logs: list[str]


def exec_workflow(g: Global, c: Context, wf: Workflow, args: Any) -> WorkflowRunResult:
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
        wf.f(RunContext(g, c), args)
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
        return WorkflowRunResult(
            workflow_name=wf.f.__name__,
            run_id=c.run_id,
            status="paused",
            error_message=None,
            logs=_get_logs(g, c.run_id),
        )
    except Exception as e:
        logger.error(f"ワークフローが失敗しました: {e}")
        print(f"{wf.f.__name__}: error: {e}")
        add_failed_runs_log(g, c)
        return WorkflowRunResult(
            workflow_name=wf.f.__name__,
            run_id=c.run_id,
            status="failed",
            error_message=repr(e),
            logs=_get_logs(g, c.run_id),
        )
    add_completed_runs_log(g, c)
    _delete_run_state(g, c.run_id)
    print(f"{wf.f.__name__}: 正常終了しました")
    return WorkflowRunResult(
        workflow_name=wf.f.__name__,
        run_id=c.run_id,
        status="succeeded",
        error_message=None,
        logs=_get_logs(g, c.run_id),
    )
    # TODO: そのうちワークフロー実行後イベントを実装


def workflow(g: Global, trigger: Optional[Union[Trigger, str]] = None):
    def _decorator(f):
        if trigger is None:
            t = EventTrigger(f"_trigger_{f.__name__}")
        elif isinstance(trigger, str):
            t = EventTrigger(f"_trigger_{trigger}")
        else:
            t = trigger
        wf = Workflow(t, f)
        g.workflows.append(wf)

        @functools.wraps(f)
        def _wrapper(*args, **kwargs):
            raise RuntimeError("workflow can not be called directly")

        return _wrapper

    return _decorator


def sideeffect(g: Global):
    def _decorator(f):
        @functools.wraps(f)
        def _wrapper(*args, **kwargs):
            if len(args) == 0 or not isinstance(args[0], RunContext):
                raise RuntimeError("sideeffectはRunContextを第1引数に取る必要があります")
            c = args[0]
            if _is_already_executed(g, c.get_context_data()) is not None:
                return
            return _mark_as_executed(g, c.get_context_data(), f(*args, **kwargs))

        return _wrapper

    return _decorator
