"""実行トレース

client.run()の各呼び出しごとに、イベント→ワークフロー実行の因果関係を記録する。
可視化APIのデータソースとして使用される。
"""

import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from ..core.global_env import Global
from ..core.state import _add_list_state_raw

_LOG_KEY = "_execution_traces"


@dataclass
class WorkflowExecutionEntry:
    """ワークフロー実行の記録"""

    workflow_name: str
    run_id: str
    status: str  # succeeded, failed, paused
    triggered_by_event: str
    timestamp: float
    state_changes: list[dict] = field(default_factory=list)


@dataclass
class ExecutionTrace:
    """client.run()の1回の呼び出しに対応するトレース"""

    trace_id: str
    timestamp: float
    trigger_name: str | None
    workflow_executions: list[WorkflowExecutionEntry] = field(default_factory=list)


class ExecutionTraceRecorder:
    """実行中にトレースデータを記録するレコーダー"""

    def __init__(self, trigger_name: str | None):
        self._trace = ExecutionTrace(
            trace_id=uuid.uuid4().hex,
            timestamp=time.time(),
            trigger_name=trigger_name,
        )
        self._current_state_changes: list[dict] = []

    def record_workflow_execution(
        self,
        workflow_name: str,
        run_id: str,
        status: str,
        triggered_by_event: str,
    ) -> None:
        """ワークフロー実行を記録する"""
        self._trace.workflow_executions.append(
            WorkflowExecutionEntry(
                workflow_name=workflow_name,
                run_id=run_id,
                status=status,
                triggered_by_event=triggered_by_event,
                timestamp=time.time(),
                state_changes=list(self._current_state_changes),
            )
        )
        self._current_state_changes = []

    def record_state_change(
        self,
        state_name: str,
        old_value: Any,
        new_value: Any,
    ) -> None:
        """ステート変更を記録する"""
        self._current_state_changes.append(
            {
                "state_name": state_name,
                "old_value": old_value,
                "new_value": new_value,
            }
        )

    def get_trace(self) -> ExecutionTrace:
        return self._trace


def save_execution_trace(g: Global, trace: ExecutionTrace) -> None:
    """実行トレースを永続化する"""
    _add_list_state_raw(g, _LOG_KEY, asdict(trace), max_length=500)


def _get_execution_traces(g: Global) -> list[dict]:
    """永続化されたトレース一覧を取得する"""
    return g.state.read_state(_LOG_KEY, default=[])
