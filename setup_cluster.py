import optparse
import os
import kubernetes
import time
import traceback
import sieve
import yaml
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


def generate_configmap(test_plan):
    test_plan_content = open(test_plan).read()
    configmap = {}
    configmap["apiVersion"] = "v1"
    configmap["kind"] = "ConfigMap"
    configmap["metadata"] = {"name": "sieve-testing-global-config"}
    configmap["data"] = {"sieveTestPlan": test_plan_content}
    configmap_path = "%s-configmap.yaml" % test_plan[:-5]
    yaml.dump(configmap, open(configmap_path, "w"), sort_keys=False)
    return configmap_path


def generate_kind_config(num_apiservers, num_workers):
    kind_config_dir = "kind_configs"
    os.makedirs(kind_config_dir, exist_ok=True)
    kind_config_filename = os.path.join(
        kind_config_dir,
        "kind-%sa-%sw.yaml"
        % (
            str(num_apiservers),
            str(num_workers),
        ),
    )
    kind_config_file = open(kind_config_filename, "w")
    kind_config_file.writelines(
        ["kind: Cluster\n", "apiVersion: kind.x-k8s.io/v1alpha4\n", "nodes:\n"]
    )
    for i in range(num_apiservers):
        kind_config_file.write("- role: control-plane\n")
    for i in range(num_workers):
        kind_config_file.write("- role: worker\n")
    kind_config_file.close()
    return kind_config_filename


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
        "-p",
        "--test_plan",
        dest="test_plan",
        help="",
        default="/root/chaos_sieve/mytest/create-delay-apiserver.yaml",
    )
    parser.add_option(
        "-n",
        "--name",
        dest="name",
        help="",
        default="kind",
    )
    parser.add_option(
        "-a",
        "--apiserver_num",
        dest="apiserver_num",
        help="",
        default=1,
    )
    parser.add_option(
        "-w",
        "--worker_num",
        dest="worker_num",
        help="",
        default=1,
    )
    
    (options, args) = parser.parse_args()
    if options.controller_config_dir is None:
        parser.error("parameter controller required")
    controller_config = sieve.load_controller_config(
        options.controller_config_dir)
    mode = "test"
    test_plan = options.test_plan
    container_registry = common_config.container_registry
    image_tag = "test"
    name = options.name
    num_apiservers = int(options.apiserver_num)
    num_workers = int(options.worker_num)
    # sieve.setup_kind_cluster(test_context)
    kind_config = generate_kind_config(
        num_apiservers, num_workers
    )
    k8s_container_registry = container_registry
    k8s_image_tag = (
        controller_config.kubernetes_version + "-" + image_tag
    )
    retry_cnt = 0
    while retry_cnt < 5:
        try:
            cmd_early_exit(f"kind delete cluster --name {name}")
            # sleep here in case if the machine is slow and kind cluster deletion is not done before creating a new cluster
            time.sleep(5 + 10 * retry_cnt)
            retry_cnt += 1
            print("try to create kind cluster; retry count {}".format(retry_cnt))
            cmd_early_exit(
                "kind create cluster --name %s --image %s/node:%s --config %s"
                % (name, k8s_container_registry, k8s_image_tag, kind_config)
            )
            cmd_early_exit(
                f"docker exec {name}-control-plane bash -c 'mkdir -p /root/.kube/ && cp /etc/kubernetes/admin.conf /root/.kube/config'"
            )
            break
        except Exception:
            print(traceback.format_exc())
    kubernetes.config.load_kube_config()
    core_v1 = kubernetes.client.CoreV1Api()
    # Then we wait apiservers to be ready
    print("Waiting for apiservers to be ready...")
    apiserver_list = []
    for i in range(num_apiservers):
        apiserver_name = f"kube-apiserver-{name}-control-plane" + (
            "" if i == 0 else str(i + 1)
        )
        apiserver_list.append(apiserver_name)
    for tick in range(600):
        created = core_v1.list_namespaced_pod(
            "kube-system", watch=False, label_selector="component=kube-apiserver"
        ).items
        if len(created) == len(apiserver_list) and len(created) == len(
            [item for item in created if item.status.phase == "Running"]
        ):
            break
        time.sleep(1)
    # sieve.prepare_sieve_server(test_context)
    cmd_early_exit("cp %s chaos_server/server.yaml" % test_plan)
    org_dir = os.getcwd()
    os.chdir("chaos_server")
    cmd_early_exit("go mod tidy")
    # TODO: we should build a container image for sieve server
    cmd_early_exit("env GOOS=linux GOARCH=amd64 go build")
    os.chdir(org_dir)
    cmd_early_exit(f"docker cp chaos_server {name}-control-plane:/chaos_server")

    cprint("Update APIServer...", bcolors.OKGREEN)
    cmd_early_exit(
        f"docker cp /root/chaos_sieve/fakegopath/src/k8s.io/kubernetes/_output/release-images/amd64/kube-apiserver.tar {name}-control-plane:/")
    cmd_early_exit(
        f'docker exec {name}-control-plane sh -c "ctr -n k8s.io images import kube-apiserver.tar"')
    cmd_early_exit(f"docker exec {name}-control-plane sh -c \"sed -i 's/kube-apiserver:v1.18.9-sieve-94f372e501c973a7fa9eb40ec9ebd2fe7ca69848-dirty/kube-apiserver-amd64:v1.18.9-dirty/' /etc/kubernetes/manifests/kube-apiserver.yaml\"")
    ok("APIServer Updated")

    cprint("Setting up Sieve server...", bcolors.OKGREEN)
    cmd_early_exit(
        f"docker exec {name}-control-plane bash -c 'cd /chaos_server && ./chaos_server &> chaos_server.log &'"
    )
    ok("Sieve server set up")

    print("Waiting for apiservers to be ready...")
    # ensure that every apiserver will see the configmap is created
    time.sleep(60)
    cprint("Generate Config Map...", bcolors.OKGREEN)
    configmap = generate_configmap(test_plan)
    print(configmap)
    cmd_early_exit("kubectl apply -f %s" % configmap)

    # Preload operator image to kind nodes
    image = "%s/%s:%s" % (
        container_registry,
        controller_config.controller_name,
        image_tag,
    )
    kind_load_cmd = "kind load docker-image %s" % (image)
    print("Loading image %s to kind nodes..." % (image))
    if cmd_early_exit(kind_load_cmd, early_exit=False) != 0:
        print("Cannot load image %s locally, try to pull from remote" % (image))
        cmd_early_exit("docker pull %s" % (image))
        cmd_early_exit(kind_load_cmd)
    ok("Gen Config Map Finished")

    cmd_early_exit("go build user_client.go")
    cmd_early_exit(f"docker cp user_client {name}-control-plane:/chaos_server")
