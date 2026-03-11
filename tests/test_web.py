"""Webダッシュボードのテスト"""

from fastapi.testclient import TestClient

import ttflow
from ttflow.web import create_app


def _create_test_app():
    """テスト用のttflow ClientとFastAPI TestClientを作成する"""
    c = ttflow.setup("onmemory")

    @c.workflow(trigger="run_sample")
    def sample_workflow(ctx):
        ctx.log("hello from sample")
        ctx.set_state("counter", 1)

    @c.workflow(trigger=ttflow.every_trigger())
    def every_workflow(ctx):
        """毎回実行されるワークフロー"""
        ctx.log("every run")

    app = create_app(c)
    return c, TestClient(app)


class TestReadOnlyAPI:
    def test_list_workflows(self):
        _, http = _create_test_app()
        res = http.get("/api/workflows")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 2
        names = {w["name"] for w in data}
        assert "sample_workflow" in names
        assert "every_workflow" in names

    def test_list_workflows_trigger_info(self):
        _, http = _create_test_app()
        data = http.get("/api/workflows").json()
        sample = next(w for w in data if w["name"] == "sample_workflow")
        assert sample["trigger"]["type"] == "event"
        assert sample["trigger"]["event_name"] == "_trigger_run_sample"

    def test_list_workflows_description(self):
        _, http = _create_test_app()
        data = http.get("/api/workflows").json()
        every = next(w for w in data if w["name"] == "every_workflow")
        assert every["description"] == "毎回実行されるワークフロー"

    def test_list_runs_empty(self):
        _, http = _create_test_app()
        res = http.get("/api/runs")
        assert res.status_code == 200
        assert res.json() == []

    def test_list_events_empty(self):
        _, http = _create_test_app()
        res = http.get("/api/events")
        assert res.status_code == 200
        assert res.json() == []

    def test_get_state_not_found(self):
        _, http = _create_test_app()
        res = http.get("/api/state/nonexistent")
        assert res.status_code == 404

    def test_status(self):
        _, http = _create_test_app()
        res = http.get("/api/status")
        assert res.status_code == 200
        data = res.json()
        assert data["is_locked"] is False
        assert data["paused_workflows"] == []

    def test_run_logs_empty(self):
        _, http = _create_test_app()
        res = http.get("/api/runs/nonexistent/logs")
        assert res.status_code == 200
        assert res.json() == []


class TestTriggerAPI:
    def test_trigger_workflow(self):
        _, http = _create_test_app()
        res = http.post("/api/trigger/run_sample")
        assert res.status_code == 200
        data = res.json()
        assert "results" in data
        names = {r["workflow_name"] for r in data["results"]}
        assert "sample_workflow" in names

    def test_trigger_then_check_runs(self):
        _, http = _create_test_app()
        http.post("/api/trigger/run_sample")
        res = http.get("/api/runs")
        runs = res.json()
        assert len(runs) > 0
        assert any(r["workflow_name"] == "sample_workflow" for r in runs)

    def test_trigger_then_check_state(self):
        _, http = _create_test_app()
        http.post("/api/trigger/run_sample")
        res = http.get("/api/state/counter")
        assert res.status_code == 200
        data = res.json()
        assert data["key"] == "counter"
        assert data["value"] == 1

    def test_trigger_then_check_logs(self):
        _, http = _create_test_app()
        trigger_res = http.post("/api/trigger/run_sample")
        results = trigger_res.json()["results"]
        sample_result = next(
            r for r in results if r["workflow_name"] == "sample_workflow"
        )
        run_id = sample_result["run_id"]

        res = http.get(f"/api/runs/{run_id}/logs")
        logs = res.json()
        assert "hello from sample" in logs

    def test_resume(self):
        _, http = _create_test_app()
        res = http.post("/api/resume/sample_workflow")
        assert res.status_code == 200


class TestPausedWorkflows:
    def test_paused_workflow_appears_in_status(self):
        c = ttflow.setup("onmemory")

        @c.workflow(trigger="start_pausable")
        def pausable(ctx):
            ctx.pause_once()
            ctx.log("resumed!")

        app = create_app(c)
        http = TestClient(app)

        # ワークフローを中断させる
        http.post("/api/trigger/start_pausable")

        # ステータスに中断中ワークフローが表示される
        status = http.get("/api/status").json()
        paused = status["paused_workflows"]
        assert len(paused) == 1
        assert paused[0]["workflow_name"] == "pausable"


class TestDashboard:
    def test_dashboard_html(self):
        _, http = _create_test_app()
        res = http.get("/")
        assert res.status_code == 200
        assert "ttflow Dashboard" in res.text
        assert "text/html" in res.headers["content-type"]
