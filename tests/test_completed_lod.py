from dataclasses import asdict
import json

from ttflow import Client, RunContext
from ttflow.system_states.completed import get_completed_runs_log


def test_完了ログを取れること(client: Client):
    ttflow = client

    @ttflow.workflow()
    def action(c: RunContext, args: dict):
        logs = get_completed_runs_log(c._global, c.get_context_data())
        c.log(json.dumps([asdict(log) for log in logs]))
        return 7

    results = client.run("action")
    assert len(results[0].logs) == 1
    assert json.loads(results[0].logs[0]) == []

    results = client.run("action")
    assert len(results[0].logs) == 1
    log = json.loads(results[0].logs[0])[0]
    assert log["status"] == "success"
    assert log["workflow_name"] == "action"
