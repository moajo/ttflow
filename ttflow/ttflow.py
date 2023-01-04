import time
from pathlib import Path
from typing import Any, Optional
import logging

from .core.context import Context
from .core.event import _enque_event, iterate_events, _enque_webhook
from .core.global_env import Global
from .core.pause import _wait_event, iterate_paused_workflows
from .core.state import get_state, set_state
from .core.trigger import EventTrigger, Trigger
from .core.workflow import _get_workflows, exec_workflow, workflow
from .system_states.logs import log
from .system_states.event_log import _add_event_log
from .utils import workflow_hash

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


def webhook_trigger(name: str) -> Trigger:
    """webhookトリガー

    Args:
        name (str): _description_

    Returns:
        Trigger: _description_
    """
    return EventTrigger(f"_webhook_{name}")


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


class Client:
    def __init__(self, _global: Global):
        self._global = _global

    def workflow(self, trigger: Optional[Trigger] = None):
        return workflow(self._global, trigger)

    def get_state(self, c: Context, state_name: str, default: Any = None):
        return get_state(self._global, c, state_name, default)

    def set_state(self, c: Context, state_name: str, value):
        set_state(self._global, c, state_name, value)

    def log(self, c: Context, message: str):
        return log(self._global, c, message)

    def wait_event(self, c: Context, event_name: str):
        _wait_event(self._global, c, event_name)

    def run(self):
        logger.info("check registered workflows")

        # デプロイイベントの対応
        h = workflow_hash(self._global.registerer.workflows)
        current_hash = self._global.state.read_state("workflows_hash")
        if current_hash != h:
            logger.info(
                f"workflow is changed from last run. hash: {current_hash} -> {h}"
            )
            _enque_event(self._global, "workflows_changed", None)
            self._global.state.save_state("workflows_hash", h)

        # PAUSEDのワークフローを再開する
        for p in iterate_paused_workflows(self._global.state):
            logger.info(f"resume paused workflow: {p['workflow_name']}")
            args = p["args"]
            wf = [
                a
                for a in _get_workflows(self._global)
                if a.f.__name__ == p["workflow_name"]
            ][0]
            c = Context(wf.f.__name__, run_id=p["run_id"])
            exec_workflow(self._global, c, wf, args)

        logger.info("start event loop")
        for e in iterate_events(self._global):
            event_name = e["event_name"]
            args = e["args"]
            logger.info(f"processing event '{event_name}'")
            _add_event_log(
                self._global,
                event_name,
                args,
            )
            for wf in _get_workflows(self._global):
                if (
                    isinstance(wf.trigger, EventTrigger)
                    and wf.trigger.event_name == event_name
                ):
                    logger.info(
                        f"run workflow '{wf.f.__name__}' triggered by event '{event_name}'"
                    )
                    c = Context(wf.f.__name__)
                    exec_workflow(self._global, c, wf, args)

    def euqueue_webhook(self, name: str, args: Any):
        """
        webhookの発生をstateにキューイングします。
        次回のrun()で実行されます。

        Args:
            name (str): _description_
            args (Any): _description_
        """
        _enque_webhook(self._global, name, args)

    def euqueue_event(self, name: str, args: Any):
        """
        eventの発生をstateにキューイングします。
        次回のrun()で実行されます。

        Args:
            name (str): _description_
            args (Any): _description_
        """
        _enque_event(self._global, name, args)


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
    else:
        raise Exception("Unknown repository: ", state_repository)

    return Client(
        Global(
            state=s,
        )
    )
