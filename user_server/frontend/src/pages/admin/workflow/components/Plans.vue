<template>
  <el-card shadow="hover">
    <template #header>
        <div class="card-header">
            <span class="card-title font-medium font-serif text-xl text-blue-900 text-opacity-85">
                Plan
            </span>
            <el-button @click="addNewItem">Add Plan</el-button>
        </div>
    </template>
    <el-form  :model="item" ref="item" :rules="rules" label-width="120px" v-for="(item, index) in planForm.items" :key="index" :label="`Item ${index + 1}`">
        <el-row>
        <el-col :span="23">
            <el-form-item label="Action Type">
            <el-select class="input" v-model="item.actionType"  size="large">
                    <el-option
                    v-for="(item, index) in actionType"
                    :key="item"
                    :label="item"
                    :value="item"
                    />
                </el-select>
            </el-form-item>
            <el-form-item v-if="item.actionType == 'pauseAPIServer' || item.actionType == 'resumeAPIServer'" label="APIServer Name">
                <el-select class="input" v-model="item.actionArgs[0]"  size="large">
                    <el-option
                    v-for="(item, index) in apiserver"
                    :key="item"
                    :label="item"
                    :value="item"
                    />
                </el-select>
            </el-form-item>
            <el-form-item v-if="item.actionType == 'pauseAPIServer' || item.actionType == 'resumeAPIServer'" label="Pause Scope">
                <el-input class="input" v-model="item.actionArgs[1]"></el-input>
            </el-form-item>

            <el-form-item v-if="item.actionType == 'pauseController' || item.actionType == 'resumeController'" label="Pause At">
                <el-input class="input" v-model="item.actionArgs[0]"></el-input>
            </el-form-item>
            <el-form-item v-if="item.actionType == 'pauseController' || item.actionType == 'resumeController'" label="Pause Scope">
                <el-input class="input" v-model="item.actionArgs[1]"></el-input>
            </el-form-item>

            <el-form-item v-if="item.actionType == 'reconnectController'" label="Reconnected APIServer">
                <el-select class="input" v-model="item.actionArgs[0]"  size="large">
                    <el-option
                    v-for="(item, index) in apiserver"
                    :key="item"
                    :label="item"
                    :value="item"
                    />
                </el-select>
            </el-form-item>

            <el-form-item v-if="item.actionType == 'delayAPIServer'" label="APIServer Name">
                <el-select class="input" v-model="item.actionArgs[0]"  size="large">
                    <el-option
                    v-for="(item, index) in apiserver"
                    :key="item"
                    :label="item"
                    :value="item"
                    />
                </el-select>
            </el-form-item>
            <el-form-item v-if="item.actionType == 'delayAPIServer'" label="Delay Time(s)">
                <el-input class="input" v-model="item.actionArgs[1]"></el-input>
            </el-form-item>
            <el-form-item v-if="item.actionType == 'delayAPIServer'" label="Delay Scope">
                <el-input class="input" v-model="item.actionArgs[2]"></el-input>
            </el-form-item>
        </el-col>
        <el-col :span="1">
            <el-button @click="deleteItem(index)" type="danger" :icon="Delete" circle />
        </el-col>
        </el-row>
        
        <Triggers :triggerForm="item.triggerForm"></Triggers>
        <el-divider/>
    </el-form> 
    
  </el-card>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue';
import Triggers from './Triggers.vue'
import {Delete} from '@element-plus/icons-vue'

const props = defineProps({
    apiserver: Array,
    planForm: {
        items: [
            { actionType: '' ,
                actionArgs: ['', '', ''],
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
    }
})

const actionType = [
    'pauseAPIServer',
    'resumeAPIServer',
    'pauseController',
    'resumeController',
    'pauseControllerWrite',
    'resumeControllerWrite',
    'restartController',
    'reconnectController',
    'delayAPIServer',
    'omitEvent'
]

const conditionType = [
    'onObjectCreate',
    'onObjectDelete',
    'onObjectUpdate',
    'onAnyFieldModification',
    'onTimeout',
    'onAnnotatedAPICall',
]

const observedWhen = [
    'beforeAPIServerRecv',
    'afterAPIServerRecv',
    'beforeControllerRecv',
    'afterControllerRecv',
    'beforeControllerWrite',
    'afterControllerWrite',
    'beforeControllerRead',
    'afterControllerRead',
    'beforeAnnotatedAPICall',
    'afterAnnotatedAPICall',
]

onMounted(() => {
    console.log(props.apiserver)
})

const deleteItem = (idx) => {
    props.planForm.items.splice(idx, 1)
}


// const triggerForm = reactive({items: [
//         { name: '123aaaa' ,
//             conditionType: '',
//             resourceKey: '',
//             observedWhen: '',
//             observedBy: ''
//         },
//         ]})
        
// const form = reactive({
//     items: [
//     { actionType: '' ,
//         actionArgs: '',
//         conditionType: '',
//         resourceKey: '',
//         observedWhen: '',
//         observedBy: ''
//     },
//     ],
// });


const addNewItem = () => {
    console.log("!!!")
    props.planForm.items.push({ name: '' ,
        conditionType: '',
        resourceKey: '',
        observedWhen: '',
        observedBy: '',
        triggerForm: {
            items: [
            { name: '' ,
                conditionType: '',
                resourceKey: '',
                observedWhen: '',
                observedBy: ''
            },
            ]
        }
    });
};

</script>

<style scoped>

.input {
    width: 60%;
}
.paper-list:hover {
    color: #3b82f6;
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
