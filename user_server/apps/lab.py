from utils import PROJECT_DIR
import sys
sys.path.append(PROJECT_DIR)
from utils import PROJECT_DIR, exec_bash
from sieve_common.common import (
    TestContext,
    TestResult,
    cprint,
    bcolors,
    ok,
    fail,
    cmd_early_exit,
    deploy_directory,
    get_all_controllers,
)
from sieve_common.config import (
    CommonConfig,
    load_controller_config,
    get_common_config,
    ControllerConfig,
)
import docker
import shutil
import json
import yaml
import traceback
import time
import kubernetes
import os
import subprocess


DEFAULT_K8S_VERSION = "v1.18.9"
K8S_VER_TO_APIMACHINERY_VER = {"v1.18.9": "v0.18.9", "v1.23.1": "v0.23.1"}


def watch_crd(crds, addrs):
    for addr in addrs:
        for crd in crds:
            cmd_early_exit(
                "kubectl get %s -s %s --ignore-not-found=true" % (crd, addr))


def get_apiserver_ports(lab, num_api):
    client = docker.from_env()
    ports = []
    for i in range(num_api):
        container_name_prefix = f"{lab}-control-plane"
        suffix = str(i + 1) if i > 0 else ""
        cp_port = client.containers.get(container_name_prefix + suffix).attrs[
            "NetworkSettings"
        ]["Ports"]["6443/tcp"][0]["HostPort"]
        ports.append(cp_port)
    return ports


def update_sieve_client_go_mod_with_version(go_mod_path, version):
    fin = open(go_mod_path)
    data = fin.read()
    data = data.replace(
        "k8s.io/apimachinery v0.18.9",
        "k8s.io/apimachinery %s" % version,
    )
    fin.close()
    fout = open(go_mod_path, "w")
    fout.write(data)
    fout.close()


def download_controller(
    common_config: CommonConfig,
    controller_config: ControllerConfig,
):
    application_dir = os.path.join(
        PROJECT_DIR, "app", controller_config.controller_name)
    # If for some permission issue that we can't remove the operator, try sudo
    if cmd_early_exit("rm -rf %s" % application_dir, early_exit=False) != 0:
        print("We cannot remove %s, try sudo instead" % application_dir)
        cmd_early_exit("sudo rm -rf %s" % application_dir)
    cmd_early_exit(
        "git clone %s %s >> /dev/null"
        % (controller_config.github_link, application_dir)
    )
    os.chdir(application_dir)
    cmd_early_exit("git checkout %s >> /dev/null" % controller_config.commit)
    cmd_early_exit("git checkout -b sieve >> /dev/null")
    for commit in controller_config.cherry_pick_commits:
        cmd_early_exit("git cherry-pick %s" % commit)
    os.chdir(PROJECT_DIR)


def remove_replacement_in_go_mod_file(file):
    lines = []
    with open(file, "r") as go_mod_file:
        lines = go_mod_file.readlines()
    with open(file, "w") as go_mod_file:
        for line in lines:
            if "k8s.io/client-go =>" in line:
                continue
            elif "sigs.k8s.io/controller-runtime =>" in line:
                continue
            go_mod_file.write(line)


def install_lib_for_controller(
    common_config: CommonConfig, controller_config: ControllerConfig
):
    application_dir = os.path.join(
        PROJECT_DIR, "app", controller_config.controller_name)
    # download controller_runtime
    cmd_early_exit(
        "go mod download sigs.k8s.io/controller-runtime@%s >> /dev/null"
        % controller_config.controller_runtime_version
    )
    cmd_early_exit("mkdir -p %s/sieve-dependency/src/sigs.k8s.io" %
                   application_dir)
    cmd_early_exit(
        "cp -r ${GOPATH}/pkg/mod/sigs.k8s.io/controller-runtime@%s %s/sieve-dependency/src/sigs.k8s.io/controller-runtime@%s"
        % (
            controller_config.controller_runtime_version,
            application_dir,
            controller_config.controller_runtime_version,
        )
    )
    cmd_early_exit(
        "chmod -R +w %s/sieve-dependency/src/sigs.k8s.io/controller-runtime@%s"
        % (
            application_dir,
            controller_config.controller_runtime_version,
        )
    )
    # download client_go
    cmd_early_exit(
        "go mod download k8s.io/client-go@%s >> /dev/null"
        % controller_config.client_go_version
    )
    cmd_early_exit("mkdir -p %s/sieve-dependency/src/k8s.io" % application_dir)
    cmd_early_exit(
        "cp -r ${GOPATH}/pkg/mod/k8s.io/client-go@%s %s/sieve-dependency/src/k8s.io/client-go@%s"
        % (
            controller_config.client_go_version,
            application_dir,
            controller_config.client_go_version,
        )
    )
    cmd_early_exit(
        "chmod -R +w %s/sieve-dependency/src/k8s.io/client-go@%s"
        % (application_dir, controller_config.client_go_version)
    )
    cmd_early_exit(
        "cp -r sieve_client %s/sieve-dependency/src/sieve.client" % application_dir
    )
    if controller_config.kubernetes_version != DEFAULT_K8S_VERSION:
        update_sieve_client_go_mod_with_version(
            "%s/sieve-dependency/src/sieve.client/go.mod" % application_dir,
            K8S_VER_TO_APIMACHINERY_VER[controller_config.kubernetes_version],
        )
    elif controller_config.apimachinery_version is not None:
        update_sieve_client_go_mod_with_version(
            "%s/sieve-dependency/src/sieve.client/go.mod" % application_dir,
            controller_config.apimachinery_version,
        )
    # download the other dependencies
    downloaded_module = set()
    for api_to_instrument in controller_config.apis_to_instrument:
        module = api_to_instrument["module"]
        if module in downloaded_module:
            continue
        downloaded_module.add(module)
        cmd_early_exit("go mod download %s >> /dev/null" % module)
        cmd_early_exit(
            "mkdir -p %s/sieve-dependency/src/%s"
            % (application_dir, os.path.dirname(module))
        )
        cmd_early_exit(
            "cp -r ${GOPATH}/pkg/mod/%s %s/sieve-dependency/src/%s"
            % (
                module,
                application_dir,
                module,
            )
        )
        cmd_early_exit(
            "chmod -R +w %s/sieve-dependency/src/%s"
            % (
                application_dir,
                module,
            )
        )

    os.chdir(application_dir)
    cmd_early_exit("git add -A >> /dev/null")
    cmd_early_exit('git commit -m "install the lib" >> /dev/null')
    os.chdir(PROJECT_DIR)


def update_go_mod_for_controller(
    controller_config_dir,
    common_config: CommonConfig,
    controller_config: ControllerConfig,
):
    application_dir = os.path.join(
        PROJECT_DIR, "app", controller_config.controller_name)
    # modify the go.mod to import the libs
    remove_replacement_in_go_mod_file("%s/go.mod" % application_dir)
    with open("%s/go.mod" % application_dir, "a") as go_mod_file:
        go_mod_file.write("require sieve.client v0.0.0\n")
        go_mod_file.write(
            "replace sieve.client => ./sieve-dependency/src/sieve.client\n"
        )
        go_mod_file.write(
            "replace sigs.k8s.io/controller-runtime => ./sieve-dependency/src/sigs.k8s.io/controller-runtime@%s\n"
            % controller_config.controller_runtime_version
        )
        go_mod_file.write(
            "replace k8s.io/client-go => ./sieve-dependency/src/k8s.io/client-go@%s\n"
            % controller_config.client_go_version
        )
        added_module = set()
        for api_to_instrument in controller_config.apis_to_instrument:
            module = api_to_instrument["module"]
            if module in added_module:
                continue
            added_module.add(module)
            go_mod_file.write(
                "replace %s => ./sieve-dependency/src/%s\n"
                % (module.split("@")[0], module)
            )

    # TODO: do we need to modify go.mod in controller-runtime and client-go?
    with open(
        "%s/sieve-dependency/src/sigs.k8s.io/controller-runtime@%s/go.mod"
        % (
            application_dir,
            controller_config.controller_runtime_version,
        ),
        "a",
    ) as go_mod_file:
        go_mod_file.write("require sieve.client v0.0.0\n")
        go_mod_file.write("replace sieve.client => ../../sieve.client\n")
        go_mod_file.write(
            "replace k8s.io/client-go => ../../k8s.io/client-go@%s\n"
            % controller_config.client_go_version
        )
    with open(
        "%s/sieve-dependency/src/k8s.io/client-go@%s/go.mod"
        % (application_dir, controller_config.client_go_version),
        "a",
    ) as go_mod_file:
        go_mod_file.write("require sieve.client v0.0.0\n")
        go_mod_file.write("replace sieve.client => ../../sieve.client\n")

    # copy the build.sh and Dockerfile
    cmd_early_exit(
        "cp %s %s"
        % (
            os.path.join(controller_config_dir, "build", "build.sh"),
            os.path.join(application_dir, "build.sh"),
        )
    )
    cmd_early_exit(
        "cp %s %s"
        % (
            os.path.join(controller_config_dir, "build", "Dockerfile"),
            os.path.join(application_dir, controller_config.dockerfile_path),
        )
    )
    os.chdir(application_dir)
    cmd_early_exit("git add -A >> /dev/null")
    cmd_early_exit('git commit -m "import the lib" >> /dev/null')
    os.chdir(PROJECT_DIR)


def instrument_controller(
    common_config: CommonConfig, controller_config: ControllerConfig, mode
):
    application_dir = os.path.join(
        PROJECT_DIR, "app", controller_config.controller_name)
    os.chdir("sieve_instrumentation")
    instrumentation_config = {
        "project": controller_config.controller_name,
        "mode": mode,
        "app_file_path": "%s" % application_dir,
        "controller_runtime_filepath": "%s/sieve-dependency/src/sigs.k8s.io/controller-runtime@%s"
        % (
            application_dir,
            controller_config.controller_runtime_version,
        ),
        "client_go_filepath": "%s/sieve-dependency/src/k8s.io/client-go@%s"
        % (
            application_dir,
            controller_config.client_go_version,
        ),
        "apis_to_instrument": controller_config.apis_to_instrument,
    }
    json.dump(instrumentation_config, open("config.json", "w"), indent=4)
    cmd_early_exit("go mod tidy")
    cmd_early_exit("go build")
    cmd_early_exit("./instrumentation config.json")
    os.chdir(PROJECT_DIR)


def install_lib_for_controller_with_vendor(
    common_config: CommonConfig, controller_config: ControllerConfig
):
    application_dir = os.path.join(
        PROJECT_DIR, "app", controller_config.controller_name)
    cmd_early_exit(
        "cp -r sieve_client %s"
        % os.path.join(application_dir, controller_config.vendored_sieve_client_path)
    )
    if controller_config.kubernetes_version != DEFAULT_K8S_VERSION:
        update_sieve_client_go_mod_with_version(
            os.path.join(
                application_dir, controller_config.vendored_sieve_client_path, "go.mod"
            ),
            K8S_VER_TO_APIMACHINERY_VER[controller_config.kubernetes_version],
        )
    elif controller_config.apimachinery_version is not None:
        update_sieve_client_go_mod_with_version(
            os.path.join(
                application_dir, controller_config.vendored_sieve_client_path, "go.mod"
            ),
            controller_config.apimachinery_version,
        )
    os.chdir(application_dir)
    cmd_early_exit("git add -A >> /dev/null")
    cmd_early_exit('git commit -m "install the lib" >> /dev/null')
    os.chdir(PROJECT_DIR)


def update_go_mod_for_controller_with_vendor(
    controller_config_dir,
    common_config: CommonConfig,
    controller_config: ControllerConfig,
):
    application_dir = os.path.join(
        PROJECT_DIR, "app", controller_config.controller_name)
    with open(os.path.join(application_dir, "go.mod"), "a") as go_mod_file:
        go_mod_file.write("require sieve.client v0.0.0\n")
    with open(
        os.path.join(
            application_dir,
            controller_config.vendored_controller_runtime_path,
            "go.mod",
        ),
        "a",
    ) as go_mod_file:
        go_mod_file.write("require sieve.client v0.0.0\n")
    with open(
        os.path.join(
            application_dir,
            controller_config.vendored_client_go_path,
            "go.mod",
        ),
        "a",
    ) as go_mod_file:
        go_mod_file.write("require sieve.client v0.0.0\n")

    # copy the build.sh and Dockerfile
    cmd_early_exit(
        "cp %s %s"
        % (
            os.path.join(controller_config_dir, "build", "build.sh"),
            os.path.join(application_dir, "build.sh"),
        )
    )
    cmd_early_exit(
        "cp %s %s"
        % (
            os.path.join(controller_config_dir, "build", "Dockerfile"),
            os.path.join(application_dir, controller_config.dockerfile_path),
        )
    )
    os.chdir(application_dir)
    cmd_early_exit("git add -A >> /dev/null")
    cmd_early_exit('git commit -m "import the lib" >> /dev/null')
    os.chdir(PROJECT_DIR)


def instrument_controller_with_vendor(
    common_config: CommonConfig, controller_config: ControllerConfig, mode
):
    application_dir = os.path.join(
        PROJECT_DIR, "app", controller_config.controller_name)
    os.chdir("sieve_instrumentation")
    instrumentation_config = {
        "project": controller_config.controller_name,
        "mode": mode,
        "app_file_path": os.path.join(application_dir),
        "controller_runtime_filepath": os.path.join(
            application_dir,
            controller_config.vendored_controller_runtime_path,
        ),
        "client_go_filepath": os.path.join(
            application_dir,
            controller_config.vendored_client_go_path,
        ),
        "apis_to_instrument": controller_config.apis_to_instrument,
    }
    json.dump(instrumentation_config, open("config.json", "w"), indent=4)
    cmd_early_exit("go mod tidy")
    cmd_early_exit("go build")
    cmd_early_exit("./instrumentation config.json")
    os.chdir(PROJECT_DIR)


def build_controller(
    common_config: CommonConfig,
    controller_config: ControllerConfig,
    image_tag,
    container_registry,
):
    application_dir = os.path.join(
        PROJECT_DIR, "app", controller_config.controller_name)
    os.chdir(application_dir)
    cmd_early_exit("./build.sh %s %s" % (container_registry, image_tag))
    os.chdir(PROJECT_DIR)
    os.system(
        "docker tag %s %s/%s:%s"
        % (
            controller_config.controller_image_name,
            container_registry,
            controller_config.controller_name,
            image_tag,
        )
    )


def setup_controller(
    controller_config_dir,
    common_config: CommonConfig,
    controller_config: ControllerConfig,
    mode,
    container_registry
):
    image_tag = mode
    download_controller(common_config, controller_config)
    if controller_config.go_mod == "mod":
        install_lib_for_controller(common_config, controller_config)
        update_go_mod_for_controller(
            controller_config_dir, common_config, controller_config
        )
        instrument_controller(common_config, controller_config, mode)
    else:
        install_lib_for_controller_with_vendor(
            common_config, controller_config)
        update_go_mod_for_controller_with_vendor(
            controller_config_dir, common_config, controller_config
        )
        instrument_controller_with_vendor(
            common_config, controller_config, mode)
    build_controller(common_config, controller_config,
                     image_tag, container_registry)


def build(controller_config_dir):
    mode = "test"
    common_config = get_common_config()
    container_registry = common_config.container_registry
    controller_config = load_controller_config(controller_config_dir)
    setup_controller(
        controller_config_dir,
        common_config,
        controller_config,
        mode,
        container_registry
    )


def _generate_configmap(test_plan):
    test_plan_content = open(test_plan).read()
    configmap = {}
    configmap["apiVersion"] = "v1"
    configmap["kind"] = "ConfigMap"
    configmap["metadata"] = {"name": "sieve-testing-global-config"}
    configmap["data"] = {"sieveTestPlan": test_plan_content}
    configmap_path = "%s-configmap.yaml" % test_plan[:-5]
    yaml.dump(configmap, open(configmap_path, "w"), sort_keys=False)
    return configmap_path


def _generate_kind_config(num_apiservers, num_workers):
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


def setup_cluster(name, controller_config_dir, test_plan, apiserver_cnt, worker_cnt):
    common_config = get_common_config()
    controller_config = load_controller_config(controller_config_dir)
    container_registry = common_config.container_registry
    mode = "test"
    image_tag = "test"
    kind_config = _generate_kind_config(
        apiserver_cnt, worker_cnt
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
    for i in range(apiserver_cnt):
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
    cmd_early_exit("cp %s chaos_server/server.yaml" % test_plan)
    os.chdir(os.path.join(PROJECT_DIR, "chaos_server"))
    cmd_early_exit("go mod tidy")
    # TODO: we should build a container image for sieve server
    cmd_early_exit("env GOOS=linux GOARCH=amd64 go build")
    os.chdir(PROJECT_DIR)
    cmd_early_exit(
        f"docker cp chaos_server {name}-control-plane:/chaos_server")

    cprint("Update APIServer...", bcolors.OKGREEN)
    cmd_early_exit(
        f"docker cp /root/chaos_sieve/fakegopath/src/k8s.io/kubernetes/_output/release-images/amd64/kube-apiserver.tar {name}-control-plane:/")
    cmd_early_exit(
        f'docker exec {name}-control-plane sh -c "ctr -n k8s.io images import kube-apiserver.tar"')
    cmd_early_exit(f"docker exec {name}-control-plane sh -c \"sed -i 's/kube-apiserver:v1.18.9-sieve-94f372e501c973a7fa9eb40ec9ebd2fe7ca69848-dirty/kube-apiserver-amd64:v1.18.9-dirty/' /etc/kubernetes/manifests/kube-apiserver.yaml\"")
    ok("APIServer Updated")

    cprint("Setting up Chaos server...", bcolors.OKGREEN)
    cmd_early_exit(
        f"docker exec {name}-control-plane bash -c 'cd /chaos_server && ./chaos_server &> chaos_server.log &'"
    )
    ok("Chaos server set up")

    print("Waiting for apiservers to be ready...")
    # ensure that every apiserver will see the configmap is created
    time.sleep(60)
    cprint("Generate Config Map...", bcolors.OKGREEN)
    configmap = _generate_configmap(test_plan)
    print(configmap)
    cmd_early_exit("kubectl apply -f %s " % (configmap))
    ok("Gen Config Map Finished")

    # Preload operator image to kind nodes
    image = "%s/%s:%s" % (
        container_registry,
        controller_config.controller_name,
        image_tag,
    )
    kind_load_cmd = "kind load docker-image %s --name %s" % (image, name)
    print("Loading image %s to kind nodes..." % (image))
    if cmd_early_exit(kind_load_cmd, early_exit=False) != 0:
        print("Cannot load image %s locally, try to pull from remote" % (image))
        cmd_early_exit("docker pull %s" % (image))
        cmd_early_exit(kind_load_cmd)

    cmd_early_exit("go build user_client.go")
    cmd_early_exit(f"docker cp user_client {name}-control-plane:/chaos_server")


def setup_operator(lab, controller_config_dir):
    common_config = get_common_config()
    controller_config = load_controller_config(controller_config_dir)
    num_apiservers = 1
    # deploy_controller(test_context)
    deployment_file = controller_config.controller_deployment_file_path
    # backup deployment file
    backup_deployment_file = deployment_file + ".bkp"
    shutil.copyfile(deployment_file, backup_deployment_file)
    fin = open(deployment_file)
    data = fin.read()
    data = data.replace("${SIEVE-DR}", common_config.container_registry)
    data = data.replace("${SIEVE-DT}", "test")
    data = data.replace("${SIEVE-NS}", lab)
    fin.close()
    fin = open(deployment_file, "w")
    fin.write(data)
    fin.close()
    os.chdir(os.path.join(controller_config_dir, "deploy"))
    cmd_early_exit(f"./deploy.sh")

    os.chdir(PROJECT_DIR)

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
    apiserver_ports = get_apiserver_ports(lab, num_apiservers)
    # print("apiserver ports", apiserver_ports)
    for port in apiserver_ports:
        apiserver_addr_list.append("https://127.0.0.1:" + port)
    watch_crd(
        controller_config.custom_resource_definitions, apiserver_addr_list
    )
    ok("Operator deployed")
