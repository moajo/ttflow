from ttflow import RunContext, event_trigger, setup
from ttflow.powerup.run_by_cli import run_by_cli

# TRY: `python examples/cli.py run 処理1`

ttflow = setup(
    state_repository="local:states/cli.json",
)


@ttflow.workflow()
def 処理1(c: RunContext, args: dict):
    c.log("処理1を実行します")
    c.event("event1", 42)


@ttflow.workflow(trigger=event_trigger("event1"))
def 処理2(c: RunContext, args: int):
    c.log(f"処理2も実行します: {args}")


run_by_cli(ttflow)
