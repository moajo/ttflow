import asyncio
import functools
import inspect
import logging
from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import Any

from ..errors import SideeffectUsageError, WorkflowDirectCallError
from ..system_states.completed import add_completed_runs_log, add_failed_runs_log
from ..system_states.logs import _get_logs
from ..system_states.run_state import (
    _delete_run_state,
    _execute_once,
    _execute_once_async,
)
from .context import Context
from .global_env import Global, Workflow
from .pause import PauseException
from .run_context import RunContext
from .system_events.pause import _enque_pause_event
from .trigger import EventTrigger, Trigger

logger = logging.getLogger(__name__)


def _find_workflow(g: Global, workflow_name: str) -> Workflow | None:
    for wf in g.workflows:
        if wf.f.__name__ == workflow_name:
            return wf
    return None


def _find_event_triggered_workflows(
    g: Global, event_name: str
) -> Generator[Workflow, None, None]:
    for wf in g.workflows:
        if isinstance(wf.trigger, EventTrigger) and wf.trigger.event_name == event_name:
            yield wf


@dataclass
class WorkflowRunResult:
    workflow_name: str
    run_id: str
    status: str  # succeeded, failed, paused
    error_message: str | None
    logs: list[str]


def _call_workflow_func(wf: Workflow, g: Global, c: Context, args: Any):
    """ワークフロー関数を呼び出す。asyncの場合はasyncio.run()で実行する"""
    params = inspect.signature(wf.f).parameters
    if inspect.iscoroutinefunction(wf.f):
        # asyncワークフロー
        if len(params) >= 2:
            asyncio.run(wf.f(RunContext(g, c), args))
        else:
            asyncio.run(wf.f(RunContext(g, c)))
    else:
        # syncワークフロー
        if len(params) >= 2:
            wf.f(RunContext(g, c), args)
        else:
            wf.f(RunContext(g, c))


def exec_workflow(g: Global, c: Context, wf: Workflow, args: Any) -> WorkflowRunResult:
    """workflowを実行する
    中断する場合、paused_workflowsステートにその状態を保存する
    完了したらcompleted_runs_logステートに記録する
    """

    try:
        _call_workflow_func(wf, g, c, args)
    except PauseException as e:
        logger.info("ワークフローを中断します")
        _enque_pause_event(
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


def workflow(g: Global, trigger: Trigger | str | None = None) -> Callable:
    def _decorator(f: Callable) -> Callable:
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
            raise WorkflowDirectCallError("workflow can not be called directly")

        return _wrapper

    return _decorator


def sideeffect(g: Global) -> Callable:
    def _decorator(f: Callable) -> Callable:
        if inspect.iscoroutinefunction(f):
            # async sideeffect: syncワークフローからの呼び出しを検出するため、
            # 通常の関数でラップし、実行中イベントループの有無で判定する
            @functools.wraps(f)
            def _async_guard(*args, **kwargs):
                try:
                    asyncio.get_running_loop()
                except RuntimeError:
                    raise SideeffectUsageError(
                        "async sideeffectはasyncワークフローからのみ呼び出せます"
                    )
                return _async_impl(*args, **kwargs)

            async def _async_impl(*args, **kwargs):
                if len(args) == 0 or not isinstance(args[0], RunContext):
                    raise SideeffectUsageError(
                        "sideeffectはRunContextを第1引数に取る必要があります"
                    )
                c = args[0]

                @_execute_once_async(g, c.get_context_data())
                async def a():
                    return await f(*args, **kwargs)

                return await a()

            return _async_guard
        else:
            # sync sideeffect
            @functools.wraps(f)
            def _wrapper(*args, **kwargs):
                if len(args) == 0 or not isinstance(args[0], RunContext):
                    raise SideeffectUsageError(
                        "sideeffectはRunContextを第1引数に取る必要があります"
                    )
                c = args[0]

                @_execute_once(g, c.get_context_data())
                def a():
                    return f(*args, **kwargs)

                return a()

            return _wrapper

    return _decorator
