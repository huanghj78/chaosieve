import json
import os
import time
from utils import PROJECT_DIR, DATA_DIR, exec_bash

def get_all_result():
    res = []
    res_path = os.path.join(DATA_DIR, "workflow_result")
    for dir_name in os.listdir(res_path):
        workflow = {}
        workflow['name'] = dir_name
        workflow['result'] = []
        for file_name in os.listdir(os.path.join(res_path, dir_name)):
            result = {}
            result['workflow_id'] = file_name
            result['created_at'] = os.path.getctime(os.path.join(res_path, dir_name, file_name))
            with open(os.path.join(res_path, dir_name, file_name), 'r') as f:
                line = f.readline()
                while line:
                    if "RESULT" in line:
                        result['result'] = line.split(":")[-1]
                    if "DESCRIPTION" in line:
                        result['description'] = line.split(":")[-1]
                    line = f.readline()
            workflow['result'].append(result)
        workflow['result'] = sorted(workflow['result'], key=lambda x : -x['created_at'])
        for item in workflow['result']:
            item['created_at'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item['created_at']))

        res.append(workflow)
    return json.dumps(res)

def get_result(workflow, workflow_id):
    file_name = os.path.join(DATA_DIR, "workflow_result", workflow, workflow_id)
    with open(file_name, 'r') as f:
        res = f.read()
    return res