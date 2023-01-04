from typing import Any, Optional

from .global_env import Global

# _global.eventsはオンメモリのイベントキューである
# ttflowの一回の実行は、イベントキューが空になるまで続く


def _enque_event(g: Global, event_name: str, args: Any):
    g.events.append(
        {
            "event_name": event_name,
            "args": args,
        }
    )


# webhookは実態としては単にイベントである
def _enque_webhook(g: Global, name: str, args: Any):
    _enque_event(g, f"_webhook_{name}", args)


def _pop_event(
    g: Global,
) -> Optional[dict]:
    if len(g.events) == 0:
        return None
    return g.events.pop(0)


def iterate_events(
    g: Global,
):
    while True:
        e = _pop_event(g)
        if e is None:
            break
        yield e
