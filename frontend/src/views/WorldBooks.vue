<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { NCard, NButton, NDataTable, NIcon, NModal, NPopconfirm, NSpace, NTag, useMessage } from 'naive-ui'
import { TrashOutline, AddOutline } from '@vicons/ionicons5'
import { worldbooksApi } from '@/api'

const message = useMessage()
const worldbooks = ref<any[]>([])
const loading = ref(false)

const columns = [
  { title: '名称', key: 'name' },
  { title: '描述', key: 'description', ellipsis: { tooltip: true } },
  {
    title: '条数', key: 'entries', width: 80, align: 'center',
    render(row: any) {
      return Object.keys(row.entries || {}).length
    },
  },
  { title: '类型', key: 'is_global', width: 80, align: 'center',
    render(row: any) {
      return h(NTag, { type: row.is_global ? 'info' : 'default', size: 'small' }, {
        default: () => row.is_global ? '全局' : '角色',
      })
    },
  },
  {
    title: '操作', key: 'actions', width: 80, align: 'center',
    render(row: any) {
      return h(NPopconfirm, {
        onPositiveClick: () => deleteWb(row.id),
      }, {
        trigger: () => h(NButton, { size: 'tiny', quaternary: true, type: 'error' }, {
          icon: () => h(NIcon, null, { default: () => h(TrashOutline) }),
        }),
        default: () => '确定删除此世界书？',
      })
    },
  },
]

async function loadWorldbooks() {
  loading.value = true
  try {
    const res = await worldbooksApi.list()
    worldbooks.value = res.data
  } catch (e) {
    // 静默
  } finally {
    loading.value = false
  }
}

async function deleteWb(id: string) {
  try {
    await worldbooksApi.delete(id)
    message.success('已删除')
    loadWorldbooks()
  } catch (e) { message.error('删除失败') }
}

onMounted(loadWorldbooks)
</script>

<template>
  <div>
    <div class="page-header">
      <h3>📚 世界书</h3>
    </div>
    <n-card style="margin-top: 16px;">
      <n-dataTable :columns="columns" :data="worldbooks" :loading="loading" size="small" :row-key="(r:any)=>r.id" />
      <div v-if="!loading && worldbooks.length === 0" style="text-align:center;padding:40px;color:#999;">
        <p>还没有世界书</p>
        <p style="font-size:13px;">世界书为角色提供动态背景知识</p>
      </div>
    </n-card>
  </div>
</template>

<style scoped>
.page-header { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; }
@media(max-width:768px){.page-header{flex-direction:column;align-items:flex-start}}
</style>
