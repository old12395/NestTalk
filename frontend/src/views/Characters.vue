<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import {
  NCard, NButton, NDataTable, NIcon, NUpload, NModal,
  NPopconfirm, NSpace, NH3, NTag, useMessage, NForm, NFormItem, NInput,
} from 'naive-ui'
import { AddOutline, CloudUploadOutline, TrashOutline, CreateOutline } from '@vicons/ionicons5'
import { charactersApi } from '@/api'

const message = useMessage()
const characters = ref<any[]>([])
const loading = ref(false)
const uploadVisible = ref(false)
const editing = ref<any>(null)
const editVisible = ref(false)

const columns: any[] = [
  { title: '名称', key: 'name', width: 150, ellipsis: { tooltip: true } },
  { title: '版本', key: 'spec_version', width: 60 },
  { title: '对话', key: 'total_chats', width: 60, align: 'center' },
  {
    title: '状态', key: 'is_active', width: 70, align: 'center',
    render(row: any) {
      return h(NTag, { type: row.is_active ? 'success' : 'default', size: 'small' }, {
        default: () => row.is_active ? '活跃' : '停用',
      })
    },
  },
  {
    title: '操作', key: 'actions', width: 100, align: 'center',
    render(row: any) {
      return h(NSpace, { justify: 'center' }, {
        default: () => [
          h(NButton, {
            size: 'tiny', quaternary: true,
            onClick: () => startEdit(row),
          }, {
            icon: () => h(NIcon, null, { default: () => h(CreateOutline) }),
          }),
          h(NPopconfirm, {
            onPositiveClick: () => deleteChar(row.id),
          }, {
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
    const res = await charactersApi.import(file.file)
    message.success(`角色「${res.data.name}」导入成功`)
    uploadVisible.value = false
    loadCharacters()
  } catch (e: any) {
    const detail = e?.response?.data?.detail || '请检查文件格式'
    message.error(`导入失败: ${detail}`)
  }
}

async function deleteChar(id: string) {
  try {
    await charactersApi.delete(id)
    message.success('已删除')
    loadCharacters()
  } catch (e) { message.error('删除失败') }
}

function startEdit(row: any) {
  editing.value = { ...row }
  editVisible.value = true
}

async function saveEdit() {
  if (!editing.value) return
  try {
    await charactersApi.update(editing.value.id, {
      name: editing.value.name,
      nickname: editing.value.nickname,
      description: editing.value.description,
      personality: editing.value.personality,
      scenario: editing.value.scenario,
      first_mes: editing.value.first_mes,
      is_active: editing.value.is_active,
    })
    message.success('角色已更新')
    editVisible.value = false
    loadCharacters()
  } catch (e) { message.error('更新失败') }
}

onMounted(loadCharacters)
</script>

<template>
  <div class="characters-page">
    <div class="page-header">
      <h3>🎭 角色管理</h3>
      <n-space>
        <n-button @click="uploadVisible = true">
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
        :row-key="(r: any) => r.id"
      />
      <div v-if="!loading && characters.length === 0" style="text-align: center; padding: 40px; color: #999;">
        <p style="font-size: 48px;">🎭</p>
        <p>还没有角色，导入你的第一个角色卡吧</p>
        <p style="font-size: 13px;">支持 PNG / CHARX / JSON (Character Card V2 & V3)</p>
      </div>
    </n-card>

    <!-- 上传弹窗 -->
    <n-modal v-model:show="uploadVisible" title="导入角色卡">
      <n-card style="width: 400px; max-width: 90vw;" title="上传角色卡文件">
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

    <!-- 编辑弹窗 -->
    <n-modal v-model:show="editVisible" title="编辑角色">
      <n-card style="width: 500px; max-width: 90vw;">
        <n-form v-if="editing" label-placement="top" size="small">
          <n-form-item label="名称">
            <n-input v-model:value="editing.name" />
          </n-form-item>
          <n-form-item label="昵称">
            <n-input v-model:value="editing.nickname" />
          </n-form-item>
          <n-form-item label="描述">
            <n-input v-model:value="editing.description" type="textarea" :rows="3" />
          </n-form-item>
          <n-form-item label="性格">
            <n-input v-model:value="editing.personality" type="textarea" :rows="3" />
          </n-form-item>
          <n-form-item label="开场白">
            <n-input v-model:value="editing.first_mes" type="textarea" :rows="2" />
          </n-form-item>
        </n-form>
        <n-space justify="end" style="margin-top: 16px;">
          <n-button @click="editVisible = false">取消</n-button>
          <n-button type="primary" @click="saveEdit">保存</n-button>
        </n-space>
      </n-card>
    </n-modal>
  </div>
</template>

<style scoped>
.characters-page { max-width: 1200px; }
.page-header {
  display: flex; justify-content: space-between;
  align-items: center; flex-wrap: wrap; gap: 8px;
}
@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; }
}
</style>
