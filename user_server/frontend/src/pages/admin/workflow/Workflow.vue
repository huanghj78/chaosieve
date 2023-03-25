<template>
  <el-button type="primary" class="button" @click="createDialogVisible=true">Create Workflow</el-button>
  <div class="markup-tables flex">
  <va-card class="flex mb-4" >
    <va-card-title>Workflow</va-card-title>
    <va-card-content>
      <div class="table-wrapper">
        <table class="va-table">
          <thead>
            <tr>
              <th>{{ t('name') }}</th>
              <th>{{ t('lab name') }}</th>
              <th>{{ t('target name') }}</th>
              <th>{{ t('workload') }}</th>
              <th>{{ t('actions') }}</th>
              <th>{{ t('detail') }}</th>
              <th>{{ t('operation') }}</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="workflow in workflows.list" :key="workflow['name']">
              <td>{{ workflow['name'] }}</td>
              <td>{{ workflow['lab_name'] }}</td>
              <td>{{ workflow['target_name'] }}</td>
              <td>{{ workflow['workload'] }}</td>
              <td>{{ workflow['actions'] }}</td>
              <td>
                <el-button type="primary" @click="getWorkflowDetail(workflow['lab_name'], workflow['target_name'], workflow['name'])" :icon="View" circle></el-button>
              </td>
              <td>
                <el-button type="success" @click="_runWorkflow(workflow['lab_name'], workflow['target_name'], workflow['name'])" :icon="VideoPlay" circle></el-button>
                <el-button type="danger" @click="_deleteWorkflow(workflow['lab_name'], workflow['target_name'], workflow['name'])" :icon="Delete" circle></el-button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </va-card-content>
  </va-card>
  </div>
  <el-dialog v-model="detailDialogVisible" title="Workflow Detail">
    <pre>
      <code><highlightjs language="json" :autodetect="false" :code="code"></highlightjs></code>
    </pre>
  </el-dialog>

  <el-dialog v-model="runDialogVisible" title="Run Workflow">
    <el-form :model="hypothesisForm" label-width="100px">
      <el-form-item label="Description">
        <el-input v-model="hypothesisForm.description"></el-input>
      </el-form-item>
      
      <va-card class="flex mb-4">
        <va-card-title>Probe</va-card-title>
        <va-card-content>
          <el-upload
            class="upload-demo"
            action="/Workflow/upload"
            :show-file-list="true"
            :on-success="handleUploadSuccess"
          >
            <el-button type="primary">Click to upload</el-button>
            Upload a python file
          </el-upload>
          <el-form>
            <el-form-item label="timeout">
              <el-input v-model="hypothesisForm.probe.timeout"></el-input>
            </el-form-item>
            <el-form-item label="expected result">
              <el-input v-model="hypothesisForm.probe.tolerance"></el-input>
            </el-form-item>
          </el-form>
        </va-card-content>
      </va-card>
    </el-form>
    <el-button type="primary" @click="_run">Run</el-button>
  </el-dialog>

  <el-dialog v-model="createDialogVisible" title="Create Workflow">
    <el-form :model="form" label-width="100px">
      <el-form-item label="Name">
        <el-input v-model="form.name"></el-input>
      </el-form-item>
      <el-form-item label="Lab Name">
        <el-select @change="changeAPIServerName()" class="input" v-model="form.labName"  size="large">
            <el-option
            v-for="(item, index) in labs.list"
            :key="item['name']"
            :label="item['name']"
            :value="item['name']"
            />
        </el-select>
      </el-form-item>
      <el-form-item label="Target">
        <el-select class="input" v-model="form.target"  size="large">
              <el-option
              v-for="(item, index) in targets.list"
              :key="item"
              :label="item"
              :value="item"
              />
          </el-select>
      </el-form-item>
      <el-form-item label="Workload">
        <el-select class="input" v-model="form.workload"  size="large">
            <el-option
            v-for="(item, index) in workloads"
            :key="item"
            :label="item"
            :value="item"
            />
        </el-select>
      </el-form-item>
      <Plans :apiserver="apiserver.list" :planForm="planForm"></Plans>
      <el-row justify="center">
        <el-button  type="primary" @click="create">Create</el-button>
      </el-row>
    </el-form>
    

  </el-dialog>

</template>

<script setup lang="ts">
  import { useI18n } from 'vue-i18n'
  import vkbeautify from 'vkbeautify'
  import { ElNotification } from 'element-plus'
  import type { UploadProps } from 'element-plus'
  import {Delete, VideoPlay, View} from '@element-plus/icons-vue'
  import Triggers from './components/Triggers.vue'
  import Plans from './components/Plans.vue'
  import {getTarget} from '../../../api/target.js'
  import {getWorkflow, getDetail, createWorkflow, deleteWorkflow, runWorkflow} from '../../../api/workflow.js'
  import {getLaboratory, createLaboratory, getAPIServerName, getTargetName} from '../../../api/laboratory.js'
  import {onMounted, ref, reactive} from 'vue'
  
  
  const { t } = useI18n()
  const form = reactive({
    name: '',
    workload: '',
    labName: '' ,
    target: ''
  });

  const planForm = reactive({
      items: [
          { actionType: '' ,
              actionArgs: ['', '', '', ''],
              triggerForm: {
                items: [
                { name: '' ,
                    conditionType: '',
                    resourceKey: '',
                    observedWhen: '',
                    observedBy: ''
                },
                ],
                expression: '',
                immediately: false
            }
          },
      ],
  });

  const hypothesisForm = reactive({
    description: '',
    probe: {
        uid: '',
        tolerance: '',
        timeout: ''
      }
  });

  const workloads = [
    'no',
    'create',
    'delete',
    'recreate',
    'disable-enable-shard',
    'disable-enable-arbiter',
    'run-cert-manager',
    'scaleup-scaledown',
    'disable-enable-shard-brittle'
  ]

  let createDialogVisible = ref(false)
  let runDialogVisible = ref(false)
  let detailDialogVisible = ref(false)
  let code = ref('')
  let labNameToRun = ref('')
  let targetToRun = ref('')
  let workflowToRun = ref('')

  let workflows = reactive({
    list: []
  })

  let labs = reactive({
    list: []
  })

  let targets = reactive({
    list: []
  })

  let apiserver = reactive({
    list: []
  })

  onMounted(async () => {
    await getLaboratory()
      .then(res => {
        labs.list = res.data
      })
      .catch(err => {
        console.log(err)
      })

    // await getTarget()
    //   .then(res => {

    //     targets.list = res.data
    //   })
    //   .catch(err => {
    //     console.log(err)
    //   })

    await getWorkflow()
    .then(res => {
      workflows.list = res.data
    })
    .catch(err => {
      console.log(err)
    })
  })

  async function getWorkflowDetail(labName: string, targetName: string, name: string) {
    detailDialogVisible.value = true
    await getDetail(labName, targetName, name)
    .then(res => {
        console.log(res.data)
        code.value = vkbeautify.json(JSON.stringify(res.data))
    })
    .catch(err => {
      console.log(err)
    })
  }

  async function create() {
    await createWorkflow(form, planForm)
    .then(res => {
      if(res.data.code != 0) {
        ElNotification({
          title: 'Fail',
          message: res.data.msg,
          type: 'error',
        })
      }
    })
    .catch(err => {
      console.log(err)
    })

    await getWorkflow()
    .then(res => {
      workflows.list = res.data
    })
    .catch(err => {
      console.log(err)
    })

    createDialogVisible.value = false
  }

  const handleUploadSuccess: UploadProps['onSuccess'] = (
    response,
    uploadFile
  ) => {
    console.log(response.uid)
    hypothesisForm.probe.uid = response.uid
  }

  async function changeAPIServerName() {
    await getAPIServerName(form.labName)
    .then(res => {
      apiserver.list = res.data
      console.log(apiserver.list)
    })
    .catch(err => {
      console.log(err)
    })

    await getTargetName(form.labName)
    .then(res => {
      targets.list = res.data
    })
    .catch(err => {
      console.log(err)
    })

  }

  function _runWorkflow(labName: string, targetName: string, workflow: string) {
    runDialogVisible.value = true
    labNameToRun.value = labName
    targetToRun.value = targetName
    workflowToRun.value = workflow
  }

  async function _run() {
    runDialogVisible.value = false
    ElNotification({
      title: 'Success',
      message: "Begin run workflow, see the result later",
      type: 'success',
    })
    runWorkflow(labNameToRun.value, targetToRun.value, workflowToRun.value, hypothesisForm)
    

  }


  async function _deleteWorkflow(labName: string, targetName: string, workflow: string) {
    await deleteWorkflow(labName, targetName, workflow)
    .then(res => {
      console.log(res.data)
    })
    .catch(err => {
      console.log(err)
    })

    await getWorkflow()
    .then(res => {
      workflows.list = res.data
    })
    .catch(err => {
      console.log(err)
    })
    
  }
</script>
<style lang="scss">
.markup-tables {
    .table-wrapper {
      overflow: auto;
    }

    .va-table {
      width: 100%;
    }
  }

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.el-card :deep(.el-card__header) {
    background-color: #f8fafc;
}

.el-card:hover :deep(.el-card__header) {
    background-color: #f1f5f9;
}

.el-card:hover .card-title {
    --tw-text-opacity: 1;
}
</style>
