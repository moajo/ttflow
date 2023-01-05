from ttflow import RunContext, setup
from ttflow.powerup.run_by_cli import run_by_cli

# TRY: `python examples/cli.py run 処理1`

ttflow = setup(
    state_repository="local:states/cli_infinite_loop.json",
)


@ttflow.workflow()
def loop(c: RunContext, args: dict):
    count = 0
    while True:
        c.log(f"loop: {count}週目開始")
        c.pause_once()
        c.log(f"loop: {count}週目おわり")
        count += 1
        if count > 10:
            break


run_by_cli(ttflow)
