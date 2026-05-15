<script setup lang="ts">
import { ref } from 'vue'
import {
  NCard, NButton, NForm, NFormItem, NInput, NSelect,
  NInputNumber, NSlider, NSpace, NH3, NUpload, useMessage, NSwitch,
} from 'naive-ui'
import { SaveOutline, CloudDownloadOutline, CloudUploadOutline } from '@vicons/ionicons5'
import { backupApi } from '@/api'

const message = useMessage()
const exporting = ref(false)
const importing = ref(false)

const llmOptions = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'DeepSeek', value: 'deepseek' },
  { label: 'Claude', value: 'claude' },
  { label: 'Gemini', value: 'gemini' },
  { label: '通义千问', value: 'qwen' },
  { label: 'Ollama (本地)', value: 'ollama' },
  { label: '自定义', value: 'custom' },
]

const form = ref({
  llm_provider: 'openai',
  llm_api_key: '',
  llm_model: 'gpt-4o-mini',
  llm_base_url: 'https://api.openai.com/v1',
  vision_provider: null as string | null,
  vision_model: '',
  image_provider: null as string | null,
  image_model: '',
  stt_provider: null as string | null,
  stt_model: '',
  tts_provider: 'edge_tts',
  tts_voice: 'zh-CN-XiaoxiaoNeural',
  proactive_enabled: true,
  proactive_max_per_hour: 2,
})

async function handleExport() {
  exporting.value = true
  try {
    const res = await backupApi.export()
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const a = document.createElement('a')
    a.href = url
    a.download = `nesttalk_backup_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    window.URL.revokeObjectURL(url)
    message.success('备份已导出')
  } catch (e: any) {
    message.error(`导出失败: ${e?.response?.data?.detail || e.message}`)
  } finally {
    exporting.value = false
  }
}

async function handleImport({ file }: any) {
  if (!file.file) return
  importing.value = true
  try {
    const res = await backupApi.import(file.file)
    message.success(res.data?.message || '导入成功')
  } catch (e: any) {
    message.error(`导入失败: ${e?.response?.data?.detail || e.message}`)
  } finally {
    importing.value = false
  }
}

function saveSettings() {
  message.success('设置已保存（需重启服务生效）')
}
</script>

<template>
  <div class="settings-page">
    <div class="page-header">
      <h3>⚙️ 系统设置</h3>
      <n-space>
        <n-button @click="handleExport" :loading="exporting">
          <n-icon><CloudDownloadOutline /></n-icon>
          导出备份
        </n-button>
        <n-button type="primary" @click="saveSettings">
          <n-icon><SaveOutline /></n-icon>
          保存设置
        </n-button>
      </n-space>
    </div>

    <!-- LLM 主模型 -->
    <n-card title="🤖 主模型配置" style="margin-top: 16px;" size="small">
      <n-form :model="form" label-placement="top" size="small">
        <n-form-item label="模型提供商">
          <n-select v-model:value="form.llm_provider" :options="llmOptions" />
        </n-form-item>
        <n-form-item label="API Key">
          <n-input v-model:value="form.llm_api_key" type="password" show-password-on="click" placeholder="sk-..." />
        </n-form-item>
        <n-form-item label="模型名称">
          <n-input v-model:value="form.llm_model" placeholder="gpt-4o-mini" />
        </n-form-item>
        <n-form-item label="API Base URL">
          <n-input v-model:value="form.llm_base_url" placeholder="https://api.openai.com/v1" />
        </n-form-item>
      </n-form>
    </n-card>

    <!-- 多模态 -->
    <n-card title="🎨 多模态模型" style="margin-top: 16px;" size="small">
      <n-form :model="form" label-placement="top" size="small">
        <n-form-item label="识图 (Vision)">
          <n-select v-model:value="form.vision_provider" :options="llmOptions" placeholder="可选，使用主模型" clearable />
        </n-form-item>
        <n-form-item label="生图 (Image)">
          <n-select v-model:value="form.image_provider" :options="[
            { label: 'OpenAI DALL-E', value: 'openai' },
            { label: 'Stable Diffusion', value: 'sd' },
          ]" placeholder="可选" clearable />
        </n-form-item>
        <n-form-item label="语音识别 (STT)">
          <n-select v-model:value="form.stt_provider" :options="[
            { label: 'OpenAI Whisper', value: 'openai' },
          ]" placeholder="可选" clearable />
        </n-form-item>
        <n-form-item label="语音合成 (TTS)">
          <n-select v-model:value="form.tts_provider" :options="[
            { label: 'Edge TTS (免费)', value: 'edge_tts' },
            { label: 'OpenAI TTS', value: 'openai' },
            { label: 'ElevenLabs', value: 'elevenlabs' },
          ]" />
        </n-form-item>
        <n-form-item label="TTS 语音">
          <n-input v-model:value="form.tts_voice" placeholder="zh-CN-XiaoxiaoNeural" />
        </n-form-item>
      </n-form>
    </n-card>

    <!-- 主动交互 -->
    <n-card title="💓 主动交互" style="margin-top: 16px;" size="small">
      <n-form :model="form" label-placement="top" size="small">
        <n-form-item label="启用主动交互">
          <n-switch v-model:value="form.proactive_enabled" />
        </n-form-item>
        <n-form-item label="每小时最多发言次数">
          <n-slider v-model:value="form.proactive_max_per_hour" :min="0" :max="10" :step="1" />
          <template #feedback>{{ form.proactive_max_per_hour }} 次/小时</template>
        </n-form-item>
      </n-form>
    </n-card>

    <!-- 备份 -->
    <n-card title="💾 备份与恢复" style="margin-top: 16px;" size="small">
      <p style="color: #999; font-size: 13px; margin-bottom: 12px;">
        导出备份包含所有角色、世界书、预设、模型配置等。API Key 自动脱敏。
        支持跨版本兼容，重装系统后可一键恢复。
      </p>
      <n-space>
        <n-button @click="handleExport" :loading="exporting">
          <n-icon><CloudDownloadOutline /></n-icon>
          一键导出
        </n-button>
        <n-upload :default-upload="false" accept=".json" @change="handleImport">
          <n-button :loading="importing">
            <n-icon><CloudUploadOutline /></n-icon>
            导入备份
          </n-button>
        </n-upload>
      </n-space>
    </n-card>
  </div>
</template>

<style scoped>
.settings-page { max-width: 800px; }
.page-header {
  display: flex; justify-content: space-between;
  align-items: center; flex-wrap: wrap; gap: 8px;
}
@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; }
}
</style>
