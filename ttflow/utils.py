import hashlib
import os


def get_dir_hash(directory: str):
    if not os.path.exists(directory):
        return -1
    hash = hashlib.sha1()
    for root, dirs, files in os.walk(directory):
        for file in files:
            with open(os.path.join(root, file), "rb") as f:
                while True:
                    buf = f.read(hash.block_size * 0x800)
                    if not buf:
                        break
                    hash.update(buf)
    return hash.hexdigest()
