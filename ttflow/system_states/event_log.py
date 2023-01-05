import time

from ..core.context import Context
from ..core.global_env import Global
from ..core.state import _add_list_state_raw, get_state

# 発行されたイベントのログ


def _log_key():
    return "_event_log"


def _add_event_log(g: Global, event_name: str, args: dict):
    # 最新1000件のみ保持
    return _add_list_state_raw(
        g,
        _log_key(),
        {
            "event_name": event_name,
            "args": args,
            "timestamp": time.time(),
        },
        max_length=1000,
    )


def get_event_logs(g: Global, c: Context) -> list:
    return get_state(g, c, _log_key(), default=[])


def _get_event_logs(g: Global) -> list:
    return g.state.read_state(_log_key(), default=[])
