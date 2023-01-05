from ttflow import RunContext, setup
from ttflow.powerup.run_by_cli import run_by_cli

# ユースケース例
# 1. 外出、帰宅イベントを受信する
# 2. 外出中にモーションセンサーが反応したら、通知する
# TRY:
# python examples/home_security.py run 外出
# python examples/home_security.py run 帰宅
# python examples/home_security.py run モーションセンサー

ttflow = setup(
    state_repository="local:states/home_security.json",
)


@ttflow.workflow()
def 外出(c: RunContext, args: dict):
    c.set_state("外出中", True)
    c.log(f"外出しました。現在の外出中状態: {c.get_state('外出中')}")


@ttflow.workflow()
def 帰宅(c: RunContext, args: dict):
    c.set_state("外出中", False)
    c.log(f"帰宅しました。現在の外出中状態: {c.get_state('外出中')}")


@ttflow.workflow()
def モーションセンサー(c: RunContext, data: dict):
    if c.get_state("外出中", default=False):
        c.log("外出中にモーションセンサーが反応した")
        notification_to_app(c, "外出中にモーションセンサーが反応した")


@ttflow.sideeffect()
def notification_to_app(c: RunContext, message: str):
    # TODO: ここで通知を送信する
    c.log(f"ここでアプリに通知を送信する: {message}")


run_by_cli(ttflow, enabled_dangerous_clear_state_command=True)
