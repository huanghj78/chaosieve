import json
import yaml
import os
import time
from utils import LogHandler, exec_bash, PROJECT_DIR, DATA_DIR
from apps.workflow import generate_config, update_test_plan, check_hypothesis, run_workload

def get_all_workflow():
    res = []
    workflows = exec_bash(f"ls -l {os.path.join(DATA_DIR, 'workflow')}")[1:]
    for workflow in workflows:
        item = {}
        workflow = workflow.split()
        item['lab_name'] = workflow[-1].split(',')[0]
        item['target_name'] = workflow[-1].split(',')[1]
        item['name'] = ','.join(workflow[-1].split(',')[2:])
        with open(os.path.join(DATA_DIR, 'workflow', workflow[-1]), 'r', encoding='utf-8') as f:
            config = yaml.load(f.read(), Loader=yaml.FullLoader)
            item['workload'] = config['workload']
            actions = [action['actionType'] for action in config['actions']]
            item['actions'] = ",".join(actions)
        res.append(item)
    return json.dumps(res)

def get_workflow(lab_name, target_name, workflow):
    file_name = os.path.join(DATA_DIR, 'workflow', f'{lab_name},{target_name},{workflow}')
    with open(file_name, 'r', encoding='utf-8') as f:
        config = yaml.load(f.read(), Loader=yaml.FullLoader)
    return json.dumps(config)

def create_workflow(workflow_form, plan_form):
    res = {}
    config = generate_config(workflow_form, plan_form)
    workflow = workflow_form['name']
    res_path = os.path.join(DATA_DIR, "workflow_result", workflow)
    if os.path.exists(res_path):
        res['code'] = 1
        res['msg'] = f"workflow {workflow} has existed"
        return json.dumps(res)
    else:
        os.makedirs(res_path)
    lab_name = workflow_form['labName']
    target_name = workflow_form['target']
    file_name = f'{DATA_DIR}/workflow/{lab_name},{target_name},{workflow}'
    with open(file_name, 'w', encoding='utf-8') as f:
        yaml.dump(data=config, stream=f, allow_unicode=True)
    res['code'] = 0
    res['data'] = config
    return json.dumps(res)

# 1. 检查稳态假设 2. 更新config 3. 运行workload 4. 再次检查稳态假设 
def run_workflow(workflow_id, lab_name, target_name, workflow, hypothesis_form):
    res = {}
    res_file = f'{DATA_DIR}/workflow_result/{workflow}/{workflow_id}'
    log = LogHandler(res_file)
    probe = hypothesis_form['probe']
    log.info("Begin run workflow")
    log.info(f"WORKFLOW_ID:{workflow_id}")
    log.info(f"WORKFLOW:{workflow}")
    log.info(f"DESCRIPTION:{hypothesis_form['description']}")
    # if check_hypothesis(probe['uid'], probe['tolerance'], probe['timeout'], log):
    #     log.info("Steady state hypothesis is met!")
    #     log.info("Update test plan...")
    # else:
    #     return json.dumps({})
    log.info("Update test plan...")
    file_name = f'{DATA_DIR}/workflow/{lab_name},{target_name},{workflow}'
    with open(file_name, 'r', encoding='utf-8') as f:
        config = yaml.load(f.read(), Loader=yaml.FullLoader)
    cnt = 0
    for action in config['actions']:
        if action['trigger']['expression'] == '':
            cnt += 1
        else:
            break
    if update_test_plan(lab_name, file_name, cnt):
        log.info("Update test plan success")
    else:
        res['code'] = 1
        res['msg'] = "Update test plan failed"
        log.error("Update test plan failed")
        log.info("RESULT:fail")
        return json.dumps(res)
    if config['workload'] != "no":
        run_workload(lab_name, target_name, config['workload'], log)
    if check_hypothesis(probe['uid'], probe['tolerance'], probe['timeout'], log):
        log.info("Steady state hypothesis is met!")
        log.info("RESULT:success")
    else:
        log.info("RESULT:fail")
        res['code'] = 1
        res['msg'] = "Steady state hypothesis is not met"
        return json.dumps(res)
    res['code'] = 0
    res['workflow_id'] = workflow_id
    return json.dumps(res)

def delete_workflow(lab_name, target_name, workflow):
    file_name = os.path.join(DATA_DIR, 'workflow', f"{lab_name},{target_name},{workflow}")
    exec_bash(f"rm {file_name}")
    dir_name = os.path.join(DATA_DIR, 'workflow_result', f"{workflow}")
    exec_bash(f"rm -r {dir_name}")
    return json.dumps({})