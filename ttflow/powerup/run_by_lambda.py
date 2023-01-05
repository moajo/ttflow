import json
from dataclasses import asdict

from ..ttflow import Client


def run_by_lambda(client: Client):
    def handler(event, context):
        payload = _try_parse_webhook_payload(event)
        if payload is not None:
            trigger_name, webhook_args = payload
        else:
            # triggerd other event
            trigger_name, webhook_args = None, None
        results = client.run(trigger_name, webhook_args)
        return {"results": [asdict(r) for r in results]}

    return handler


def _try_parse_webhook_payload(event: dict):
    raw_body = event.get("body")
    if raw_body is None:
        return None
    body = json.loads(raw_body)
    trigger_name = body.get("trigger_name")
    if trigger_name is None:
        return None
    webhook_args = body.get("args")
    return (trigger_name, webhook_args)
