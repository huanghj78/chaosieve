<template>
   <div class="markup-tables flex">
    <va-card class="flex mb-4" v-for="(result, index) in results.list" :key="result['name']">
      <va-card-title>{{ result['name'] }}</va-card-title>
      <va-card-content>
        <div class="table-wrapper">
          <table class="va-table">
            <thead>
              <tr>
                <th>{{ t('id') }}</th>
                <th>{{ t('description') }}</th>
                <th>{{ t('created at') }}</th>
                <th>{{ t('status') }}</th>
                <th>{{ t('detail') }}</th>
              </tr>
            </thead>

            <tbody>
              <tr v-for="(item, index) in result['result']" :key="item['workflow_id']">
                <td>{{ index+1 }}</td>
                <td>{{ item['description'] }}</td>
                <td>{{ item['created_at'] }}</td>
                <td>
                  <va-badge v-if="item['result'] === 'success\n' || item['result'] === 'fail\n'" :text="item['result']" :color="getResultColor(item['result'])" />
                  <va-badge v-else text="running" :color="getResultColor('running')" />
                </td>
                <td>
                   <el-button type="primary" @click="getResultDetail(result['name'], item['workflow_id'])" :icon="View" circle></el-button> 
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </va-card-content>
    </va-card>
  </div>
  <el-dialog v-model="detailDialogVisible" title="Result Detail">
    <pre>
      <code><highlightjs :autodetect="true" :code="code"></highlightjs></code>
    </pre>
  </el-dialog>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { onMounted, ref, reactive } from 'vue'
import { View } from '@element-plus/icons-vue'
import {getAllResult, getResult} from '../../../api/result.js'
import vkbeautify from 'vkbeautify'
let detailDialogVisible = ref(false)
let code = ref('')
let results = reactive({
    list: []
})
const { t } = useI18n()
onMounted(async () => {
    await getAllResult()
    .then(res => {
        console.log(res.data)
        results.list = res.data
    })
    .catch(err => {
        console.log(err)
    })
})

function getResultColor(result: string) {
    if (result === 'success\n') {
      return 'success'
    }
    if (result === 'fail\n') {
      return 'danger'
    }
    return 'info'
}

async function getResultDetail(name: string, id: string) {
    detailDialogVisible.value = true
    await getResult(name, id)
    .then(res => {
        console.log(res.data)
        code.value = res.data
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