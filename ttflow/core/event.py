from collections.abc import Generator
from dataclasses import asdict
from typing import Any

from dacite import from_dict

from ..constants import STATE_KEY_EVENTS
from .global_env import Event, Global

# _global.eventsはオンメモリのイベントキューである
# ttflowの一回の実行は、イベントキューが空になるまで続く


def _enque_event(
    g: Global,
    event_name: str,
    args: Any,
    process_immediately: bool = True,
) -> None:
    """イベントをキューに追加する

    Args:
        process_immediately: Trueならこのrun中に処理される。Falseなら次回のrunで処理される。
    """
    e = Event(
        event_name=event_name,
        args=args,
    )
    if process_immediately:
        g.events.append(e)
    else:
        g.events_for_next_run.append(e)


# triggerは実態としては単にイベントである
def _enque_trigger(g: Global, name: str, args: Any) -> None:
    # triggerなので即時実行
    _enque_event(g, f"_trigger_{name}", args, process_immediately=True)


def load_events_from_state(g: Global) -> None:
    es = _read_events_from_state(g)
    g.events.extend(es)


def _read_events_from_state(g: Global) -> list[Event]:
    unprocessed_events = g.state.read_state(STATE_KEY_EVENTS, default=[])
    return [from_dict(data_class=Event, data=e) for e in unprocessed_events]


def flush_events_for_next_run_to_state(g: Global) -> None:
    es = [asdict(e) for e in g.events_for_next_run]
    g.state.save_state(STATE_KEY_EVENTS, es)


def _pop_event(
    g: Global,
) -> Event | None:
    if len(g.events) == 0:
        return None
    return g.events.pop(0)


def iterate_events(
    g: Global,
) -> Generator[Event, None, None]:
    while True:
        e = _pop_event(g)
        if e is None:
            break
        yield e
