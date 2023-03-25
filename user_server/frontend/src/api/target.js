import axios from 'axios'

export function getTarget() {
    return axios.get('/Target/all')
}

export function getConfig(name) {
    return axios({
        method: "get",
        url: "/Target/config",
        params: { name: name }
    })
}

export function createTarget() {
    console.log(form)
    return axios.post("/Target", {
        'username': username,
        'form': form._rawValue,
    })
}

export function deleteTarget(name) {
    return axios.post("/Target/delete", {
        name: name,
    })
}


