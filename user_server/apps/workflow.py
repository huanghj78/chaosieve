import optparse
import os
import subprocess
from utils import exec_bash, PROJECT_DIR
from sieve_common.config import (
    get_common_config,
    load_controller_config,
)
from sieve_common.common import (
    TestContext,
    TestResult,
    cprint,
    bcolors,
    ok,
    fail,
    sieve_modes,
    cmd_early_exit,
    deploy_directory,
)

def update_test_plan(lab_name, test_plan, cnt):
    exec_bash(
        f"docker cp {test_plan} {lab_name}-control-plane:/chaos_server/server.yaml")
    ret = exec_bash(
        f"docker exec {lab_name}-control-plane bash -c '/chaos_server/user_client {lab_name} {cnt} 1'")
    if ret[0] == "0":
        return True
    else:
        print(ret[0])
        return False

def generate_config(workflowForm, planForm):
    config = {}
    config['workload'] = workflowForm['workload']
    config['actions'] = []
    for item in planForm['items']:
        action = {}
        action['actionType'] = item['actionType']
        if action['actionType'] == 'pauseAPIServer' or action['actionType'] == 'resumeAPIServer':
            action['apiServerName'] = item['actionArgs'][0]
            action['pauseScope'] = item['actionArgs'][1]
        elif action['actionType'] == 'pauseController' or action['actionType'] == 'resumeController':
            action['pauseAt'] = item['actionArgs'][0]
            action['pauseScope'] = item['actionArgs'][1]
            action['avoidOngoingRead'] = True
        elif action['actionType'] == 'reconnectController':
            #todo
            return
        elif action['actionType'] == 'delayAPIServer':
            action['apiServerName'] = item['actionArgs'][0]
            action['delayTime'] = int(item['actionArgs'][1])
            action['pauseScope'] = item['actionArgs'][2]
            action['avoidOngoingRead'] = True
        action['trigger'] = {'definitions': []}
        trigger = {}
        trigger['definitions'] = []
        triggerForm = item['triggerForm']
        for triggerItem in triggerForm['items']:
            definition = {}
            definition['triggerName'] = triggerItem['name']
            definition['condition'] = {}
            definition['condition']['conditionType'] = triggerItem['conditionType']
            definition['condition']['resourceKey'] = triggerItem['resourceKey']
            definition['condition']['occurrence'] = 1
            definition['observationPoint'] = {}
            definition['observationPoint']['when'] = triggerItem['observedWhen']
            definition['observationPoint']['by'] = triggerItem['observedBy']
            trigger['definitions'].append(definition)
        if triggerForm['immediately']:
            trigger['expression'] = ''
        else:
            trigger['expression'] = triggerForm['expression']
        action['trigger'] = trigger
        config['actions'].append(action)
    return config

def check_hypothesis(file_name, tolerance, timeout, log):
    file_path = os.path.join(PROJECT_DIR, "user_server/static/files", file_name)
    output = exec_bash(f"python3 {file_path}", timeout=timeout)
    if len(output) == 0:
        log.error("TIME OUT")
        return False
    else:
        if not isinstance(output, list):
            log.error("INVALID RESULT")
            return False
        tolerance = tolerance.split(',')
        for idx in range(len(output)):
            log.info(f"output {idx+1}: {output[idx]}")
            if output[idx] != tolerance[idx]:
                log.error(f"{output[idx]} NOT EQUAL TO {tolerance[idx]}")
                return False
        return True

def run_workload(lab_name, target_name, workload, log):
    os.chdir(PROJECT_DIR)
    common_config = get_common_config()
    controller_config_dir = os.path.join(PROJECT_DIR, "examples", target_name)
    controller_config = load_controller_config(controller_config_dir)
    result_dir = "/root/chaos_sieve/result_dir"
    use_soft_timeout = "0"
    log.info("Running test workload...")
    test_command = "%s %s %s %s" % (
        controller_config.test_command,
        workload,
        use_soft_timeout,
        os.path.join(result_dir, "workload.log"),
    )
    process = subprocess.Popen(test_command, shell=True)
    process.wait()
    log.info("Running test workload finish")

