import time

from ..core.context import Context
from ..core.global_env import Global
from ..core.state import get_state

# 発行されたイベントのログ


def _log_key():
    return "_event_log"


def _add_event_log(g: Global, event_name: str, args: dict):
    event_log = g.state.read_state(_log_key(), default=[])
    event_log.append(
        {
            "event_name": event_name,
            "args": args,
            "timestamp": time.time(),
        }
    )
    # 最新1000件のみ保持
    event_log = event_log[-1000:]
    g.state.save_state(_log_key(), event_log)


def get_event_logs(g: Global, c: Context) -> list:
    return get_state(g, c, _log_key(), default=[])


def _get_event_logs(g: Global) -> list:
    return g.state.read_state(_log_key(), default=[])
