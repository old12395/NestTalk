<script setup lang="ts">
import { ref } from 'vue'
import { NCard, NButton, NInput, NSpace, NDataTable, NTag, NPopconfirm, useMessage } from 'naive-ui'
import { SearchOutline, TrashOutline } from '@vicons/ionicons5'
import api from '@/api'

const message = useMessage()
const userId = ref('')
const query = ref('')
const searchResults = ref<any[]>([])
const searching = ref(false)

const columns = [
  { title: '内容', key: 'content', ellipsis: { tooltip: true } },
  { title: '重要性', key: 'importance', width: 80, align: 'center' as const,
    render(row: any) {
      const color = row.importance > 5 ? 'error' : row.importance > 2 ? 'warning' : 'default'
      return h(NTag, { type: color, size: 'small' }, { default: () => row.importance?.toFixed(1) })
    }
  },
  { title: '相关度', key: 'relevance', width: 80, align: 'center' as const },
]

async function doSearch() {
  if (!userId.value || !query.value) {
    message.warning('请输入用户 ID 和搜索关键词')
    return
  }
  searching.value = true
  try {
    const res = await api.post('/memories/search', {
      user_id: userId.value,
      query: query.value,
    })
    searchResults.value = res.data.results || []
    message.success(`找到 ${searchResults.value.length} 条记忆`)
  } catch (e) {
    message.error('搜索失败')
  } finally {
    searching.value = false
  }
}

async function clearMemories() {
  if (!userId.value) return
  try {
    await api.delete(`/memories/${userId.value}`)
    message.success('记忆已清空')
    searchResults.value = []
  } catch (e) {
    message.error('清空失败')
  }
}
</script>

<script lang="ts">
import { h } from 'vue'
</script>

<template>
  <div style="max-width:800px;">
    <h3 style="margin-bottom:16px;">🧠 记忆管理</h3>

    <n-card size="small" style="margin-bottom:16px;">
      <n-space vertical>
        <n-input v-model:value="userId" placeholder="用户 ID（如 Telegram 用户数字ID）" />
        <n-input v-model:value="query" placeholder="搜索关键词" @keydown.enter="doSearch" />
        <n-space>
          <n-button type="primary" @click="doSearch" :loading="searching">
            <template #icon><SearchOutline /></template>
            搜索记忆
          </n-button>
          <n-popconfirm @positive-click="clearMemories" v-if="userId">
            <template #trigger>
              <n-button type="error" ghost>
                <template #icon><TrashOutline /></template>
                清空此用户记忆
              </n-button>
            </template>
            确定清空该用户所有记忆？不可恢复。
          </n-popconfirm>
        </n-space>
      </n-space>
    </n-card>

    <n-card size="small">
      <n-dataTable
        :columns="columns"
        :data="searchResults"
        size="small"
        :row-key="(_:any,i:number)=>String(i)"
      />
      <div v-if="searchResults.length === 0" style="text-align:center;padding:40px;color:#999;">
        <p style="font-size:48px;">🧠</p>
        <p>输入用户 ID 和关键词搜索长期记忆</p>
        <p style="font-size:13px;">例如：用户ID=tg用户数字ID，关键词=喜欢</p>
      </div>
    </n-card>
  </div>
</template>
