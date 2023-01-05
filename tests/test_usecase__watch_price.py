from ttflow import Client, RunContext


def define_workflow(ttflow: Client):
    @ttflow.workflow()
    def 買いたいもの追加(c: RunContext, args: dict):
        item_name = args["item_name"]
        price = args["price"]
        c.log(f"買いたいもの追加: {item_name}")

        count = 1
        while True:
            current_price = 値段を取得(c, item_name)
            if current_price <= price:
                c.log(f"{count}回目: {item_name}は{current_price}円!")
                # send notification here!
                return
            c.log(f"{count}回目: {item_name}は{current_price}で買えませんでした")
            count += 1
            c.pause_once()

    @ttflow.sideeffect()
    def 値段を取得(c: RunContext, item_name: str) -> int:
        # dummy
        s = c.get_state(f"price_{item_name}", 0)
        if s == 0:
            c.set_state(f"price_{item_name}", 1)
            return 200 + len(item_name)
        elif s == 1:
            c.set_state(f"price_{item_name}", 2)
            return 300 + len(item_name)
        else:
            c.set_state(f"price_{item_name}", 0)
            return 100 + len(item_name)


def test_値段監視ワークフロー(client: Client):
    ttflow = client

    define_workflow(ttflow)

    results = client.run("買いたいもの追加", {"item_name": "hoge", "price": 200})
    assert len(results) == 1
    assert results[0].workflow_name == "買いたいもの追加"
    assert results[0].status == "paused"
    assert results[0].logs == [
        "買いたいもの追加: hoge",
        "1回目: hogeは204で買えませんでした",
    ]

    results = client.run("買いたいもの追加", {"item_name": "fuga", "price": 150})
    assert len(results) == 2
    assert results[0].workflow_name == "買いたいもの追加"
    assert results[0].status == "paused"
    assert results[0].logs == [
        "買いたいもの追加: fuga",
        "1回目: fugaは204で買えませんでした",
    ]
    assert results[1].workflow_name == "買いたいもの追加"
    assert results[1].status == "paused"
    assert results[1].logs == [
        "買いたいもの追加: hoge",
        "1回目: hogeは204で買えませんでした",
        "2回目: hogeは304で買えませんでした",
    ]
