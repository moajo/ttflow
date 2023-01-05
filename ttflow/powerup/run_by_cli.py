from typing import Any, Optional

import fire
from ttflow import Client, WorkflowRunResult


def run(client: Client):
    def _internal(trigger_name: Optional[str] = None, args: Any = None):
        results = client.run(trigger_name, args)
        _print_workflow_results(results)

    return _internal


def _print_workflow_results(results: list[WorkflowRunResult]):
    print()
    print("---------RUN SUMMARY---------")
    print(f"{len(results)}件のワークフローが実行されました")
    for i, result in enumerate(results):
        print(f"\t{i+1}件目")
        print(f"\t  ワークフロー名: {result.workflow_name}")
        print(f"\t  run_id: {result.run_id}")
        print(f"\t  状態: {result.status}")
        print("\t  ログ:")
        for log in result.logs:
            print(f"\t    - {log}")


def clear_state(client: Client):
    def _internal():
        client._global.state.clear_state()

    return _internal


def run_by_cli(client: Client, *, enabled_dangerous_clear_state_command=False):
    opts: dict[str, Any] = {
        "run": run(client),
    }
    if enabled_dangerous_clear_state_command:
        opts["clear_state"] = clear_state(client)
    fire.Fire(opts)
