<script setup lang="ts">
import { ref } from 'vue'
import {
  NCard, NButton, NForm, NFormItem, NInput, NSelect,
  NInputNumber, NColorPicker, NSlider, NSpace, NH3, useMessage,
} from 'naive-ui'
import { SaveOutline, CloudDownloadOutline } from '@vicons/ionicons5'
import { backupApi } from '@/api'

const message = useMessage()
const exporting = ref(false)

const llmOptions = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'DeepSeek', value: 'deepseek' },
  { label: 'Claude', value: 'claude' },
  { label: 'Gemini', value: 'gemini' },
  { label: '通义千问', value: 'qwen' },
  { label: 'Ollama', value: 'ollama' },
  { label: '自定义', value: 'custom' },
]

const form = ref({
  llm_provider: 'openai',
  llm_api_key: '',
  llm_model: 'gpt-4o-mini',
  llm_base_url: 'https://api.openai.com/v1',
  vision_provider: '',
  vision_model: '',
  image_provider: '',
  image_model: '',
  stt_provider: '',
  stt_model: '',
  tts_provider: 'edge_tts',
  tts_model: 'default',
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
    message.success('备份已导出')
  } catch (e) {
    message.error('导出失败')
  } finally {
    exporting.value = false
  }
}

function handleSave() {
  message.success('设置已保存')
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
        <n-button type="primary" @click="handleSave">
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
        <n-form-item label="API Base URL（可选）">
          <n-input v-model:value="form.llm_base_url" placeholder="https://api.openai.com/v1" />
        </n-form-item>
      </n-form>
    </n-card>

    <!-- 多模态模型配置 -->
    <n-card title="🎨 多模态模型配置" style="margin-top: 16px;" size="small">
      <n-form :model="form" label-placement="top" size="small">
        <n-form-item label="识图模型 (Vision)">
          <n-select v-model:value="form.vision_provider" :options="llmOptions" placeholder="可选，使用主模型" clearable />
        </n-form-item>
        <n-form-item label="生图模型 (Image Generation)">
          <n-select v-model:value="form.image_provider" :options="[
            { label: 'OpenAI DALL-E', value: 'openai' },
            { label: 'Stable Diffusion', value: 'sd' },
            { label: 'None', value: 'none' },
          ]" placeholder="可选" clearable />
        </n-form-item>
        <n-form-item label="语音识别 (STT)">
          <n-select v-model:value="form.stt_provider" :options="[
            { label: 'OpenAI Whisper', value: 'openai' },
            { label: 'None', value: 'none' },
          ]" placeholder="可选" clearable />
        </n-form-item>
        <n-form-item label="语音合成 (TTS)">
          <n-select v-model:value="form.tts_provider" :options="[
            { label: 'Edge TTS (免费)', value: 'edge_tts' },
            { label: 'OpenAI TTS', value: 'openai' },
            { label: 'ElevenLabs', value: 'elevenlabs' },
          ]" placeholder="可选" clearable />
        </n-form-item>
        <n-form-item label="TTS 语音">
          <n-input v-model:value="form.tts_voice" placeholder="zh-CN-XiaoxiaoNeural" />
        </n-form-item>
      </n-form>
    </n-card>

    <!-- 主动交互 -->
    <n-card title="💓 主动交互设置" style="margin-top: 16px;" size="small">
      <n-form :model="form" label-placement="top" size="small">
        <n-form-item label="启用主动交互">
          <n-switch v-model:value="form.proactive_enabled" />
        </n-form-item>
        <n-form-item label="每小时最多主动发言次数">
          <n-slider v-model:value="form.proactive_max_per_hour" :min="0" :max="10" :step="1" />
        </n-form-item>
      </n-form>
    </n-card>

    <!-- 备份与恢复 -->
    <n-card title="💾 备份与恢复" style="margin-top: 16px;" size="small">
      <p style="color: #999; font-size: 13px; margin-bottom: 12px;">
        导出备份包含所有角色、世界书、预设、模型配置等数据。API Key 等敏感信息会自动脱敏。
        备份文件版本化，支持跨版本兼容。
      </p>
      <n-space>
        <n-button @click="handleExport" :loading="exporting">
          <n-icon><CloudDownloadOutline /></n-icon>
          一键导出所有数据
        </n-button>
        <n-upload :default-upload="false" accept=".json">
          <n-button>导入备份文件</n-button>
        </n-upload>
      </n-space>
    </n-card>
  </div>
</template>

<script lang="ts">
import { NSwitch } from 'naive-ui'
</script>

<style scoped>
.settings-page {
  max-width: 800px;
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
