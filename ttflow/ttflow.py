import time
from typing import Any, Optional

from .core.context import Context
from .core.event import _enque_event, iterate_events
from .core.global_env import Global
from .core.pause import _wait_event, iterate_paused_workflows
from .core.state import get_state, set_state
from .core.trigger import EventTrigger, Trigger
from .core.workflow import _get_workflows, exec_workflow, workflow
from .system_states.logs import log
from .utils import workflow_hash


class Client:
    def __init__(self):
        self._global = Global()

    def webhook(self, name: str) -> Trigger:
        return EventTrigger(f"_webhook_{name}")

    def event(self, name: str) -> Trigger:
        return EventTrigger(name)

    def workflow(self, trigger: Optional[Trigger] = None):
        return workflow(self._global, trigger)

    def get_state(self, c: Context, state_name: str, default: Any = None):
        return get_state(self._global, c, state_name, default)

    def set_state(self, c: Context, state_name: str, value):
        set_state(self._global, c, state_name, value)

    # 状態変化を監視するトリガー
    def state(self, state_name: str) -> Trigger:
        return EventTrigger(f"state_changed_{state_name}")

    def log(self, c: Context, message: str):
        return log(self._global, c, message)

    def wait_event(self, c: Context, event_name: str):
        _wait_event(self._global.state, c, event_name)

    def do_ttflow(self):
        s = self._global.state
        print("実行します")

        # イベントを処理する
        print("イベント処理開始")
        for e in iterate_events(self._global):
            event_name = e["event_name"]
            args = e["args"]
            event_log = s.read_state("event_log", default=[])
            event_log.append(
                {
                    "event_name": event_name,
                    "args": args,
                    "timestamp": time.time(),
                }
            )
            s.save_state("event_log", event_log)
            for wf in _get_workflows(self._global):
                if (
                    isinstance(wf.trigger, EventTrigger)
                    and wf.trigger.event_name == event_name
                ):
                    print("イベントに対応するワークフローを実行します: ", wf.f.__name__)
                    c = Context(wf.f.__name__)
                    exec_workflow(self._global, c, wf, args)

        # PAUSEDのワークフローを再開する
        for p in iterate_paused_workflows(self._global.state):
            print("再開します: ", p["workflow_name"])
            args = p["args"]
            wf = [
                a
                for a in _get_workflows(self._global)
                if a.f.__name__ == p["workflow_name"]
            ][0]
            c = Context(wf.f.__name__, run_id=p["run_id"])
            exec_workflow(self._global, c, wf, args)

    def run(self):
        print("ワークフローをロードします")
        # g = self._global
        try:
            # sys.path.insert(1, str(workflow_dir))
            # m = importlib.import_module("index")
            # reset_global_registerer()
            # g.registerer.reset()
            # importlib.reload(m)
            # sys.path.remove(str(workflow_dir))
            # write_state_with_changed_event(g, "workflow_loaded_successfull", True)

            # デプロイイベントの対応
            # h = utils.get_dir_hash(str(workflow_dir))
            h = workflow_hash(self._global.registerer.workflows)
            s = self._global.state
            current_hash = s.read_state("workflows_hash")
            if current_hash != h:
                _enque_event(self._global, "workflows_changed", None)
                s.save_state("workflows_hash", h)
            self.do_ttflow()
            return True
        except Exception as e:
            print("ワークフローの読み込みに失敗しました", e)
            # write_state_with_changed_event(g, "workflow_loaded_successfull", False)
            return False


def setup(
    # repository: str,
) -> Client:
    return Client()