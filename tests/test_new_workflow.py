"""ワークフローの登録・実行・トリガーに関するテスト"""

import pytest

from ttflow import Client, RunContext, event_trigger, every_trigger, state_trigger
from ttflow.core import _enque_event
from ttflow.errors import WorkflowDirectCallError


# --- トリガーの指定方法 ---


class TestTriggerVariations:
    """@workflow() のトリガー指定方法のバリエーション"""

    def test_トリガー省略時は関数名がトリガーになる(self, client: Client):
        @client.workflow()
        def my_workflow(c: RunContext, args: dict):
            c.log("executed")

        results = client.run("my_workflow")
        assert len(results) == 1
        assert results[0].status == "succeeded"
        assert results[0].logs == ["executed"]

    def test_文字列トリガー(self, client: Client):
        @client.workflow(trigger="my_trigger")
        def wf(c: RunContext, args: dict):
            c.log("executed")

        results = client.run("my_trigger")
        assert len(results) == 1
        assert results[0].status == "succeeded"

    def test_event_triggerオブジェクト(self, client: Client):
        @client.workflow(trigger=event_trigger("custom_event"))
        def wf(c: RunContext, args: dict):
            c.log("executed")

        _enque_event(client._global, "custom_event", {"key": "value"})
        results = client.run()
        assert len(results) == 1
        assert results[0].status == "succeeded"

    def test_every_trigger(self, client: Client):
        @client.workflow(trigger=every_trigger())
        def wf(c: RunContext, args: dict):
            c.log("every")

        results = client.run()
        assert any(r.workflow_name == "wf" and r.status == "succeeded" for r in results)

    def test_state_trigger(self, client: Client):
        @client.workflow()
        def setter(c: RunContext, args: dict):
            c.set_state("watched_value", 42)

        @client.workflow(trigger=state_trigger("watched_value"))
        def watcher(c: RunContext, args: dict):
            c.log("state changed")

        results = client.run("setter")
        watcher_results = [r for r in results if r.workflow_name == "watcher"]
        assert len(watcher_results) == 1
        assert watcher_results[0].status == "succeeded"


# --- ワークフロー引数 ---


class TestWorkflowArgs:
    """ワークフロー関数の引数に関するテスト"""

    def test_argsあり(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.log(f"got: {args['key']}")

        results = client.run("wf", {"key": "hello"})
        assert results[0].logs == ["got: hello"]

    def test_args省略(self, client: Client):
        """ワークフロー関数の第2引数を省略できる"""

        @client.workflow()
        def wf(c: RunContext):
            c.log("no args")

        results = client.run("wf")
        assert results[0].status == "succeeded"
        assert results[0].logs == ["no args"]

    def test_argsにNoneを渡す(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.log(f"args is {args}")

        results = client.run("wf", None)
        assert results[0].status == "succeeded"


# --- ワークフロー実行結果 ---


class TestWorkflowRunResult:
    """WorkflowRunResultの内容に関するテスト"""

    def test_成功時のresult(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.log("done")

        results = client.run("wf")
        r = results[0]
        assert r.workflow_name == "wf"
        assert r.run_id is not None
        assert r.status == "succeeded"
        assert r.error_message is None
        assert r.logs == ["done"]

    def test_失敗時のresult(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            raise ValueError("something went wrong")

        results = client.run("wf")
        r = results[0]
        assert r.status == "failed"
        assert "ValueError" in r.error_message
        assert "something went wrong" in r.error_message

    def test_中断時のresult(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.log("before pause")
            c.pause_once()
            c.log("after pause")

        results = client.run("wf")
        r = results[0]
        assert r.status == "paused"
        assert r.error_message is None
        assert r.logs == ["before pause"]


# --- ワークフローの直接呼び出し禁止 ---


class TestDirectCallPrevention:
    def test_workflow関数を直接呼び出すとエラー(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            pass

        with pytest.raises(WorkflowDirectCallError):
            wf(None, None)

    def test_workflow内から別workflowを直接呼び出すとfailed(self, client: Client):
        @client.workflow()
        def wf1(c: RunContext, args: dict):
            wf2(c)

        @client.workflow()
        def wf2(c: RunContext, args: dict):
            pass

        results = client.run("wf1")
        assert results[0].status == "failed"
        assert "WorkflowDirectCallError" in results[0].error_message


# --- イベント連鎖 ---


class TestEventChaining:
    """ワークフローからイベントを発火して別ワークフローを起動"""

    def test_event発火による連鎖(self, client: Client):
        """c.event()で発火したイベントは同じrun内で処理される"""

        @client.workflow()
        def wf1(c: RunContext, args: dict):
            c.log("wf1")
            c.event("next_event", {"from": "wf1"})

        @client.workflow(trigger=event_trigger("next_event"))
        def wf2(c: RunContext, args: dict):
            c.log(f"wf2: {args['from']}")

        # wf1を実行するとnext_eventが発火され、同じrun内でwf2も実行される
        results = client.run("wf1")
        wf1_results = [r for r in results if r.workflow_name == "wf1"]
        wf2_results = [r for r in results if r.workflow_name == "wf2"]
        assert len(wf1_results) == 1
        assert len(wf2_results) == 1
        assert wf2_results[0].logs == ["wf2: wf1"]

    def test_同じイベントで複数ワークフローが起動(self, client: Client):
        @client.workflow(trigger=event_trigger("shared_event"))
        def wf1(c: RunContext, args: dict):
            c.log("wf1")

        @client.workflow(trigger=event_trigger("shared_event"))
        def wf2(c: RunContext, args: dict):
            c.log("wf2")

        _enque_event(client._global, "shared_event", None)
        results = client.run()
        names = {r.workflow_name for r in results}
        assert "wf1" in names
        assert "wf2" in names


# --- トリガーなしのrun ---


class TestRunWithoutTrigger:
    def test_トリガーなしで中断中ワークフローがない場合(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.log("done")

        results = client.run()
        # ワークフローは実行されない（workflows_changedイベントがなければ）
        wf_results = [r for r in results if r.workflow_name == "wf"]
        assert len(wf_results) == 0


# --- ワークフローハッシュ変更検知 ---


class TestWorkflowHashChange:
    def test_初回実行でworkflows_changedイベントが発火(self, client: Client):
        @client.workflow(trigger=event_trigger("workflows_changed"))
        def on_deploy(c: RunContext, args: dict):
            c.log("deployed")

        results = client.run()
        deploy_results = [r for r in results if r.workflow_name == "on_deploy"]
        assert len(deploy_results) == 1

    def test_2回目以降はworkflows_changedが発火しない(self, client: Client):
        call_count = []

        @client.workflow(trigger=event_trigger("workflows_changed"))
        def on_deploy(c: RunContext, args: dict):
            call_count.append(1)

        client.run()
        assert len(call_count) == 1

        client.run()
        # 2回目は同じハッシュなので発火しない
        assert len(call_count) == 1


# --- list_registered_workflows ---


class TestListRegisteredWorkflows:
    def test_登録されたワークフローを取得(self, client: Client):
        @client.workflow()
        def wf1(c: RunContext, args: dict):
            pass

        @client.workflow()
        def wf2(c: RunContext, args: dict):
            pass

        workflows = client.list_registered_workflows()
        names = [w.f.__name__ for w in workflows]
        assert "wf1" in names
        assert "wf2" in names
