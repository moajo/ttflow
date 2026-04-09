import json

from ttflow import Client, RunContext
from ttflow.core import _enque_event
from ttflow.core.event import _read_events_from_state
from ttflow.system_states.logs import _get_logs

from .utils import create_client_for_test


def _define_workflow_for_test(ttflow: Client):
    @ttflow.workflow(trigger="デプロイCD")
    def CI(c: RunContext, args: dict):
        count = c.get_state("CD開始回数")
        if count is None:
            count = 0
        c.set_state("CD開始回数", count + 1)
        hoge = args["値"]
        notification_to_app(c, f"{count}回目のCDを開始します: {hoge}")
        承認待ち(c)

        count = c.get_state("CD完了回数")
        if count is None:
            count = 0
        c.set_state("CD完了回数", count + 1)
        notification_to_app(c, "CD完了")

    @ttflow.sideeffect()
    def notification_to_app(c: RunContext, message: str):
        # ここでアプリに通知を送信する
        c.log(f"通知ダミー: {message}")

    @ttflow.sideeffect()
    def 承認待ち(c: RunContext):
        notification_to_app(c, f"承認事項がが1件あります:{c.get_context_data().run_id}")
        c.wait_event(f"承認:{c.get_context_data().run_id}")
        c.log("承認されました")


def test_中断機能が正しく動くこと(client: Client):
    _define_workflow_for_test(client)
    s = client._global.state

    assert s.read_state("CD開始回数") is None
    assert s.read_state("CD完了回数") is None

    results = client.run("デプロイCD", {"値": "hoge"})
    assert len(results) == 1
    assert results[0].workflow_name == "CI"
    assert results[0].status == "paused"
    assert len(results[0].logs) == 2
    assert results[0].logs == [
        "通知ダミー: 0回目のCDを開始します: hoge",
        f"通知ダミー: 承認事項がが1件あります:{results[0].run_id}",
    ]

    paused_event = _read_events_from_state(client._global)
    assert len(client._global.events_for_next_run) == 0, "commitされてるので0"
    assert len(paused_event) == 1
    assert s.read_state("CD開始回数") == 1
    assert s.read_state("CD完了回数") is None
    run_id = paused_event[0].args["run_id"]
    assert _get_logs(client._global, run_id) == [
        "通知ダミー: 0回目のCDを開始します: hoge",
        f"通知ダミー: 承認事項がが1件あります:{run_id}",
    ]

    current = json.loads(
        json.dumps(s.cache, indent=2, sort_keys=True, ensure_ascii=False)
    )
    current["_events"] = []  # paused eventは更新されるので無視する
    results = client.run()
    assert len(results) == 1
    assert results[0].workflow_name == "CI"
    assert results[0].status == "paused"
    assert len(results[0].logs) == 2
    assert results[0].logs == [
        "通知ダミー: 0回目のCDを開始します: hoge",
        f"通知ダミー: 承認事項がが1件あります:{results[0].run_id}",
    ]
    paused_event = _read_events_from_state(client._global)
    assert len(client._global.events_for_next_run) == 0, "commitされてるので0"
    assert len(paused_event) == 1
    new_state = json.loads(
        json.dumps(s.cache, indent=2, sort_keys=True, ensure_ascii=False)
    )
    new_state["_events"] = []  # paused eventは更新されるので無視する
    assert new_state == current, "stateが変化していないこと"
    assert _get_logs(client._global, run_id) == [
        "通知ダミー: 0回目のCDを開始します: hoge",
        f"通知ダミー: 承認事項がが1件あります:{run_id}",
    ]

    # 承認する
    _enque_event(client._global, f"承認:{run_id}", None)
    results = client.run()
    assert len(results) == 1
    assert results[0].workflow_name == "CI"
    assert results[0].status == "succeeded"
    assert len(results[0].logs) == 4
    assert results[0].logs == [
        "通知ダミー: 0回目のCDを開始します: hoge",
        f"通知ダミー: 承認事項がが1件あります:{results[0].run_id}",
        "承認されました",
        "通知ダミー: CD完了",
    ]

    assert len(s.read_state("paused_workflows", default=[])) == 0
    assert s.read_state("CD開始回数") == 1
    assert s.read_state("CD完了回数") == 1
    assert _get_logs(client._global, run_id) == [
        "通知ダミー: 0回目のCDを開始します: hoge",
        f"通知ダミー: 承認事項がが1件あります:{run_id}",
        "承認されました",
        "通知ダミー: CD完了",
    ]


def test_中断イベントは永続化される():
    client = create_client_for_test()
    _define_workflow_for_test(client)

    client.run("デプロイCD", {"値": "hoge"})
    assert len(client._global.events_for_next_run) == 0, "commitされてるので0"
    paused_event = _read_events_from_state(client._global)
    assert len(paused_event) == 1

    # reloadする
    client._global.purge_events()
    _define_workflow_for_test(client)
    client.run()
    assert len(client._global.events_for_next_run) == 0, "commitされてるので0"
    paused_event = _read_events_from_state(client._global)
    assert len(paused_event) == 1
    run_id = paused_event[0].args["run_id"]

    # 承認する
    _enque_event(client._global, f"承認:{run_id}", None)
    client.run()
    assert client._global.state.read_state("CD開始回数") == 1
    assert client._global.state.read_state("CD完了回数") == 1
    assert _get_logs(client._global, run_id) == [
        "通知ダミー: 0回目のCDを開始します: hoge",
        f"通知ダミー: 承認事項がが1件あります:{run_id}",
        "承認されました",
        "通知ダミー: CD完了",
    ]


def test_中断機能が正しく動くこと_2重実行ケース(client: Client):
    """中断中のワークフローがある状態で同じトリガーが再度発火した場合、
    それぞれ独立したrun_idで並行して動作すること"""
    _define_workflow_for_test(client)
    s = client._global.state

    # 1回目のトリガー → 中断する
    results1 = client.run("デプロイCD", {"値": "first"})
    assert len(results1) == 1
    assert results1[0].status == "paused"
    run_id_1 = results1[0].run_id

    # 2回目のトリガー → 1回目が中断したまま再度トリガー
    results2 = client.run("デプロイCD", {"値": "second"})
    # 新規トリガーが先に処理され、その後中断再開が処理される = 2件
    assert len(results2) == 2
    # 新規トリガーによる2回目の実行（中断）
    assert results2[0].status == "paused"
    run_id_2 = results2[0].run_id
    assert run_id_1 != run_id_2
    # 1回目の再開（承認イベントがないのでまた中断）
    assert results2[1].status == "paused"
    assert results2[1].run_id == run_id_1

    # CD開始回数: 1回目で1に設定済み（再開時はスキップ）、2回目で2に設定
    assert s.read_state("CD開始回数") == 2

    # 1回目を承認
    _enque_event(client._global, f"承認:{run_id_1}", None)
    results3 = client.run()
    # 1回目が完了、2回目は再開するがまた中断 = 2件
    assert len(results3) == 2
    completed = [r for r in results3 if r.status == "succeeded"]
    paused = [r for r in results3 if r.status == "paused"]
    assert len(completed) == 1
    assert completed[0].run_id == run_id_1
    assert len(paused) == 1
    assert paused[0].run_id == run_id_2

    assert s.read_state("CD完了回数") == 1

    # 2回目を承認
    _enque_event(client._global, f"承認:{run_id_2}", None)
    results4 = client.run()
    completed = [r for r in results4 if r.status == "succeeded"]
    assert len(completed) == 1
    assert completed[0].run_id == run_id_2

    assert s.read_state("CD完了回数") == 2
