import json
import os
from utils import exec_bash, PROJECT_DIR, DATA_DIR


def get_target():
    res = []
    targets = exec_bash(f"ls -l {os.path.join(DATA_DIR, 'targets')}")[1:]
    for target in targets:
        item = {}
        item['name'] = target.split()[-1]
        item['created_at'] = " ".join(target.split()[5:8])
        res.append(item)
    print(res)
    return res

def get_config(name):
    with open(os.path.join(DATA_DIR, "targets", name, "config.json"), 'r') as f:
        res = f.read()
    return res

def create_target():
    pass
    
def delete_target(name):
    dir_name = os.path.join(DATA_DIR, "targets", name)
    exec_bash(f"rm -r {dir_name}")
    return json.dumps({})