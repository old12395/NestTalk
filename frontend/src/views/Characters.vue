<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  NCard, NButton, NDataTable, NIcon, NUpload, NModal, NTag,
  NPopconfirm, NSpace, NH3, useMessage,
} from 'naive-ui'
import { AddOutline, CloudUploadOutline, TrashOutline, CreateOutline } from '@vicons/ionicons5'
import { charactersApi } from '@/api'

const message = useMessage()
const characters = ref<any[]>([])
const loading = ref(false)
const uploadVisible = ref(false)

const columns = [
  { title: '头像', key: 'avatar', width: 60 },
  { title: '名称', key: 'name' },
  { title: '版本', key: 'spec_version', width: 80 },
  { title: '对话数', key: 'total_chats', width: 80 },
  { title: '状态', key: 'is_active', width: 80 },
  {
    title: '操作', key: 'actions', width: 120,
    render(row: any) {
      return h(NSpace, null, {
        default: () => [
          h(NButton, { size: 'tiny', quaternary: true }, {
            icon: () => h(NIcon, null, { default: () => h(CreateOutline) }),
          }),
          h(NPopconfirm, { onPositiveClick: () => deleteChar(row.id) }, {
            trigger: () => h(NButton, { size: 'tiny', quaternary: true, type: 'error' }, {
              icon: () => h(NIcon, null, { default: () => h(TrashOutline) }),
            }),
            default: () => '确定删除此角色？',
          }),
        ],
      })
    },
  },
]

async function loadCharacters() {
  loading.value = true
  try {
    const res = await charactersApi.list()
    characters.value = res.data
  } catch (e) {
    message.error('加载角色列表失败')
  } finally {
    loading.value = false
  }
}

async function handleUpload({ file }: any) {
  if (!file.file) return
  try {
    await charactersApi.import(file.file)
    message.success('角色卡导入成功')
    uploadVisible.value = false
    loadCharacters()
  } catch (e) {
    message.error('导入失败，请检查文件格式')
  }
}

async function deleteChar(id: string) {
  try {
    await charactersApi.delete(id)
    message.success('已删除')
    loadCharacters()
  } catch (e) {
    message.error('删除失败')
  }
}

onMounted(loadCharacters)
</script>

<script lang="ts">
import { h } from 'vue'
</script>

<template>
  <div class="characters-page">
    <div class="page-header">
      <h3>🎭 角色管理</h3>
      <n-space>
        <n-button type="primary" @click="uploadVisible = true">
          <n-icon><CloudUploadOutline /></n-icon>
          导入角色卡
        </n-button>
      </n-space>
    </div>

    <n-card style="margin-top: 16px;">
      <n-dataTable
        :columns="columns"
        :data="characters"
        :loading="loading"
        :bordered="false"
        size="small"
      />
      <div v-if="!loading && characters.length === 0" style="text-align: center; padding: 40px; color: #999;">
        <p>还没有角色</p>
        <p style="font-size: 13px;">支持导入 PNG / CHARX / JSON 格式的角色卡</p>
      </div>
    </n-card>

    <!-- 上传弹窗 -->
    <n-modal v-model:show="uploadVisible" title="导入角色卡">
      <n-card style="width: 400px;" title="上传角色卡文件">
        <n-upload
          :default-upload="false"
          accept=".png,.charx,.json"
          @change="handleUpload"
        >
          <n-button>选择文件</n-button>
        </n-upload>
        <p style="margin-top: 12px; color: #999; font-size: 13px;">
          支持 Character Card V2 / V3 格式
        </p>
      </n-card>
    </n-modal>
  </div>
</template>

<style scoped>
.characters-page {
  max-width: 1200px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
