from typing import Any, Optional
from dataclasses import asdict, dataclass


from ..event import Event, _enque_event
from ..global_env import Global

# _every イベントは、毎回一度自動的に発生するイベントです。
# 毎回実行したいような場合に使用します

SYSTEM_EVENT__EVERY = "_every"


@dataclass
class EveryEvent:
    pass


def _enque_every_event(g: Global):
    _enque_event(
        g,
        event_name=SYSTEM_EVENT__EVERY,
        args=None,
        process_immediately=True,
    )


def try_parse_event__every(event_raw: Event) -> Optional[EveryEvent]:
    if event_raw.event_name != SYSTEM_EVENT__EVERY:
        return None
    return EveryEvent()
