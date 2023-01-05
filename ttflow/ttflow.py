import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional, Union

from .core.context import Context
from .core.event import (
    _enque_event,
    _enque_trigger,
    flush_events_for_next_run_to_state,
    iterate_events,
    load_events_from_state,
)
from .core.global_env import Global
from .core.system_events.pause import try_parse_pause_event
from .core.trigger import EventTrigger, Trigger
from .core.workflow import (
    WorkflowRunResult,
    _find_event_triggered_workflows,
    _find_workflow,
    exec_workflow,
    sideeffect,
    workflow,
)
from .state_repository.buffer_cache_proxy import BufferCacheStateRepositoryProxy
from .system_states.event_log import _add_event_log
from .utils import workflow_hash

logger = logging.getLogger(__name__)


def event_trigger(name: str) -> Trigger:
    """イベントトリガー"""
    return EventTrigger(name)


def state_trigger(state_name: str) -> Trigger:
    """状態変化を監視するトリガー

    Args:
        state_name (str): _description_

    Returns:
        Trigger: _description_
    """
    return EventTrigger(f"state_changed_{state_name}")


@contextmanager
def _lock_state(g: Global):
    if g.state.is_locked():
        logger.info("state is locked. skip run.")
        raise ValueError("state is locked")
    g.state.lock_state()
    try:
        yield
    finally:
        g.state.unlock_state()


class Client:
    def __init__(self, _global: Global):
        self._global = _global

    def workflow(self, trigger: Optional[Union[Trigger, str]] = None):
        return workflow(self._global, trigger)

    def sideeffect(self):
        return sideeffect(self._global)

    def run(self, trigger_name: Optional[str] = None, args: Any = None):
        """
        トリガーに基づいてワークフローを実行します

        Args:
            name (str): _description_
            args (Any): _description_
        """
        if trigger_name is not None:
            _enque_trigger(self._global, trigger_name, args)
        with _lock_state(self._global):
            with self._global.state.buffering():
                return self.__run()

    def __run(self) -> list[WorkflowRunResult]:
        logger.info("check registered workflows")

        # デプロイイベントの対応
        h = workflow_hash(self._global.workflows)
        current_hash = self._global.state.read_state("workflows_hash")
        if current_hash != h:
            logger.info(
                f"workflow is changed from last run. hash: {current_hash} -> {h}"
            )
            _enque_event(self._global, "workflows_changed", None)
            self._global.state.save_state("workflows_hash", h)

        # 未処理イベントをロードする
        load_events_from_state(self._global)

        logger.info("start event loop")
        workflow_run_results: list[WorkflowRunResult] = []
        for e in iterate_events(self._global):
            event_name = e.event_name
            args = e.args
            # NOTE: system eventは数が多くユーザがあまりhookするべきではないのでevent logには記録しない
            if (pause_event := try_parse_pause_event(e)) is not None:
                c = Context(
                    pause_event.workflow_name,
                    run_id=pause_event.run_id,
                    paused_info=args,
                )
                wf = _find_workflow(self._global, pause_event.workflow_name)
                if wf is not None:
                    logger.info(f"workflow '{wf.f.__name__}' resuming")
                    print()
                    print(f"{wf.f.__name__}: 中断した点から再開します")
                    workflow_run_results.append(
                        exec_workflow(self._global, c, wf, args["args"])
                    )
            elif event_name.startswith("_"):
                logger.info(f"processing system event '{event_name}'")
                for wf in _find_event_triggered_workflows(self._global, event_name):
                    logger.info(f"'{wf.f.__name__}' triggered by event '{event_name}'")
                    print()
                    print(f"{wf.f.__name__}: イベント'{event_name}'により実行されます")
                    c = Context(wf.f.__name__)
                    workflow_run_results.append(
                        exec_workflow(self._global, c, wf, args)
                    )
            else:
                logger.info(f"processing event '{event_name}'")
                print(f"イベント[{event_name}]が発生しました")
                _add_event_log(
                    self._global,
                    event_name,
                    args,
                )
                for wf in _find_event_triggered_workflows(self._global, event_name):
                    print()
                    print(f"{wf.f.__name__}: イベント[{event_name}]により実行されます")
                    logger.info(
                        f"run workflow '{wf.f.__name__}' triggered by event '{event_name}'"
                    )
                    c = Context(wf.f.__name__)
                    workflow_run_results.append(
                        exec_workflow(self._global, c, wf, args)
                    )

        logger.info("do post processes")
        # eventを永続化してメモリ上から消す
        flush_events_for_next_run_to_state(self._global)
        self._global.purge_events()
        return workflow_run_results


def setup(
    state_repository: str = "local:state.json",
) -> Client:
    if state_repository.startswith("local:"):
        from .state_repository.local_file_state import LocalFileStateRepository

        s = LocalFileStateRepository(state_file=Path(state_repository[len("local:") :]))
    elif state_repository.startswith("dynamodb:"):
        from .state_repository.dynamodb import DynamoDBStateRepository

        s = DynamoDBStateRepository(
            table_name=state_repository[len("dynamodb:") :],
        )
    elif state_repository.startswith("s3:"):
        from .state_repository.s3 import S3StateRepository

        s3_path = state_repository[len("s3:") :]
        if "/" not in s3_path:
            bucket = s3_path
            prefix = ""
        else:
            bucket, prefix = s3_path.split("/", maxsplit=1)

        s = S3StateRepository(
            bucket_name=bucket,
            prefix=prefix,
        )
    elif state_repository.startswith("onmemory"):
        from .state_repository.on_memory_state import OnMemoryStateRepository

        s = OnMemoryStateRepository()
    else:
        raise Exception("Unknown repository: ", state_repository)

    return Client(
        Global(
            state=BufferCacheStateRepositoryProxy(s),
        )
    )
