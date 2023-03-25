import optparse
import os
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
    usage = "usage: python3 update_test_plan.py [options]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option(
        "-p",
        "--test_plan",
        dest="test_plan",
        help="New test plan",
    )
    parser.add_option(
        "-i",
        "--run_immediately",
        dest="is_run_immediately",
        default=0,
    )
    (options, args) = parser.parse_args()
    test_plan = options.test_plan
    is_run_immediately = options.is_run_immediately
    cmd_early_exit(
        f"docker cp {test_plan} kind-control-plane:/chaos_server/server.yaml")
    cmd_early_exit(
        f"docker exec kind-control-plane bash -c '/chaos_server/user_client {is_run_immediately}'")
