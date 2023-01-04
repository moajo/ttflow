from typing import Optional,Any

from .global_env import _global

# _global.eventsはオンメモリのイベントキューである
# ttflowの一回の実行は、イベントキューが空になるまで続く

def _enque_event(event_name:str,args:Any):
    _global.events.append({
        "event_name":event_name,
        "args":args,
    })

# webhookは実態としては単にイベントである
def _enque_webhook(name:str,args:Any):
    _enque_event(f"_webhook_{name}",args)

def _pop_event()->Optional[dict]:
    if len(_global.events) == 0:
        return None
    return _global.events.pop(0)

def iterate_events():
    while True:
        e = _pop_event()
        if e is None:
            break
        yield e
