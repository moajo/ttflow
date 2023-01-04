from dataclasses import asdict
from typing import Any, Optional

from dacite import from_dict

from .global_env import Event, Global

# _global.eventsはオンメモリのイベントキューである
# ttflowの一回の実行は、イベントキューが空になるまで続く


def _enque_event(
    g: Global,
    event_name: str,
    args: Any,
    process_immediately: bool = True,
):
    """_summary_

    Args:
        g (Global): _description_
        event_name (str): _description_
        args (Any): _description_
        process_immediately (bool, optional): Trueならこのrun中に処理されます。そうでなければ次回のrunで処理されます. Defaults to False.
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
def _enque_trigger(g: Global, name: str, args: Any):
    # triggerなので即時実行
    _enque_event(g, f"_trigger_{name}", args, process_immediately=True)


def load_events_from_state(g: Global):
    es = _read_events_from_state(g)
    g.events.extend(es)


def _read_events_from_state(g: Global):
    unprocessed_events = g.state.read_state("_events", default=[])
    return [from_dict(data_class=Event, data=e) for e in unprocessed_events]


def flush_events_for_next_run_to_state(g: Global):
    es = [asdict(e) for e in g.events_for_next_run]
    g.state.save_state("_events", es)


def _pop_event(
    g: Global,
) -> Optional[Event]:
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
