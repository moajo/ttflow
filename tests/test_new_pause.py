"""中断・再開メカニズムに関するテスト"""

from ttflow import Client, RunContext
from ttflow.core import _enque_event


class TestPauseOnce:
    """pause_onceの基本動作"""

    def test_pause_onceで中断して次回再開(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.log("step1")
            c.pause_once()
            c.log("step2")

        results = client.run("wf")
        assert results[0].status == "paused"
        assert results[0].logs == ["step1"]

        results = client.run()
        assert results[0].status == "succeeded"
        assert results[0].logs == ["step1", "step2"]

    def test_複数のpause_onceを順番に通過(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.log("A")
            c.pause_once()
            c.log("B")
            c.pause_once()
            c.log("C")

        r1 = client.run("wf")
        assert r1[0].status == "paused"
        assert r1[0].logs == ["A"]

        r2 = client.run()
        assert r2[0].status == "paused"
        assert r2[0].logs == ["A", "B"]

        r3 = client.run()
        assert r3[0].status == "succeeded"
        assert r3[0].logs == ["A", "B", "C"]

    def test_ループ内のpause_once(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            for i in range(3):
                c.log(f"iter:{i}")
                c.pause_once()

        # 3回のpause_onceがあるので、4回runする必要がある
        r = client.run("wf")
        assert r[0].status == "paused"
        assert r[0].logs == ["iter:0"]

        r = client.run()
        assert r[0].status == "paused"
        assert r[0].logs == ["iter:0", "iter:1"]

        r = client.run()
        assert r[0].status == "paused"
        assert r[0].logs == ["iter:0", "iter:1", "iter:2"]

        r = client.run()
        assert r[0].status == "succeeded"

    def test_pause後にrun_stateが削除される(self, client: Client):
        """成功したワークフローのrun_stateは削除される"""

        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.pause_once()

        r1 = client.run("wf")
        run_id = r1[0].run_id

        # 中断中はrun_stateが存在する
        key = f"_run_state:{run_id}"
        assert client._global.state.read_state(key, []) != []

        # 再開して完了
        client.run()

        # 完了後はrun_stateがクリアされる
        assert client._global.state.read_state(key, []) == []


class TestWaitEvent:
    """wait_eventの動作"""

    def test_wait_eventで特定イベントまで中断(self, client: Client):
        @client.sideeffect()
        def wait_approval(c: RunContext):
            c.wait_event("approved")

        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.log("waiting")
            wait_approval(c)
            c.log("approved!")

        # 初回: 中断
        r = client.run("wf")
        assert r[0].status == "paused"
        assert r[0].logs == ["waiting"]

        # イベントなしで再実行: まだ中断
        r = client.run()
        assert r[0].status == "paused"

        # approvedイベントを発行して再実行
        _enque_event(client._global, "approved", None)
        r = client.run()
        assert r[0].status == "succeeded"
        assert r[0].logs == ["waiting", "approved!"]

    def test_wait_eventでrun_id固有のイベントを待つ(self, client: Client):
        """各ワークフロー実行が独自のイベントを待つパターン"""

        @client.sideeffect()
        def wait(c: RunContext):
            c.wait_event(f"approve:{c.get_context_data().run_id}")

        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.log("waiting")
            wait(c)
            c.log("done")

        # 2つのワークフローを起動
        r1 = client.run("wf")
        run_id_1 = r1[0].run_id

        r2 = client.run("wf")
        # 新規 + 1つ目の再開 = 2件
        run_id_2 = [r for r in r2 if r.run_id != run_id_1][0].run_id

        # 1つ目だけ承認
        _enque_event(client._global, f"approve:{run_id_1}", None)
        r3 = client.run()
        completed = [r for r in r3 if r.status == "succeeded"]
        paused = [r for r in r3 if r.status == "paused"]
        assert len(completed) == 1
        assert completed[0].run_id == run_id_1
        assert len(paused) == 1
        assert paused[0].run_id == run_id_2


class TestPauseWithSideeffect:
    """中断・再開とsideeffectの組み合わせ"""

    def test_中断前のsideeffectは再開時にスキップ(self, client: Client):
        actual_calls = []

        @client.sideeffect()
        def effect(c: RunContext, label: str):
            actual_calls.append(label)

        @client.workflow()
        def wf(c: RunContext, args: dict):
            effect(c, "A")
            c.pause_once()
            effect(c, "B")
            c.pause_once()
            effect(c, "C")

        client.run("wf")
        assert actual_calls == ["A"]

        client.run()
        assert actual_calls == ["A", "B"]

        client.run()
        assert actual_calls == ["A", "B", "C"]


class TestPauseWithState:
    """中断・再開とstateの組み合わせ"""

    def test_stateを使ったループカウンター(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            while True:
                count = c.get_state("count", 0)
                c.log(f"count={count}")
                c.pause_once()
                c.set_state("count", count + 1)
                if c.get_state("count") > 2:
                    break

        r = client.run("wf")
        assert r[0].logs == ["count=0"]

        r = client.run()
        assert r[0].logs[-1] == "count=1"

        r = client.run()
        assert r[0].logs[-1] == "count=2"

        r = client.run()
        assert r[0].status == "succeeded"


class TestMultiplePausedWorkflows:
    """複数の中断中ワークフローの並行処理"""

    def test_複数ワークフローが独立して中断再開(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.log(f"start:{args['id']}")
            c.pause_once()
            c.log(f"end:{args['id']}")

        # 2つのワークフローを起動
        r1 = client.run("wf", {"id": 1})
        assert r1[0].status == "paused"
        run_id_1 = r1[0].run_id

        r2 = client.run("wf", {"id": 2})
        # 1つ目の再開(succeeded) + 2つ目の新規(paused) = 2件
        assert len(r2) == 2
        completed = [r for r in r2 if r.status == "succeeded"]
        paused = [r for r in r2 if r.status == "paused"]
        assert len(completed) == 1
        assert completed[0].run_id == run_id_1
        assert len(paused) == 1

        # 2つ目も再開
        r3 = client.run()
        assert any(r.status == "succeeded" for r in r3)
