<script setup lang="ts">
import { ref, nextTick, onMounted, watch, computed } from 'vue'
import {
  NCard, NInput, NButton, NIcon, NSelect, NTag, NAvatar, NDivider,
  NPopover, NSpin, useMessage,
} from 'naive-ui'
import {
  SendOutline, ImageOutline, HappyOutline, RefreshOutline,
  PersonOutline, ChatbubbleOutline,
} from '@vicons/ionicons5'
import { chatApi, charactersApi } from '@/api'

const message = useMessage()
const chatContainer = ref<HTMLElement | null>(null)

// ─── 状态 ─────────────────────────────────

const inputText = ref('')
const sending = ref(false)
const loadingChars = ref(false)

interface ChatMsg {
  role: 'user' | 'assistant' | 'system'
  content: string
  time: string
}

const messages = ref<ChatMsg[]>([])
const characters = ref<any[]>([])
const currentChar = ref<any>(null)

// ─── 内置默认角色 ────────────────────────

const defaultChar = {
  id: '_builtin',
  name: '小栖',
  nickname: '栖栖',
  personality: '温柔、善解人意、略带俏皮。喜欢用轻松的语气聊天，偶尔会撒娇。',
  first_mes: '嗨！我是小栖～以后随时找我聊天哦，我会一直在这里陪着你 💛',
}

// ─── 初始化 ──────────────────────────────

onMounted(async () => {
  // 加载角色列表
  loadingChars.value = true
  try {
    const res = await charactersApi.list()
    characters.value = [defaultChar, ...res.data]
  } catch (e) {
    characters.value = [defaultChar]
  } finally {
    loadingChars.value = false
  }

  currentChar.value = defaultChar

  // 恢复本地历史
  const saved = localStorage.getItem('nesttalk_chat_history')
  if (saved) {
    try { messages.value = JSON.parse(saved) } catch {}
  }

  // 首次对话自动发送开场白
  if (messages.value.length === 0) {
    messages.value.push({
      role: 'assistant',
      content: currentChar.value?.first_mes || '你好！我是小栖，有什么想聊的吗？',
      time: formatTime(),
    })
  }
})

// ─── 发送消息 ────────────────────────────

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || sending.value) return

  // 用户消息
  const userMsg: ChatMsg = { role: 'user', content: text, time: formatTime() }
  messages.value.push(userMsg)
  inputText.value = ''
  scrollToBottom()

  sending.value = true

  try {
    const res = await chatApi.send({
      message: text,
      character_name: currentChar.value?.name || '小栖',
      history: buildHistory(),
    })

    const reply = res.data.content || '...'

    // 助手回复
    messages.value.push({
      role: 'assistant',
      content: reply,
      time: formatTime(),
    })
  } catch (e: any) {
    messages.value.push({
      role: 'system',
      content: `❌ 回复失败: ${e?.response?.data?.detail || e.message}`,
      time: formatTime(),
    })
  } finally {
    sending.value = false
    scrollToBottom()
    saveHistory()
  }
}

// ─── 辅助函数 ────────────────────────────

function buildHistory(): any[] {
  // 取最近 20 条
  const recent = messages.value.filter(m => m.role !== 'system').slice(-20)
  return recent.filter(m => m.role === 'user' || m.role === 'assistant')
}

function formatTime(): string {
  return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

function saveHistory() {
  try {
    const toSave = messages.value.slice(-100) // 最多保留 100 条
    localStorage.setItem('nesttalk_chat_history', JSON.stringify(toSave))
  } catch {}
}

function selectCharacter(id: string) {
  const found = characters.value.find((c: any) => c.id === id)
  if (found) {
    currentChar.value = found
    message.info(`已切换到「${found.name}」`)
  }
}

function clearChat() {
  messages.value = []
  localStorage.removeItem('nesttalk_chat_history')
  if (currentChar.value?.first_mes) {
    messages.value.push({
      role: 'assistant',
      content: currentChar.value.first_mes,
      time: formatTime(),
    })
  }
  message.success('对话已清空')
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}
</script>

<template>
  <div class="chat-page">
    <div class="page-header">
      <h3>💬 对话</h3>
      <n-space :size="8">
        <n-select
          v-model:value="currentChar?.id"
          :options="characters.map((c: any) => ({ label: c.name, value: c.id }))"
          @update:value="selectCharacter"
          size="small"
          style="width: 140px;"
          :loading="loadingChars"
        />
        <n-button quaternary size="small" @click="clearChat">
          <n-icon><RefreshOutline /></n-icon>
        </n-button>
      </n-space>
    </div>

    <!-- 角色信息栏 -->
    <div class="char-bar" v-if="currentChar">
      <n-avatar :size="32" round style="background: #7c3aed;">
        <n-icon><PersonOutline /></n-icon>
      </n-avatar>
      <div class="char-info">
        <span class="char-name">{{ currentChar.name }}</span>
        <span class="char-desc">{{ currentChar.personality?.slice(0, 30) || 'AI 陪伴者' }}...</span>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="chat-messages" ref="chatContainer">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="['message-row', msg.role]"
      >
        <!-- 助手消息 -->
        <template v-if="msg.role === 'assistant'">
          <n-avatar :size="28" round style="background: #7c3aed; flex-shrink: 0;">
            <n-icon size="16"><ChatbubbleOutline /></n-icon>
          </n-avatar>
          <div class="bubble assistant-bubble">
            <div class="bubble-text">{{ msg.content }}</div>
            <div class="bubble-time">{{ msg.time }}</div>
          </div>
        </template>

        <!-- 用户消息 -->
        <template v-else-if="msg.role === 'user'">
          <div class="bubble user-bubble">
            <div class="bubble-text">{{ msg.content }}</div>
            <div class="bubble-time">{{ msg.time }}</div>
          </div>
        </template>

        <!-- 系统消息 -->
        <template v-else>
          <div class="system-msg">{{ msg.content }}</div>
        </template>
      </div>

      <!-- 发送中指示器 -->
      <div v-if="sending" class="message-row assistant">
        <n-avatar :size="28" round style="background: #7c3aed; flex-shrink: 0;">
          <n-icon size="16"><ChatbubbleOutline /></n-icon>
        </n-avatar>
        <div class="bubble assistant-bubble typing-bubble">
          <span class="typing-dot">●</span>
          <span class="typing-dot">●</span>
          <span class="typing-dot">●</span>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input">
      <n-input
        v-model:value="inputText"
        type="textarea"
        placeholder="说点什么..."
        :autosize="{ minRows: 1, maxRows: 4 }"
        @keydown="handleKeydown"
        :disabled="sending"
        round
      />
      <n-button
        type="primary"
        circle
        :disabled="!inputText.trim() || sending"
        @click="sendMessage"
        style="flex-shrink: 0;"
      >
        <n-icon><SendOutline /></n-icon>
      </n-button>
    </div>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 56px - 40px); /* header + content padding */
  max-width: 700px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-shrink: 0;
}

/* 角色信息栏 */
.char-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: var(--n-color-modal);
  border-radius: 12px;
  margin-bottom: 12px;
  flex-shrink: 0;
}
.char-info {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.char-name {
  font-weight: 600;
  font-size: 14px;
}
.char-desc {
  font-size: 11px;
  color: #999;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
}
.message-row.user {
  justify-content: flex-end;
}
.message-row.system {
  justify-content: center;
}

/* 气泡 */
.bubble {
  max-width: 75%;
  padding: 10px 14px;
  border-radius: 16px;
  word-break: break-word;
  white-space: pre-wrap;
}
.assistant-bubble {
  background: var(--n-color-embedded);
  border-bottom-left-radius: 4px;
}
.user-bubble {
  background: #7c3aed;
  color: white;
  border-bottom-right-radius: 4px;
}
.bubble-text {
  font-size: 14px;
  line-height: 1.6;
}
.bubble-time {
  font-size: 10px;
  margin-top: 4px;
  opacity: 0.6;
  text-align: right;
}
.user-bubble .bubble-time {
  color: rgba(255,255,255,0.7);
}

/* 系统消息 */
.system-msg {
  font-size: 12px;
  color: #999;
  padding: 4px 12px;
  background: var(--n-color-embedded);
  border-radius: 8px;
}

/* 打字动画 */
.typing-bubble {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 12px 16px;
}
.typing-dot {
  font-size: 8px;
  animation: typing-bounce 1.4s infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing-bounce {
  0%, 60%, 100% { opacity: 0.3; transform: translateY(0); }
  30% { opacity: 1; transform: translateY(-4px); }
}

/* 输入区 */
.chat-input {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  padding: 10px 0 4px;
  flex-shrink: 0;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .chat-page {
    height: calc(100vh - 56px - 24px);
    max-width: 100%;
  }
  .bubble {
    max-width: 85%;
  }
  .chat-input {
    padding: 8px 0 0;
  }
}
</style>
