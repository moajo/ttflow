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
