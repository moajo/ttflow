import time
from dataclasses import asdict, dataclass

from dacite import from_dict

from ..core.context import Context
from ..core.global_env import Global
from ..core.state import _add_list_state_raw, get_state

# 完了したrunのログを保持する


@dataclass
class CompletedLog:
    workflow_name: str
    run_id: str
    timestamp: float
    status: str


def _log_key():
    return "_completed"


def add_completed_runs_log(g: Global, c: Context):
    _add_runs_log(
        g,
        c,
        asdict(
            CompletedLog(
                workflow_name=c.workflow_name,
                run_id=c.run_id,
                timestamp=time.time(),
                status="success",
            )
        ),
    )


def add_failed_runs_log(g: Global, c: Context):
    _add_runs_log(
        g,
        c,
        asdict(
            CompletedLog(
                workflow_name=c.workflow_name,
                run_id=c.run_id,
                timestamp=time.time(),
                status="failed",
            )
        ),
    )


def _add_runs_log(g: Global, c: Context, data: dict):
    _add_list_state_raw(g, _log_key(), data, max_length=1000)


def get_completed_runs_log(g: Global, c: Context):
    v = get_state(g, c, _log_key(), [])
    return [from_dict(CompletedLog, x) for x in v]


def _get_completed_runs_log(g: Global):
    return g.state.read_state(_log_key(), [])
