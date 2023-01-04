import time

from .core.context import Context
from .core.event import iterate_events
from .core.global_env import _get_state
from .core.pause import _wait_event, iterate_paused_workflows
from .core.trigger import EventTrigger, Trigger
from .core.workflow import _get_workflows, exec_workflow


def webhook(name: str) -> Trigger:
    return EventTrigger(f"_webhook_{name}")


def event(name: str) -> Trigger:
    return EventTrigger(name)


# 状態変化を監視するトリガー
def state(state_name: str) -> Trigger:
    return EventTrigger(f"state_changed_{state_name}")


def wait_event(c: Context, event_name: str):
    _wait_event(c, event_name)


def do_ttflow():
    s = _get_state()
    print("実行します")

    # イベントを処理する
    print("イベント処理開始")
    for e in iterate_events():
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
        for wf in _get_workflows():
            if (
                isinstance(wf.trigger, EventTrigger)
                and wf.trigger.event_name == event_name
            ):
                print("イベントに対応するワークフローを実行します: ", wf.f.__name__)
                c = Context(wf.f.__name__)
                exec_workflow(c, wf, args)

    # PAUSEDのワークフローを再開する
    for p in iterate_paused_workflows():
        print("再開します: ", p["workflow_name"])
        args = p["args"]
        wf = [a for a in _get_workflows() if a.f.__name__ == p["workflow_name"]][0]
        c = Context(wf.f.__name__, run_id=p["run_id"])
        exec_workflow(c, wf, args)
