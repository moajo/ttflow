class Trigger:
    def __init__(self, trigger_type: str):
        self.trigger_type = trigger_type


class EventTrigger(Trigger):
    def __init__(self, event_name: str):
        super().__init__("event")
        self.event_name = event_name
