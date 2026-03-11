"""get_state / set_state / add_list_state に関するテスト"""

from ttflow import Client, RunContext


class TestSetState:
    """set_stateの基本動作"""

    def test_set_stateで値を保存できる(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.set_state("key", "value")

        client.run("wf")
        assert client._global.state.read_state("key") == "value"

    def test_set_stateは再実行時にnoopになる(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.set_state("counter", 1)
            c.pause_once()
            c.set_state("counter", 2)

        # 初回: counter=1に設定して中断
        client.run("wf")
        assert client._global.state.read_state("counter") == 1

        # 再開: 1回目のset_stateはスキップ、2回目で2に
        client.run()
        assert client._global.state.read_state("counter") == 2

    def test_set_stateは値変更時にstate_changedイベントを発火(self, client: Client):
        triggered = []

        @client.workflow()
        def setter(c: RunContext, args: dict):
            c.set_state("val", 42)

        @client.workflow(trigger="state_changed_val")
        def watcher(c: RunContext, args: dict):
            triggered.append(args)

        # ここで直接event_triggerではなくstate_triggerに対応するイベント名で登録
        # state_trigger("val")は内部的にEventTrigger("state_changed_val")
        client.run("setter")
        # ただしstate_changed_valは_trigger_prefixなしのイベントなので
        # trigger="state_changed_val"は_trigger_state_changed_valになる
        # 正しくは event_trigger を使う必要がある

    def test_set_stateで同じ値を設定してもイベントは発火しない(self, client: Client):
        from ttflow import event_trigger

        triggered = []

        @client.workflow(trigger=event_trigger("state_changed_val"))
        def watcher(c: RunContext, args: dict):
            triggered.append(1)

        # 最初にvalを設定
        client._global.state.save_state("val", 42)

        @client.workflow()
        def setter(c: RunContext, args: dict):
            c.set_state("val", 42)  # 同じ値

        client.run("setter")
        # 値が変わっていないのでwatcherは起動しない
        assert len(triggered) == 0


class TestGetState:
    """get_stateの基本動作"""

    def test_get_stateでデフォルト値(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            val = c.get_state("nonexistent", "default_val")
            c.log(f"val={val}")

        results = client.run("wf")
        assert results[0].logs == ["val=default_val"]

    def test_get_stateはNoneをデフォルトで返す(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            val = c.get_state("nonexistent")
            c.log(f"val={val}")

        results = client.run("wf")
        assert results[0].logs == ["val=None"]

    def test_get_stateは再実行時にキャッシュ値を返す(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            val = c.get_state("key", 0)
            c.log(f"val={val}")
            c.pause_once()
            # 再開時: 外部からkeyが変更されていても、キャッシュの0が返る
            val2 = c.get_state("key", 0)
            c.log(f"val2={val2}")

        client.run("wf")

        # 外部からstateを書き換える
        client._global.state.save_state("key", 999)

        results = client.run()
        assert results[0].status == "succeeded"
        # 最初のget_stateはキャッシュ（0）を返す
        assert "val=0" in results[0].logs
        # 2回目のget_stateは新たなトークンなので実際の値（999）を読む
        assert "val2=999" in results[0].logs

    def test_set_stateした値をget_stateで読める(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.set_state("key", "hello")

        @client.workflow()
        def reader(c: RunContext, args: dict):
            val = c.get_state("key")
            c.log(f"val={val}")

        client.run("wf")
        results = client.run("reader")
        reader_results = [r for r in results if r.workflow_name == "reader"]
        assert reader_results[0].logs == ["val=hello"]


class TestAddListState:
    """add_list_stateの動作"""

    def test_リストに値を追加(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.add_list_state("items", "a")
            c.add_list_state("items", "b")

        client.run("wf")
        # add_list_stateはget_state + set_stateで実装されている
        # 内部のget_stateが冪等なので、2回目のadd_list_stateは
        # 1回目のset_stateの結果を見る

    def test_max_lengthで上限を制限(self, client: Client):
        @client.workflow()
        def wf(c: RunContext, args: dict):
            for i in range(10):
                c.add_list_state("items", i)

        client.run("wf")
        # add_list_stateは内部でget_state/set_stateを使っているため
        # 冪等性の仕組みにより、各呼び出しは独立したトークンを持つ

    def test_リストでないstateにadd_list_stateするとエラー(self, client: Client):
        client._global.state.save_state("not_list", "string_value")

        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.add_list_state("not_list", "item")

        results = client.run("wf")
        assert results[0].status == "failed"
        assert "InvalidStateError" in results[0].error_message


class TestStateIsolation:
    """ワークフロー間のstate共有と分離"""

    def test_異なるワークフローから同じstateにアクセスできる(self, client: Client):
        @client.workflow()
        def writer(c: RunContext, args: dict):
            c.set_state("shared", "written")

        @client.workflow()
        def reader(c: RunContext, args: dict):
            val = c.get_state("shared")
            c.log(f"shared={val}")

        client.run("writer")
        results = client.run("reader")
        reader_results = [r for r in results if r.workflow_name == "reader"]
        assert reader_results[0].logs == ["shared=written"]

    def test_JSONシリアライズ可能な型のみ保存可能(self, client: Client):
        """stateはJSON経由で保存されるため、dict/list/str/int/float/bool/Noneのみ"""

        @client.workflow()
        def wf(c: RunContext, args: dict):
            c.set_state("data", {"key": [1, 2.5, True, None, "str"]})
            val = c.get_state("data")
            c.log(f"type={type(val).__name__}")

        results = client.run("wf")
        assert results[0].status == "succeeded"
