"""完了ログ・イベントログ・ワークフローログに関するテスト"""

from ttflow import Client, RunContext
from ttflow.system_states.completed import _get_completed_runs_log
from ttflow.system_states.event_log import _get_event_logs


class TestCompletedRunsLog:
    """完了ログの記録"""

    def test_成功したワークフローが記録される(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            pass

        client.run("wf")
        logs = _get_completed_runs_log(client._global)
        assert len(logs) == 1
        assert logs[0]["status"] == "success"
        assert logs[0]["workflow_name"] == "wf"

    def test_失敗したワークフローが記録される(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            raise RuntimeError("error")

        client.run("wf")
        logs = _get_completed_runs_log(client._global)
        assert len(logs) == 1
        assert logs[0]["status"] == "failed"

    def test_中断中のワークフローは完了ログに記録されない(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.pause_once()

        client.run("wf")
        logs = _get_completed_runs_log(client._global)
        assert len(logs) == 0

    def test_複数ワークフローの完了ログが蓄積される(self, client: Client):
        @client.workflow()
        def wf1(c: RunContext, args: dict):
            pass

        @client.workflow()
        def wf2(c: RunContext, args: dict):
            pass

        client.run("wf1")
        client.run("wf2")
        logs = _get_completed_runs_log(client._global)
        names = [l["workflow_name"] for l in logs]
        assert "wf1" in names
        assert "wf2" in names


class TestEventLog:
    """イベントログの記録"""

    def test_ユーザイベントがログに記録される(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            pass

        client.run("wf", {"key": "val"})
        logs = _get_event_logs(client._global)
        # _trigger_wfはシステムイベントなのでログには記録されない
        # workflows_changedは記録される
        event_names = [l["event_name"] for l in logs]
        assert "workflows_changed" in event_names

    def test_システムイベントはログに記録されない(self, client: Client):
        """_で始まるイベントはevent logに記録されない"""

        @client.workflow()
        def wf(c: RunContext, args: dict):
            pass

        client.run("wf")
        logs = _get_event_logs(client._global)
        for l in logs:
            assert not l["event_name"].startswith("_")


class TestWorkflowLogs:
    """ワークフロー内のログ"""

    def test_logメッセージが記録される(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.log("message1")
            c.log("message2")

        results = client.run("wf")
        assert results[0].logs == ["message1", "message2"]

    def test_logは再実行時に重複しない(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.log("before")
            c.pause_once()
            c.log("after")

        client.run("wf")
        results = client.run()
        # 再開時に"before"のlogは再実行されない
        assert results[0].logs == ["before", "after"]

    def test_異なるワークフローのログは独立(self, client: Client):
        @client.workflow()
        def wf1(c: RunContext, args: dict):
            c.log("from wf1")

        @client.workflow()
        def wf2(c: RunContext, args: dict):
            c.log("from wf2")

        client.run("wf1")
        results = client.run("wf2")
        wf2_results = [r for r in results if r.workflow_name == "wf2"]
        assert wf2_results[0].logs == ["from wf2"]
