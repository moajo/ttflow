import time
from typing import Any

from ..core.context import Context
from ..core.global_env import Global
from ..core.state import _add_list_state_raw, get_state

# 発行されたイベントのログ

_LOG_KEY = "_event_log"


def _add_event_log(g: Global, event_name: str, args: Any) -> None:
    # 最新1000件のみ保持
    return _add_list_state_raw(
        g,
        _LOG_KEY,
        {
            "event_name": event_name,
            "args": args,
            "timestamp": time.time(),
        },
        max_length=1000,
    )


def get_event_logs(g: Global, c: Context) -> list[dict]:
    return get_state(g, c, _LOG_KEY, default=[])


def _get_event_logs(g: Global) -> list[dict]:
    return g.state.read_state(_LOG_KEY, default=[])
