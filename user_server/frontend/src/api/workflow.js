import axios from 'axios'

export function getWorkflow() {
    return axios.get('/Workflow/all')
}

export function getDetail(labName, targetName, workflow) {
    return axios({
        method: "get",
        url: "/Workflow",
        params: { lab_name: labName, workflow: workflow, target_name: targetName }
    })
}

export function createWorkflow(workflowForm, planForm) {
    return axios.post("/Workflow/new", {
        workflow_form: workflowForm,
        plan_form: planForm
    })
}

export function deleteWorkflow(labName, targetName, workflow) {
    return axios.post("/Workflow/delete", {
        lab_name: labName,
        workflow: workflow,
        target_name: targetName
    })
}

export function runWorkflow(labName, targetName, workflow, hypothesisForm) {
    return axios.post("/Workflow/run", {
        lab_name: labName,
        target_name: targetName,
        workflow: workflow,
        hypothesis_form: hypothesisForm
    })
}


