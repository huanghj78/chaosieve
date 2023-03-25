<template>
  <el-button type="primary" class="button" @click="createDialogVisible=true">Create Target</el-button>
  <div class="markup-tables flex">
  <va-card class="flex mb-4" >
    <va-card-title>Target</va-card-title>
    <va-card-content>
      <div class="table-wrapper">
        <table class="va-table">
          <thead>
            <tr>
              <th>{{ t('name') }}</th>
              <th>{{ t('created at') }}</th>
              <th>{{ t('config') }}</th>
              <th>{{ t('operation') }}</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="target in targets.list" :key="target['name']">
              <td>{{ target['name'] }}</td>
              <td>{{ target['created_at'] }}</td>
              <td>
                <el-button type="primary" @click="getTargetConfig(target['name'])" :icon="View" circle></el-button>
              </td>
              <td>
                <el-button type="danger" @click="_deleteTarget(target['name'])" :icon="Delete" circle></el-button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </va-card-content>
  </va-card>
  </div>
  <el-dialog v-model="detailDialogVisible" title="Target Detail">
    <pre>
      <code><highlightjs language="json" :autodetect="false" :code="code"></highlightjs></code>
    </pre>
  </el-dialog>

  <el-dialog v-model="createDialogVisible" title="Create Target">
    <el-form>
        <el-form-item label="Target Name">
            <el-input></el-input>
        </el-form-item>
    </el-form>
     <el-upload
        class="upload-demo"
        drag
        action="/Target/upload"
        multiple
    >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
        Drop file here or <em>click to upload</em>
        </div>
        <template #tip>
        <div class="el-upload__tip">
            上传一个关于目标系统的文件包
        </div>
        </template>
    </el-upload>

  </el-dialog>

</template>

<script setup lang="ts">
  import { useI18n } from 'vue-i18n'
  import vkbeautify from 'vkbeautify'
  import { ElNotification } from 'element-plus'
  import { UploadFilled } from '@element-plus/icons-vue'
  import type { UploadProps } from 'element-plus'
  import {Delete, VideoPlay, View} from '@element-plus/icons-vue'
  import {getTarget, deleteTarget, getConfig} from '../../../api/target.js'
  import {onMounted, ref, reactive} from 'vue'
  
  
  const { t } = useI18n()
  const form = reactive({
    name: '',
    workload: '',
    labName: '' ,
    target: ''
  });

  let createDialogVisible = ref(false)
  let detailDialogVisible = ref(false)
  let code = ref('')

  let targets = reactive({
    list: []
  })

  onMounted(async () => {
    await getTarget()
      .then(res => {
        targets.list = res.data
      })
      .catch(err => {
        console.log(err)
      })
  })

  async function getTargetConfig(name: string) {
    detailDialogVisible.value = true
    await getConfig(name)
    .then(res => {
        console.log(res.data)
        code.value = vkbeautify.json(JSON.stringify(res.data))
    })
    .catch(err => {
      console.log(err)
    })
  }

  async function _deleteTarget(name: string) {
    await deleteTarget(name)
    .then(res => {
      console.log(res.data)
    })
    .catch(err => {
      console.log(err)
    })

    await getTarget()
    .then(res => {
        targets.list = res.data
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
