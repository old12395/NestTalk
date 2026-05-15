<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { NCard, NButton, NDataTable, NIcon, NPopconfirm, NSpace, NTag, useMessage } from 'naive-ui'
import { TrashOutline } from '@vicons/ionicons5'
import { presetsApi } from '@/api'

const message = useMessage()
const presets = ref<any[]>([])
const loading = ref(false)

const columns = [
  { title: '名称', key: 'name' },
  { title: '描述', key: 'description', ellipsis: { tooltip: true } },
  { title: '温度', key: 'temperature', width: 70, align: 'center' },
  { title: '上限', key: 'max_tokens', width: 80, align: 'center' },
  {
    title: '操作', key: 'actions', width: 80, align: 'center',
    render(row: any) {
      return h(NPopconfirm, {
        onPositiveClick: () => deletePreset(row.id),
      }, {
        trigger: () => h(NButton, { size: 'tiny', quaternary: true, type: 'error' }, {
          icon: () => h(NIcon, null, { default: () => h(TrashOutline) }),
        }),
        default: () => '确定删除此预设？',
      })
    },
  },
]

async function loadPresets() {
  loading.value = true
  try {
    const res = await presetsApi.list()
    presets.value = res.data
  } catch (e) {} finally { loading.value = false }
}

async function deletePreset(id: string) {
  try {
    await presetsApi.delete(id)
    message.success('已删除')
    loadPresets()
  } catch (e) { message.error('删除失败') }
}

onMounted(loadPresets)
</script>

<template>
  <div>
    <div class="page-header"><h3>⚙️ 预设</h3></div>
    <n-card style="margin-top:16px;">
      <n-dataTable :columns="columns" :data="presets" :loading="loading" size="small" :row-key="(r:any)=>r.id" />
      <div v-if="!loading && presets.length===0" style="text-align:center;padding:40px;color:#999;">
        <p>还没有预设</p>
        <p style="font-size:13px;">预设控制 LLM 的回复风格和行为参数</p>
      </div>
    </n-card>
  </div>
</template>

<style scoped>
.page-header{display:flex;justify-content:space-between;align-items:center}
@media(max-width:768px){.page-header{flex-direction:column;align-items:flex-start}}
</style>
