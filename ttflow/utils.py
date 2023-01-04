import hashlib


def workflow_hash(workflows):
    hash = hashlib.sha1()
    for wf in workflows:
        hash.update(wf.f.__code__.co_code)
    return hash.hexdigest()
