import optparse
import os
import time
import traceback
import shutil
import kubernetes
import sieve
import docker
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


def watch_crd(crds, addrs):
    for addr in addrs:
        for crd in crds:
            cmd_early_exit(
                "kubectl get %s -s %s --ignore-not-found=true" % (crd, addr))


def get_apiserver_ports(name, num_api):
    client = docker.from_env()
    ports = []
    for i in range(num_api):
        container_name_prefix = f"{name}-control-plane"
        suffix = str(i + 1) if i > 0 else ""
        cp_port = client.containers.get(container_name_prefix + suffix).attrs[
            "NetworkSettings"
        ]["Ports"]["6443/tcp"][0]["HostPort"]
        ports.append(cp_port)
    return ports


if __name__ == "__main__":
    common_config = get_common_config()
    usage = "usage: python3 setup_cluster.py [options]"
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
        "-n",
        "--name",
        dest="name",
        help="",
        default="kind",
    )
    (options, args) = parser.parse_args()
    if options.controller_config_dir is None:
        parser.error("parameter controller required")
    controller_config = sieve.load_controller_config(
        options.controller_config_dir)

    num_apiservers = 1
    # deploy_controller(test_context)
    deployment_file = controller_config.controller_deployment_file_path
    # backup deployment file
    backup_deployment_file = deployment_file + ".bkp"
    shutil.copyfile(deployment_file, backup_deployment_file)

    # modify container_registry and image_tag
    fin = open(deployment_file)
    data = fin.read()
    data = data.replace("${SIEVE-DR}", common_config.container_registry)
    data = data.replace("${SIEVE-DT}", "test")
    data = data.replace("${SIEVE-NS}", options.name)
    fin.close()
    fin = open(deployment_file, "w")
    fin.write(data)
    fin.close()

    # run the deploy script
    org_dir = os.getcwd()
    os.chdir(os.path.join(options.controller_config_dir, "deploy"))
    cmd_early_exit("./deploy.sh")
    os.chdir(org_dir)

    # restore deployment file
    shutil.copyfile(backup_deployment_file, deployment_file)
    os.remove(backup_deployment_file)

    kubernetes.config.load_kube_config()
    core_v1 = kubernetes.client.CoreV1Api()

    # Wait for controller pod ready
    print("Wait for the operator pod to be ready...")
    pod_ready = False
    for tick in range(600):
        controller_pod = core_v1.list_namespaced_pod(
            "default",
            watch=False,
            label_selector="sievetag=" + controller_config.controller_name,
        ).items
        if len(controller_pod) >= 1:
            if controller_pod[0].status.phase == "Running":
                pod_ready = True
                break
        time.sleep(1)
    if not pod_ready:
        fail("waiting for the operator pod to be ready")
        raise Exception("Wait timeout after 600 seconds")

    apiserver_addr_list = []
    apiserver_ports = get_apiserver_ports(options.name, num_apiservers)
    # print("apiserver ports", apiserver_ports)
    for port in apiserver_ports:
        apiserver_addr_list.append("https://127.0.0.1:" + port)
    watch_crd(
        controller_config.custom_resource_definitions, apiserver_addr_list
    )
    ok("Operator deployed")
