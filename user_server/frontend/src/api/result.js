import axios from 'axios'

export function getAllResult() {
    return axios.get('/Result/all')
}

export function getResult(workflow, id) {
    return axios({
        method: "get",
        url: "/Result",
        params: { workflow: workflow, workflow_id: id }
    })
}