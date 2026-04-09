"""ttflow Webダッシュボード

FastAPIベースの軽量Webダッシュボード。
ワークフローの状態確認・実行履歴の参照・手動トリガーを提供する。
"""

from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from ..core.global_env import Global, Workflow
from ..core.trigger import EventTrigger
from ..system_states.completed import _get_completed_runs_log
from ..system_states.event_log import _get_event_logs
from ..system_states.execution_trace import _get_execution_traces
from ..system_states.logs import _get_logs
from ..ttflow import Client

_STATIC_DIR = Path(__file__).parent / "static"


def _workflow_info(wf: Workflow) -> dict[str, Any]:
    """ワークフロー情報を辞書に変換する"""
    trigger_info: dict[str, Any] = {}
    if isinstance(wf.trigger, EventTrigger):
        trigger_info = {
            "type": "event",
            "event_name": wf.trigger.event_name,
        }
    return {
        "name": wf.name,
        "description": wf.description,
        "trigger": trigger_info,
    }


def _paused_workflows(g: Global) -> list[dict[str, Any]]:
    """中断中のワークフロー一覧を取得する"""
    events_raw = g.state.read_state("_events", default=[])
    paused = []
    for ev in events_raw:
        if ev.get("event_name") == "_pause":
            args = ev.get("args", {})
            paused.append(
                {
                    "workflow_name": args.get("workflow_name"),
                    "run_id": args.get("run_id"),
                    "pause_id": args.get("pause_id"),
                    "timestamp": args.get("timestamp"),
                }
            )
    return paused


def create_app(client: Client) -> FastAPI:
    """ttflow用のFastAPIアプリケーションを生成する

    Args:
        client: ttflowのClientインスタンス

    Returns:
        FastAPIアプリケーション
    """
    app = FastAPI(title="ttflow Dashboard", version="0.1.0")
    g = client._global

    # --- Read-Only API ---

    @app.get("/api/workflows")
    def list_workflows() -> list[dict[str, Any]]:
        """登録済みワークフロー一覧"""
        return [_workflow_info(wf) for wf in g.workflows]

    @app.get("/api/runs")
    def list_runs() -> list[dict]:
        """完了済み実行履歴"""
        return _get_completed_runs_log(g)

    @app.get("/api/runs/{run_id}/logs")
    def get_run_logs(run_id: str) -> list[str]:
        """特定のrun_idのログ"""
        return _get_logs(g, run_id)

    @app.get("/api/events")
    def list_events() -> list[dict]:
        """イベント履歴"""
        return _get_event_logs(g)

    @app.get("/api/state/{key}")
    def get_state(key: str) -> Any:
        """任意のステート値を取得する"""
        value = g.state.read_state(key)
        if value is None:
            raise HTTPException(status_code=404, detail=f"State '{key}' not found")
        return {"key": key, "value": value}

    @app.get("/api/status")
    def get_status() -> dict[str, Any]:
        """システムステータス（中断中ワークフロー・ロック状態）"""
        return {
            "is_locked": g.state.is_locked(),
            "paused_workflows": _paused_workflows(g),
        }

    # --- Visualization API ---

    @app.get("/api/visualization/timeline")
    def get_timeline() -> dict[str, Any]:
        """実行タイムライン

        ワークフロー別に実行履歴をグルーピングし、
        各実行にトリガーイベント情報を付与して返す。
        """
        traces = _get_execution_traces(g)
        runs = _get_completed_runs_log(g)

        # トレースからrun_id→triggered_by_eventのマッピングを構築
        run_trigger_map: dict[str, str] = {}
        for trace in traces:
            for we in trace.get("workflow_executions", []):
                run_trigger_map[we["run_id"]] = we["triggered_by_event"]

        # ワークフロー別にグルーピング
        by_workflow: dict[str, list[dict]] = {}
        for run in runs:
            name = run["workflow_name"]
            entry = {
                **run,
                "triggered_by": run_trigger_map.get(run["run_id"]),
            }
            by_workflow.setdefault(name, []).append(entry)

        return {"workflows": by_workflow}

    @app.get("/api/visualization/event-flow")
    def get_event_flow() -> dict[str, Any]:
        """イベントフロー

        イベント→ワークフローの発火関係を返す。
        静的な登録情報（どのワークフローがどのイベントを待ち受けているか）と、
        実際の実行トレースを組み合わせて返す。
        """
        # 静的な登録情報: イベント名→待ち受けワークフロー名リスト
        event_to_workflows: dict[str, list[str]] = {}
        for wf in g.workflows:
            if isinstance(wf.trigger, EventTrigger):
                event_name = wf.trigger.event_name
                event_to_workflows.setdefault(event_name, []).append(wf.name)

        # トレースから実際の発火履歴を構築
        traces = _get_execution_traces(g)
        recent_by_event: dict[str, list[dict]] = {}
        for trace in traces:
            for we in trace.get("workflow_executions", []):
                event = we["triggered_by_event"]
                recent_by_event.setdefault(event, []).append(
                    {
                        "workflow_name": we["workflow_name"],
                        "run_id": we["run_id"],
                        "status": we["status"],
                        "timestamp": we["timestamp"],
                    }
                )

        # 結合: 登録済みイベント + トレースに出現したイベント
        all_events = set(event_to_workflows.keys()) | set(recent_by_event.keys())
        flows = []
        for event_name in sorted(all_events):
            flows.append(
                {
                    "event_name": event_name,
                    "registered_workflows": event_to_workflows.get(event_name, []),
                    "recent_executions": recent_by_event.get(event_name, []),
                }
            )

        return {"flows": flows}

    @app.get("/api/visualization/state-transitions")
    def get_state_transitions() -> dict[str, Any]:
        """状態遷移

        ワークフローによるステート変更と、それによるstate_triggerの連鎖を返す。
        トレースのstate_changesからステート変更の履歴を構築し、
        state_trigger登録情報と突合して依存関係グラフを生成する。
        """
        # state_trigger登録情報: state名→ワークフロー名リスト
        state_consumers: dict[str, list[str]] = {}
        for wf in g.workflows:
            if isinstance(wf.trigger, EventTrigger):
                event_name = wf.trigger.event_name
                if event_name.startswith("state_changed_"):
                    state_name = event_name[len("state_changed_") :]
                    state_consumers.setdefault(state_name, []).append(wf.name)

        # トレースからステート変更の履歴を構築
        traces = _get_execution_traces(g)
        state_producers: dict[str, set[str]] = {}
        state_change_history: dict[str, list[dict]] = {}
        for trace in traces:
            for we in trace.get("workflow_executions", []):
                for sc in we.get("state_changes", []):
                    state_name = sc["state_name"]
                    state_producers.setdefault(state_name, set()).add(
                        we["workflow_name"]
                    )
                    state_change_history.setdefault(state_name, []).append(
                        {
                            "workflow_name": we["workflow_name"],
                            "old_value": sc["old_value"],
                            "new_value": sc["new_value"],
                            "timestamp": we["timestamp"],
                        }
                    )

        # state_triggerの対象 + 実際に変更されたステートを統合
        all_states = set(state_consumers.keys()) | set(state_producers.keys())
        transitions = []
        for state_name in sorted(all_states):
            transitions.append(
                {
                    "state_name": state_name,
                    "producers": sorted(state_producers.get(state_name, set())),
                    "consumers": state_consumers.get(state_name, []),
                    "recent_changes": state_change_history.get(state_name, []),
                }
            )

        return {"transitions": transitions}

    # --- Trigger API ---

    @app.post("/api/trigger/{trigger_name}")
    def trigger_workflow(trigger_name: str, args: Any = None) -> dict[str, Any]:
        """ワークフローを手動トリガーする"""
        results = client.run(trigger_name, args)
        return {"results": [asdict(r) for r in results]}

    @app.post("/api/resume/{workflow_name}")
    def resume_workflow(workflow_name: str) -> dict[str, Any]:
        """中断中のワークフローを再開する（トリガーなしでrun）"""
        results = client.run()
        return {"results": [asdict(r) for r in results]}

    # --- Dashboard UI ---

    @app.get("/", response_class=HTMLResponse)
    def dashboard():
        """Webダッシュボード"""
        html_path = _STATIC_DIR / "index.html"
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))

    return app
