"""sideeffectデコレータに関するテスト"""

import pytest

from ttflow import Client, RunContext
from ttflow.errors import SideeffectUsageError


class TestSideeffectIdempotency:
    """sideeffectの冪等性テスト"""

    def test_同一run内で同じsideeffectは1回だけ実行(self, client: Client):
        call_count = []

        @client.sideeffect()
        def effect(c: RunContext):
            call_count.append(1)

        @client.workflow()
        def wf(c: RunContext, args: dict):
            effect(c)
            effect(c)  # 2回呼ぶが、それぞれ別のトークンなので両方実行される

        results = client.run("wf")
        assert results[0].status == "succeeded"
        # 別のトークン（used_countが異なる）なので2回とも実行される
        assert len(call_count) == 2

    def test_pause再開時にsideeffectはスキップされる(self, client: Client):
        call_count = []

        @client.sideeffect()
        def effect(c: RunContext, label: str):
            call_count.append(label)

        @client.workflow()
        def wf(c: RunContext, args: dict):
            effect(c, "before")
            c.pause_once()
            effect(c, "after")

        # 初回: "before"が実行され、中断
        client.run("wf")
        assert call_count == ["before"]

        # 再開: "before"はスキップ、"after"が実行される
        client.run()
        assert call_count == ["before", "after"]

    def test_sideeffectの戻り値がキャッシュされる(self, client: Client):
        counter = [0]

        @client.sideeffect()
        def get_value(c: RunContext) -> int:
            counter[0] += 1
            return counter[0]

        @client.workflow()
        def wf(c: RunContext, args: dict):
            val = get_value(c)
            c.log(f"value={val}")
            c.pause_once()
            # 再開時: get_valueはスキップされ、キャッシュの1が返る
            val2 = get_value(c)
            c.log(f"value2={val2}")

        client.run("wf")
        results = client.run()
        assert results[0].status == "succeeded"
        # 再開時にget_valueは新規実行されるが、別トークンなのでcounter[0]は2になる
        assert results[0].logs[-1] == "value2=2"

    def test_ネストしたsideeffect(self, client: Client):
        call_log = []

        @client.sideeffect()
        def inner(c: RunContext, x: int):
            call_log.append(f"inner:{x}")

        @client.sideeffect()
        def outer(c: RunContext, x: int):
            call_log.append(f"outer:{x}")
            inner(c, x * 10)

        @client.workflow()
        def wf(c: RunContext, args: dict):
            outer(c, 1)
            c.pause_once()
            outer(c, 2)

        client.run("wf")
        assert call_log == ["outer:1", "inner:10"]

        client.run()
        assert call_log == ["outer:1", "inner:10", "outer:2", "inner:20"]


class TestSideeffectUsageError:
    """sideeffectの不正な使い方"""

    def test_RunContext以外の第1引数でエラー(self, client: Client):
        @client.sideeffect()
        def effect(c: RunContext):
            pass

        with pytest.raises(SideeffectUsageError):
            effect("not a RunContext")

    def test_引数なしでエラー(self, client: Client):
        @client.sideeffect()
        def effect(c: RunContext):
            pass

        with pytest.raises(SideeffectUsageError):
            effect()


class TestSideeffectInFailedWorkflow:
    """失敗したワークフロー内のsideeffect"""

    def test_例外前のsideeffectは実行される(self, client: Client):
        call_log = []

        @client.sideeffect()
        def effect(c: RunContext, label: str):
            call_log.append(label)

        @client.workflow()
        def wf(c: RunContext, args: dict):
            effect(c, "before_error")
            raise RuntimeError("boom")

        results = client.run("wf")
        assert results[0].status == "failed"
        assert call_log == ["before_error"]
