<template>
  <el-button type="primary" class="button" @click="dialogVisible=true">Create Laboratory</el-button>
   <div class="markup-tables flex">
    <va-card class="flex mb-4" v-for="(lab, index) in labs.list" :key="lab['name']">
      <va-card-title>
        <el-col :span="22"> 
          {{ lab['name'] }}
        </el-col>
        <el-col :span="2">
          <el-button type="danger" class="button" @click="_deleteLaboratory(lab['name'])" :icon="Delete" circle></el-button>
        </el-col>
      </va-card-title>
      <va-card-content>
        <div class="table-wrapper">
          <table class="va-table">
            <thead>
              <tr>
                <th>{{ t('node name') }}</th>
                <th>{{ t('created at') }}</th>
                <th>{{ t('status') }}</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="node in lab['nodes']" :key="node['name']">
                <td>{{ node['name'] }}</td>
                <td>{{ node['created_at'] }}</td>
                <td>
                  <va-badge :text="node['status']" :color="getStatusColor()" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </va-card-content>
    </va-card>
  </div>
  
  <el-dialog v-model="dialogVisible" title="Laboratory info">
    <el-form :model="form" label-width="120px">
      <el-form-item label="Laboratory Name">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item label="API Server Count">
        <el-input-number v-model="form.apiServerNum" :min="1" :max="10" />
      </el-form-item>
      <el-form-item label="Worker Count">
        <el-input-number v-model="form.workerNum" :min="1" :max="10" />
      </el-form-item>
      <el-form-item label="Target">
        <el-select v-model="form.target" class="m-2" placeholder="Select" size="large">
          <el-option v-for="target in targets"
            :key="target['name']"
           :label="target['name']"
           :value="target['name']"
          />
        </el-select>
      </el-form-item>
      <el-row justify="center">
        <el-button class="button" type="primary" @click="onSubmit">Create</el-button>
      </el-row>
    </el-form>
  </el-dialog>
</template>

<script setup lang="ts">
  import { onMounted, ref, reactive } from 'vue'
  import { useI18n } from 'vue-i18n'
  import {Delete} from '@element-plus/icons-vue'
  import { ElNotification } from 'element-plus'
  import {getLaboratory, createLaboratory, deleteLaboratory} from '../../../api/laboratory.js'
  import {getTarget} from '../../../api/target.js'
  const { t } = useI18n()

  let dialogVisible = ref(false)
  let labs = reactive({
    list: []
  })
  let targets = {}
  const form = reactive({
    name: '',
    apiServerNum: 1,
    workerNum: 1,
    target: '',
  })

  onMounted(async () => {
    await getLaboratory()
      .then(res => {
        console.log(res)
        labs.list = res.data
      })
      .catch(err => {
        console.log(err)
      })

    await getTarget()
      .then(res => {
        targets = res.data
      })
      .catch(err => {
        console.log(err)
      })
  })

  function getStatusColor() {
    return 'success'
  }

  async function onSubmit() {
    dialogVisible.value = false
    ElNotification({
      title: 'Success',
      message: 'please wait...',
      type: 'success',
    })
    await createLaboratory(form)
    .then(res => {
      if(res.data.code == 1) {
        ElNotification({
          title: 'Fail',
          message: res.data.msg,
          type: 'error',
        })
      }
    })
    await getLaboratory()
      .then(res => {
        console.log(res)
        labs.list = res.data
      })
      .catch(err => {
        console.log(err)
      })
  }

  async function _deleteLaboratory(name: string) {
    await deleteLaboratory(name)
    .then(res => {
      console.log(res)
    })
    .catch(err => {
      console.log(err)
    })
    await getLaboratory()
      .then(res => {
        console.log(res)
        labs.list = res.data
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

  .button {
    margin: 10px;
  }
</style>
