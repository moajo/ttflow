from ttflow import RunContext, setup
from ttflow.powerup.run_by_cli import run_by_cli

# TRY:
# python examples/watch_price.py run 買いたいもの追加 '{"item_name":"hoge","price":150}'
# python examples/watch_price.py run
# ...(repeat)...

ttflow = setup(
    state_repository="local:states/watch_price.json",
)


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
        return 200
    elif s == 1:
        c.set_state(f"price_{item_name}", 2)
        return 300
    else:
        c.set_state(f"price_{item_name}", 0)
        return 100


run_by_cli(ttflow, enabled_dangerous_clear_state_command=True)
