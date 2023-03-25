import sys
sys.path.append("/root/chaos_sieve/user_server")
import subprocess
import json
import os
from utils import exec_bash
from apps.lab import setup_cluster, build


def get_lab():
    res = []
    labs = exec_bash("kind get clusters")
    containers = exec_bash(
        "docker ps --format {{.Names}}/{{.CreatedAt}}/{{.Status}}")
    for lab in labs:
        nodes = []
        for ctn in containers:
            ctn = ctn.split('/')
            if ctn[0].startswith(lab):
                nodes.append(
                    {"name": ctn[0], "created_at": ctn[1], "status": ctn[2]})
        res.append({"name": lab, "nodes": nodes})
    return json.dumps(res)


def create_lab(name, apiserver_cnt, worker_cnt):
    # todo: setup_cluster.py 加上 worker_cnt参数
    controller_config_dir = "/root/chaos_sieve/examples/mongodb-operator"
    test_plan = "/root/chaos_sieve/mytest/create-restart-controller.yaml"
    os.chdir("/root/chaos_sieve")
    # build(controller_config_dir)
    setup_cluster(name, controller_config_dir,
                  test_plan, apiserver_cnt, worker_cnt)
    return json.dumps({'msg': 'success'})

def get_apiserver(name):
    nodes = exec_bash("docker ps --format {{.Names}} | grep %s" % name)
    res = []
    for node in nodes:
        if node.startswith(f"{name}-control-plane"):
            res.append(node)
    print(res)
    return json.dumps(res)


get_apiserver('hogar')
