import os
from router import router
from utils import DATA_DIR

if __name__ == "__main__":
    if not os.path.exists(DATA_DIR):
        cmd = f"mkdir {DATA_DIR}; cd {DATA_DIR}; touch empty-workflow; mkdir lab targets workflow workflow_result probes; cd -"
        os.system(cmd)
    router.run(host="0.0.0.0", port=8080, debug=True)
