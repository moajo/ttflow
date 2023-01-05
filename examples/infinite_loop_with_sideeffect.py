from ttflow import RunContext, setup
from ttflow.powerup.run_by_cli import run_by_cli

# TRY:
# python examples/infinite_loop_with_state.py run loop
# python examples/infinite_loop_with_state.py run
# ...(3 times)...

ttflow = setup(
    state_repository="local:states/infinite_loop_with_sideeffect.json",
)


@ttflow.sideeffect()
def send_message_to_your_phone(c: RunContext, message: str):
    c.log(f"sending message to your phone...:{message}")
    # <--- You can write here the process that actually sends the notification to the external service (this is side-effect)


@ttflow.workflow()
def loop(c: RunContext, args: dict):
    send_message_to_your_phone(c, "start!")
    c.set_state("count", 1)  # initialize variable

    while True:
        current_value = c.get_state("count")
        send_message_to_your_phone(c, f"first loop... value is {current_value}")
        c.pause_once()
        c.set_state("count", current_value + 1)

        if c.get_state("count") >= 3:
            break
    send_message_to_your_phone(c, "finish!")


run_by_cli(ttflow, enabled_dangerous_clear_state_command=True)
