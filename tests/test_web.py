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


class TestVisualizationTimeline:
    """GET /api/visualization/timeline のテスト"""

    def test_timeline_empty(self):
        _, http = _create_test_app()
        res = http.get("/api/visualization/timeline")
        assert res.status_code == 200
        data = res.json()
        assert data["workflows"] == {}

    def test_timeline_after_trigger(self):
        """トリガー実行後、タイムラインにワークフローが現れる"""
        _, http = _create_test_app()
        http.post("/api/trigger/run_sample")

        res = http.get("/api/visualization/timeline")
        data = res.json()
        assert "sample_workflow" in data["workflows"]
        runs = data["workflows"]["sample_workflow"]
        assert len(runs) >= 1
        assert runs[0]["status"] == "success"

    def test_timeline_has_triggered_by(self):
        """タイムラインの各実行にtriggered_by情報が含まれる"""
        _, http = _create_test_app()
        http.post("/api/trigger/run_sample")

        res = http.get("/api/visualization/timeline")
        data = res.json()
        runs = data["workflows"]["sample_workflow"]
        # トレース記録が実装されていればtriggered_byがある
        assert "triggered_by" in runs[0]

    def test_timeline_multiple_workflows(self):
        """複数ワークフローの実行がそれぞれグルーピングされる"""
        _, http = _create_test_app()
        # run_sampleトリガーで sample_workflow + every_workflow が両方実行される
        http.post("/api/trigger/run_sample")

        res = http.get("/api/visualization/timeline")
        data = res.json()
        assert "sample_workflow" in data["workflows"]
        assert "every_workflow" in data["workflows"]


class TestVisualizationEventFlow:
    """GET /api/visualization/event-flow のテスト"""

    def test_event_flow_static_registration(self):
        """ワークフロー登録のみ（実行なし）でも静的な登録情報が返る"""
        _, http = _create_test_app()
        res = http.get("/api/visualization/event-flow")
        assert res.status_code == 200
        data = res.json()
        flows = data["flows"]
        # sample_workflowのトリガーイベントが含まれる
        event_names = {f["event_name"] for f in flows}
        assert "_trigger_run_sample" in event_names

        sample_flow = next(f for f in flows if f["event_name"] == "_trigger_run_sample")
        assert "sample_workflow" in sample_flow["registered_workflows"]

    def test_event_flow_with_executions(self):
        """実行後にrecent_executionsが含まれる"""
        _, http = _create_test_app()
        http.post("/api/trigger/run_sample")

        res = http.get("/api/visualization/event-flow")
        data = res.json()
        sample_flow = next(
            f for f in data["flows"] if f["event_name"] == "_trigger_run_sample"
        )
        # トレース記録が実装されていれば実行履歴がある
        assert isinstance(sample_flow["recent_executions"], list)

    def test_event_flow_includes_every_trigger(self):
        """every_triggerのイベントも含まれる"""
        _, http = _create_test_app()
        res = http.get("/api/visualization/event-flow")
        data = res.json()
        event_names = {f["event_name"] for f in data["flows"]}
        assert "_every" in event_names


class TestVisualizationStateTransitions:
    """GET /api/visualization/state-transitions のテスト"""

    def test_state_transitions_empty(self):
        _, http = _create_test_app()
        res = http.get("/api/visualization/state-transitions")
        assert res.status_code == 200
        data = res.json()
        assert data["transitions"] == []

    def test_state_transitions_with_state_trigger(self):
        """state_triggerを使ったワークフロー連鎖が検出される"""
        c = ttflow.setup("onmemory")

        @c.workflow(trigger="start")
        def producer(ctx):
            ctx.set_state("counter", 1)

        @c.workflow(trigger=ttflow.state_trigger("counter"))
        def consumer(ctx):
            ctx.log("counter changed!")

        app = create_app(c)
        http = TestClient(app)

        # producerを実行 → counterが変更 → consumerが発火
        http.post("/api/trigger/start")

        res = http.get("/api/visualization/state-transitions")
        data = res.json()
        transitions = data["transitions"]

        # counterの遷移が検出される
        counter_t = next((t for t in transitions if t["state_name"] == "counter"), None)
        assert counter_t is not None
        assert "consumer" in counter_t["consumers"]

    def test_state_transitions_producers_from_trace(self):
        """トレースからproducers（ステートを変更したワークフロー）が分かる"""
        c = ttflow.setup("onmemory")

        @c.workflow(trigger="start")
        def writer(ctx):
            ctx.set_state("my_state", "hello")

        @c.workflow(trigger=ttflow.state_trigger("my_state"))
        def reader(ctx):
            pass

        app = create_app(c)
        http = TestClient(app)

        http.post("/api/trigger/start")

        res = http.get("/api/visualization/state-transitions")
        data = res.json()
        transitions = data["transitions"]

        my_state_t = next(
            (t for t in transitions if t["state_name"] == "my_state"), None
        )
        assert my_state_t is not None
        assert "reader" in my_state_t["consumers"]


class TestVisualizationWithTraceRecording:
    """トレース記録が正しく動作することを検証するテスト

    ExecutionTraceRecorderがclient.run()に組み込まれた後にpassする。
    """

    def test_timeline_triggered_by_is_populated(self):
        """triggered_byにイベント名が記録される"""
        _, http = _create_test_app()
        http.post("/api/trigger/run_sample")

        data = http.get("/api/visualization/timeline").json()
        runs = data["workflows"]["sample_workflow"]
        assert runs[0]["triggered_by"] == "_trigger_run_sample"

    def test_event_flow_recent_executions_populated(self):
        """実行後にrecent_executionsにワークフロー実行が記録される"""
        _, http = _create_test_app()
        http.post("/api/trigger/run_sample")

        data = http.get("/api/visualization/event-flow").json()
        sample_flow = next(
            f for f in data["flows"] if f["event_name"] == "_trigger_run_sample"
        )
        assert len(sample_flow["recent_executions"]) >= 1
        assert sample_flow["recent_executions"][0]["workflow_name"] == "sample_workflow"
        assert sample_flow["recent_executions"][0]["status"] == "succeeded"

    def test_state_transitions_producers_populated(self):
        """ステートを変更したワークフローがproducersに記録される"""
        c = ttflow.setup("onmemory")

        @c.workflow(trigger="start")
        def writer(ctx):
            ctx.set_state("my_state", "hello")

        @c.workflow(trigger=ttflow.state_trigger("my_state"))
        def reader(ctx):
            pass

        app = create_app(c)
        http = TestClient(app)
        http.post("/api/trigger/start")

        data = http.get("/api/visualization/state-transitions").json()
        my_state_t = next(
            t for t in data["transitions"] if t["state_name"] == "my_state"
        )
        assert "writer" in my_state_t["producers"]
        assert len(my_state_t["recent_changes"]) >= 1
        assert my_state_t["recent_changes"][0]["new_value"] == "hello"

    def test_event_flow_chain(self):
        """ワークフローA → event → ワークフローBの連鎖がevent-flowで追跡できる"""
        c = ttflow.setup("onmemory")

        @c.workflow(trigger="start")
        def step1(ctx):
            ctx.event("next_step", {"data": 42})

        @c.workflow(trigger=ttflow.event_trigger("next_step"))
        def step2(ctx, args):
            ctx.set_state("result", args["data"])

        app = create_app(c)
        http = TestClient(app)
        http.post("/api/trigger/start")

        data = http.get("/api/visualization/event-flow").json()
        next_flow = next(
            (f for f in data["flows"] if f["event_name"] == "next_step"),
            None,
        )
        assert next_flow is not None
        assert "step2" in next_flow["registered_workflows"]
        assert len(next_flow["recent_executions"]) >= 1
        assert next_flow["recent_executions"][0]["workflow_name"] == "step2"


class TestDashboard:
    def test_dashboard_html(self):
        _, http = _create_test_app()
        res = http.get("/")
        assert res.status_code == 200
        assert "ttflow Dashboard" in res.text
        assert "text/html" in res.headers["content-type"]
