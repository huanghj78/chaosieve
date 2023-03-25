from sieve_common.common import (
    sieve_modes,
    cmd_early_exit,
    get_all_controllers,
)
import os
import optparse
import json
from sieve_common.config import (
    CommonConfig,
    load_controller_config,
    get_common_config,
    ControllerConfig,
)

ORIGINAL_DIR = os.getcwd()

DEFAULT_K8S_VERSION = "v1.18.9"
K8S_VER_TO_APIMACHINERY_VER = {"v1.18.9": "v0.18.9", "v1.23.1": "v0.23.1"}


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
    application_dir = os.path.join("app", controller_config.controller_name)
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
    os.chdir(ORIGINAL_DIR)


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
    application_dir = os.path.join("app", controller_config.controller_name)
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
    os.chdir(ORIGINAL_DIR)


def update_go_mod_for_controller(
    controller_config_dir,
    common_config: CommonConfig,
    controller_config: ControllerConfig,
):
    application_dir = os.path.join("app", controller_config.controller_name)
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
    os.chdir(ORIGINAL_DIR)


def instrument_controller(
    common_config: CommonConfig, controller_config: ControllerConfig, mode
):
    application_dir = os.path.join("app", controller_config.controller_name)
    os.chdir("sieve_instrumentation")
    instrumentation_config = {
        "project": controller_config.controller_name,
        "mode": mode,
        "app_file_path": "%s/%s" % (ORIGINAL_DIR, application_dir),
        "controller_runtime_filepath": "%s/%s/sieve-dependency/src/sigs.k8s.io/controller-runtime@%s"
        % (
            ORIGINAL_DIR,
            application_dir,
            controller_config.controller_runtime_version,
        ),
        "client_go_filepath": "%s/%s/sieve-dependency/src/k8s.io/client-go@%s"
        % (
            ORIGINAL_DIR,
            application_dir,
            controller_config.client_go_version,
        ),
        "apis_to_instrument": controller_config.apis_to_instrument,
    }
    json.dump(instrumentation_config, open("config.json", "w"), indent=4)
    cmd_early_exit("go mod tidy")
    cmd_early_exit("go build")
    cmd_early_exit("./instrumentation config.json")
    os.chdir(ORIGINAL_DIR)


def install_lib_for_controller_with_vendor(
    common_config: CommonConfig, controller_config: ControllerConfig
):
    application_dir = os.path.join("app", controller_config.controller_name)
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
    os.chdir(ORIGINAL_DIR)


def update_go_mod_for_controller_with_vendor(
    controller_config_dir,
    common_config: CommonConfig,
    controller_config: ControllerConfig,
):
    application_dir = os.path.join("app", controller_config.controller_name)
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
    os.chdir(ORIGINAL_DIR)


def instrument_controller_with_vendor(
    common_config: CommonConfig, controller_config: ControllerConfig, mode
):
    application_dir = os.path.join("app", controller_config.controller_name)
    os.chdir("sieve_instrumentation")
    instrumentation_config = {
        "project": controller_config.controller_name,
        "mode": mode,
        "app_file_path": os.path.join(ORIGINAL_DIR, application_dir),
        "controller_runtime_filepath": os.path.join(
            ORIGINAL_DIR,
            application_dir,
            controller_config.vendored_controller_runtime_path,
        ),
        "client_go_filepath": os.path.join(
            ORIGINAL_DIR,
            application_dir,
            controller_config.vendored_client_go_path,
        ),
        "apis_to_instrument": controller_config.apis_to_instrument,
    }
    json.dump(instrumentation_config, open("config.json", "w"), indent=4)
    cmd_early_exit("go mod tidy")
    cmd_early_exit("go build")
    cmd_early_exit("./instrumentation config.json")
    os.chdir(ORIGINAL_DIR)


def build_controller(
    common_config: CommonConfig,
    controller_config: ControllerConfig,
    image_tag,
    container_registry,
):
    application_dir = os.path.join("app", controller_config.controller_name)
    os.chdir(application_dir)
    cmd_early_exit("./build.sh %s %s" % (container_registry, image_tag))
    os.chdir(ORIGINAL_DIR)
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

if __name__ == "__main__":
    usage = "usage: python3 build_controller.py [options]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option(
        "-c",
        "--controller_config_dir",
        dest="controller_config_dir",
        help="specify the CONTROLLER_CONFIG_DIR",
        metavar="CONTROLLER_CONFIG_DIR",
        default=None,
    )
