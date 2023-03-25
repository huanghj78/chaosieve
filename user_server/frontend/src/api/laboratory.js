import axios from 'axios'

export function getLaboratory() {
  return axios.get('/Laboratory/all')
}

export function createLaboratory(form) {
  console.log(form.name)
  return axios.post("/Laboratory/new", {
    'name': form.name,
    'apiserver_cnt': form.apiServerNum,
    'worker_cnt': form.workerNum,
    'target': form.target,
    'workflow': form.workflow
  })
}

export function deleteLaboratory(name) {
  return axios.post("/Laboratory/delete", {
    'name': name
  })
}

export function getAPIServerName(labName) {
  console.log(labName)
  return axios({
    method: "get",
    url: "/Laboratory/apiserver",
    params: { lab_name: labName }
  })
}

export function getTargetName(labName) {
  return axios({
    method: "get",
    url: "/Laboratory/target",
    params: { lab_name: labName }
  })
}

export function getWorkload(labName) {
  return axios({
    method: "get",
    url: "/Laboratory/workload",
    params: { lab_name: labName }
  })
}
