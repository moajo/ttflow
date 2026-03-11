"""asyncワークフローに関するテスト"""

from ttflow import Client, RunContext, event_trigger

# --- 基本的なasyncワークフロー ---


class TestAsyncWorkflowBasic:
    """asyncワークフローの基本動作"""

    def test_asyncワークフローが実行できる(self, client: Client):
        @client.workflow()
        async def wf(c: RunContext, args: dict):
            c.log("async executed")

        results = client.run("wf")
        assert results[0].status == "succeeded"
        assert results[0].logs == ["async executed"]

    def test_asyncワークフローでargsを受け取れる(self, client: Client):
        @client.workflow()
        async def wf(c: RunContext, args: dict):
            c.log(f"got: {args['key']}")

        results = client.run("wf", {"key": "hello"})
        assert results[0].logs == ["got: hello"]

    def test_asyncワークフローでargs省略(self, client: Client):
        @client.workflow()
        async def wf(c: RunContext):
            c.log("no args")

        results = client.run("wf")
        assert results[0].status == "succeeded"
        assert results[0].logs == ["no args"]

    def test_asyncワークフローの例外はfailedになる(self, client: Client):
        @client.workflow()
        async def wf(c: RunContext, args: dict):
            raise ValueError("async boom")

        results = client.run("wf")
        assert results[0].status == "failed"
        assert results[0].error_message is not None
        assert "ValueError" in results[0].error_message
        assert "async boom" in results[0].error_message

    def test_syncとasyncのワークフローが混在できる(self, client: Client):
        @client.workflow()
        def sync_wf(c: RunContext, args: dict):
            c.log("sync")
            c.event("next", None)

        @client.workflow(trigger=event_trigger("next"))
        async def async_wf(c: RunContext, args: dict):
            c.log("async")

        results = client.run("sync_wf")
        sync_results = [r for r in results if r.workflow_name == "sync_wf"]
        async_results = [r for r in results if r.workflow_name == "async_wf"]
        assert sync_results[0].status == "succeeded"
        assert async_results[0].status == "succeeded"
        assert async_results[0].logs == ["async"]


# --- asyncワークフローでのstate操作 ---


class TestAsyncWorkflowState:
    """asyncワークフロー内でのstate操作（syncメソッドのまま）"""

    def test_asyncワークフローでget_setstate(self, client: Client):
        @client.workflow()
        async def wf(c: RunContext, args: dict):
            c.set_state("key", "value")
            val = c.get_state("key")
            c.log(f"state={val}")

        results = client.run("wf")
        assert results[0].status == "succeeded"
        assert results[0].logs == ["state=value"]

    def test_asyncワークフローでadd_list_state(self, client: Client):
        @client.workflow()
        async def wf(c: RunContext, args: dict):
            c.add_list_state("items", "a")
            c.add_list_state("items", "b")
            c.log(f"items={c.get_state('items')}")

        results = client.run("wf")
        assert results[0].status == "succeeded"


# --- asyncワークフローでのpause/resume ---


class TestAsyncWorkflowPause:
    """asyncワークフローの中断・再開"""

    def test_asyncワークフローでpause_once(self, client: Client):
        @client.workflow()
        async def wf(c: RunContext, args: dict):
            c.log("step1")
            c.pause_once()
            c.log("step2")

        results = client.run("wf")
        assert results[0].status == "paused"
        assert results[0].logs == ["step1"]

        results = client.run()
        assert results[0].status == "succeeded"
        assert results[0].logs == ["step1", "step2"]

    def test_asyncワークフローで複数pause(self, client: Client):
        @client.workflow()
        async def wf(c: RunContext, args: dict):
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

    def test_asyncワークフローでループ内pause(self, client: Client):
        @client.workflow()
        async def wf(c: RunContext, args: dict):
            for i in range(3):
                c.log(f"iter:{i}")
                c.pause_once()

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


# --- asyncワークフローでのsideeffect ---


class TestAsyncWorkflowWithSyncSideeffect:
    """asyncワークフローからsync sideeffectを呼ぶ"""

    def test_asyncワークフローからsync_sideeffectを呼べる(self, client: Client):
        call_log = []

        @client.sideeffect()
        def effect(c: RunContext, label: str):
            call_log.append(label)

        @client.workflow()
        async def wf(c: RunContext, args: dict):
            effect(c, "hello")
            c.log("done")

        results = client.run("wf")
        assert results[0].status == "succeeded"
        assert call_log == ["hello"]

    def test_asyncワークフローでsideeffectとpauseの組み合わせ(self, client: Client):
        call_log = []

        @client.sideeffect()
        def effect(c: RunContext, label: str):
            call_log.append(label)

        @client.workflow()
        async def wf(c: RunContext, args: dict):
            effect(c, "before")
            c.pause_once()
            effect(c, "after")

        client.run("wf")
        assert call_log == ["before"]

        client.run()
        assert call_log == ["before", "after"]


class TestAsyncSideeffect:
    """async sideeffectの動作"""

    def test_async_sideeffectが実行できる(self, client: Client):
        call_log = []

        @client.sideeffect()
        async def effect(c: RunContext):
            call_log.append("called")
            return 42

        @client.workflow()
        async def wf(c: RunContext, args: dict):
            val = await effect(c)
            c.log(f"result={val}")

        results = client.run("wf")
        assert results[0].status == "succeeded"
        assert results[0].logs == ["result=42"]
        assert call_log == ["called"]

    def test_async_sideeffectの戻り値がキャッシュされる(self, client: Client):
        counter = [0]

        @client.sideeffect()
        async def get_value(c: RunContext) -> int:
            counter[0] += 1
            return counter[0]

        @client.workflow()
        async def wf(c: RunContext, args: dict):
            val = await get_value(c)
            c.log(f"value={val}")
            c.pause_once()
            val2 = await get_value(c)
            c.log(f"value2={val2}")

        client.run("wf")
        results = client.run()
        assert results[0].status == "succeeded"
        # 再開後のget_valueは別トークンなのでcounter[0]は2
        assert results[0].logs[-1] == "value2=2"

    def test_async_sideeffectとpauseでスキップされる(self, client: Client):
        call_log = []

        @client.sideeffect()
        async def effect(c: RunContext, label: str):
            call_log.append(label)

        @client.workflow()
        async def wf(c: RunContext, args: dict):
            await effect(c, "A")
            c.pause_once()
            await effect(c, "B")

        client.run("wf")
        assert call_log == ["A"]

        client.run()
        assert call_log == ["A", "B"]


class TestAsyncSideeffectFromSyncWorkflow:
    """syncワークフローからasync sideeffectを呼ぶことは禁止"""

    def test_syncワークフローからasync_sideeffectを呼ぶとエラー(self, client: Client):
        @client.sideeffect()
        async def async_effect(c: RunContext):
            return 42

        @client.workflow()
        def wf(c: RunContext, args: dict):
            # syncワークフローからasync sideeffectを呼ぶ → awaitできないのでエラー
            async_effect(c)  # type: ignore[unused-coroutine]

        results = client.run("wf")
        assert results[0].status == "failed"


# --- asyncワークフロー内でのawait ---


class TestAsyncWorkflowAwait:
    """asyncワークフロー内でawaitを使うパターン"""

    def test_asyncワークフロー内でawaitできる(self, client: Client):
        """通常の非同期関数をawaitで呼べる"""

        async def async_helper() -> str:
            return "hello from async"

        @client.workflow()
        async def wf(c: RunContext, args: dict):
            result = await async_helper()
            c.log(result)

        results = client.run("wf")
        assert results[0].status == "succeeded"
        assert results[0].logs == ["hello from async"]

    def test_asyncワークフローでイベント発火による連鎖(self, client: Client):
        @client.workflow()
        async def wf1(c: RunContext, args: dict):
            c.log("wf1")
            c.event("chain", {"from": "wf1"})

        @client.workflow(trigger=event_trigger("chain"))
        async def wf2(c: RunContext, args: dict):
            c.log(f"wf2: {args['from']}")

        results = client.run("wf1")
        wf2_results = [r for r in results if r.workflow_name == "wf2"]
        assert len(wf2_results) == 1
        assert wf2_results[0].logs == ["wf2: wf1"]
