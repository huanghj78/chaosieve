import os
import uuid
from flask import Flask, request
from flask import render_template
from handler import lab, target, workflow, result
from utils import PROJECT_DIR, DATA_DIR
router = Flask(__name__, template_folder="./frontend/dist",
               static_folder="./frontend/dist", static_url_path="")

router.config['UPLOAD_FOLDER'] = os.path.join(DATA_DIR, "probes")


@router.route("/")
def index():
    return render_template("index.html")


@router.route("/helloWorld")
def helloWorld():
    return "hello world"


@router.route("/Laboratory/all",  methods=['GET'])
def get_lab():
    return lab.get_lab()


@router.route("/Laboratory/new",  methods=['POST'])
def create_lab():
    data = request.get_json()
    return lab.create_lab(data['name'], data['apiserver_cnt'], data['worker_cnt'], data['target'])


@router.route("/Laboratory/delete",  methods=['POST'])
def delete_lab():
    data = request.get_json()
    return lab.delete_lab(data['name'])


@router.route("/Laboratory/apiserver",  methods=['GET'])
def get_apiserver():
    lab_name = request.args.get('lab_name')
    return lab.get_apiserver(lab_name)


@router.route("/Laboratory/target",  methods=['GET'])
def get_target():
    lab_name = request.args.get('lab_name')
    return lab.get_target(lab_name)


@router.route("/Target/all",  methods=['GET'])
def get_config():
    return target.get_target()


@router.route("/Target/config",  methods=['GET'])
def get_all_target():
    name = request.args.get('name')
    return target.get_config(name)


@router.route("/Target/delete",  methods=['POST'])
def delete_target():
    return target.delete_target()


@router.route("/Workflow/all",  methods=['GET'])
def get_all_workflow():
    return workflow.get_all_workflow()


@router.route("/Workflow",  methods=['GET'])
def get_workflow():
    lab_name = request.args.get('lab_name')
    workflow_name = request.args.get('workflow')
    target_name = request.args.get('target_name')
    return workflow.get_workflow(lab_name, target_name, workflow_name)


@router.route("/Workflow/new",  methods=['POST'])
def create_workflow():
    data = request.get_json()
    return workflow.create_workflow(data['workflow_form'], data['plan_form'])


@router.route("/Workflow/run",  methods=['POST'])
def run_workflow():
    data = request.get_json()
    uid = str(uuid.uuid4())
    return workflow.run_workflow(uid, data['lab_name'], data['target_name'], data['workflow'], data['hypothesis_form'])


@router.route("/Workflow/delete",  methods=['POST'])
def delete_workflow():
    data = request.get_json()
    return workflow.delete_workflow(data['lab_name'], data['target_name'], data['workflow'])


@router.route("/Workflow/upload", methods=['POST'])
def uploadFile():
    import json
    file = request.files['file']
    res = dict()
    if file:
        suffix = file.filename.split('.')[-1]
        new_name = str(uuid.uuid4())
        file_name = new_name + '.' + suffix
        file.save(os.path.join(router.config['UPLOAD_FOLDER'], file_name))
        res['uid'] = file_name
        return json.dumps(res)
    else:
        res['code'] = 1
        res['msg'] = "文件上传错误"
        return json.dumps(res)


@router.route("/Result/all",  methods=['GET'])
def get_all_result():
    return result.get_all_result()


@router.route("/Result",  methods=['GET'])
def get_result():
    workflow_id = request.args.get('workflow_id')
    workflow = request.args.get('workflow')
    return result.get_result(workflow, workflow_id)
