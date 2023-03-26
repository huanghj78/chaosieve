import json
import yaml
import os
import sys
import importlib
from utils import exec_bash, PROJECT_DIR, DATA_DIR
from apps.lab import setup_cluster, setup_operator, build


def get_lab():
    res = []
    labs = exec_bash("kind get clusters")
    containers = exec_bash(
        "docker ps --format {{.Names}},{{.CreatedAt}},{{.Status}},{{.Image}}")
    for lab in labs:
        nodes = []
        for ctn in containers:
            ctn = ctn.split(',')
            if ctn[-1] != "ghcr.io/sieve-project/action/node:v1.18.9-test":
                continue
            if ctn[0].startswith(lab+'-'):
                nodes.append(
                    {"name": ctn[0], "created_at": ctn[1], "status": ctn[2]})
        res.append({"name": lab, "nodes": nodes})
    return json.dumps(res)


def create_lab(name, apiserver_cnt, worker_cnt, target):
    res = {}
    file_name = os.path.join(DATA_DIR, "lab", name)
    if os.path.exists(file_name):
        res['code'] = 1
        res['msg'] = f"lab {name} exists"
        return json.dumps(res)
    os.chdir(PROJECT_DIR)
    # build(controller_config_dir)
    target_dir = os.path.join(PROJECT_DIR, "examples", target)
    workflow_file = os.path.join(DATA_DIR, "empty-workflow")
    init_workflow = {"serverEndpoint": name+"-control-plane:12345"}
    with open(workflow_file, 'w', encoding='utf-8') as f:
        yaml.dump(data=init_workflow, stream=f, allow_unicode=True)
    setup_cluster(name, target_dir,
                  workflow_file, apiserver_cnt, worker_cnt)
    setup_operator(name, target_dir)
    with open(file_name, 'w') as f:
        f.write(target)
    res['code'] = 0
    return json.dumps(res)


def delete_lab(name):
    exec_bash(f"kind delete cluster --name {name}")
    file_name = os.path.join(DATA_DIR, "lab", name)
    exec_bash(f"rm {file_name}")
    return json.dumps({})


def get_apiserver(name):
    nodes = exec_bash(
        "docker ps --format {{.Names}} | grep %s" % name)
    res = []
    for node in nodes:
        if node.startswith(f"{name}-control-plane"):
            res.append(node)
    return json.dumps(res)


def get_target(name):
    file_name = os.path.join(DATA_DIR, "lab", name)
    with open(file_name, 'r') as f:
        target = f.read()
    return [target]
