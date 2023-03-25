import os
import optparse
import time
import traceback
import shutil
import kubernetes
import sieve
import docker
import subprocess
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

if __name__ == "__main__":
    common_config = get_common_config()
    usage = "usage: python3 run_workload.py [options]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option(
        "-c",
        "--controller_config_dir",
        dest="controller_config_dir",
        help="specify the CONTROLLER_CONFIG_DIR",
        metavar="CONTROLLER_CONFIG_DIR",
        default="examples/mongodb-operator",
    )
    parser.add_option(
        "-w",
        "--test_workload",
        dest="test_workload",
        help="specify TEST_WORKLOAD to run",
        metavar="TEST_WORKLOAD",
    )
    (options, args) = parser.parse_args()
    if options.controller_config_dir is None:
        parser.error("parameter controller required")
    controller_config = sieve.load_controller_config(
        options.controller_config_dir)
    result_dir = "/root/chaos_sieve/result_dir"

    # select_container_from_pod = (
    #     " -c {} ".format(controller_config.container_name)
    #     if controller_config.container_name is not None
    #     else ""
    # )

    # kubernetes.config.load_kube_config()
    # pod_name = (
    #     kubernetes.client.CoreV1Api()
    #     .list_namespaced_pod(
    #         common_config.namespace,
    #         watch=False,
    #         label_selector="sievetag=" + controller_config.controller_name,
    #     )
    #     .items[0]
    #     .metadata.name
    # )
    # streamed_log_file = open(
    #     os.path.join(test_context.result_dir, "streamed-operator.log"), "w+"
    # )
    # streaming = subprocess.Popen(
    #     "kubectl logs %s %s -f" % (pod_name, select_container_from_pod),
    #     stdout=streamed_log_file,
    #     stderr=streamed_log_file,
    #     shell=True,
    #     preexec_fn=os.setsid,
    # )

    # streamed_api_server_log_file = open(
    #     os.path.join(test_context.result_dir, "apiserver1.log"), "w+"
    # )
    # streaming_api_server = subprocess.Popen(
    #     "kubectl logs kube-apiserver-kind-control-plane -n kube-system -f",
    #     stdout=streamed_api_server_log_file,
    #     stderr=streamed_api_server_log_file,
    #     shell=True,
    #     preexec_fn=os.setsid,
    # )

    use_soft_timeout = "0"
    # if "pauseController" in test_context.action_types:
    #     use_soft_timeout = "1"

    cprint("Running test workload...", bcolors.OKGREEN)
    test_command = "%s %s %s %s" % (
        controller_config.test_command,
        options.test_workload,
        use_soft_timeout,
        os.path.join(result_dir, "workload.log"),
    )
    process = subprocess.Popen(test_command, shell=True)
    process.wait()
    cprint("Running test workload finish", bcolors.OKGREEN)
    # pod_name = (
    #     kubernetes.client.CoreV1Api()
    #     .list_namespaced_pod(
    #         common_config.namespace,
    #         watch=False,
    #         label_selector="sievetag=" + controller_config.controller_name,
    #     )
    #     .items[0]
    #     .metadata.name
    # )

    # for i in range(1, num_apiservers):
    #     apiserver_name = "kube-apiserver-kind-control-plane" + (
    #         "" if i == 0 else str(i + 1)
    #     )
    #     apiserver_log = "apiserver%s.log" % (str(i + 1))
    #     cmd_early_exit(
    #         "kubectl logs %s -n kube-system > %s/%s"
    #         % (apiserver_name, test_context.result_dir, apiserver_log)
    #     )

    # if test_context.mode != sieve_modes.VANILLA:
    #     cmd_early_exit(
    #         "docker cp kind-control-plane:/sieve_server/sieve-server.log %s/sieve-server.log"
    #         % (test_context.result_dir)
    #     )

    # cmd_early_exit(
    #     "kubectl logs %s %s > %s/operator.log"
    #     % (pod_name, select_container_from_pod, test_context.result_dir)
    # )
    # os.killpg(streaming.pid, signal.SIGTERM)
    # streamed_log_file.close()
    # os.killpg(streaming_api_server.pid, signal.SIGTERM)
    # streamed_api_server_log_file.close()

    # if test_context.mode != sieve_modes.VANILLA:
    #     stop_sieve_server()
