<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  NGrid, NGridItem, NCard, NStatistic, NIcon,
  NTag, NH3, NSpin,
} from 'naive-ui'
import { PeopleOutline, ChatbubblesOutline, FlashOutline, WalletOutline } from '@vicons/ionicons5'
import { charactersApi } from '@/api'

const loading = ref(true)
const charCount = ref(0)
const activeCount = ref(0)

onMounted(async () => {
  try {
    const res = await charactersApi.list()
    const chars = res.data
    charCount.value = chars.length
    activeCount.value = chars.filter((c: any) => c.is_active).length
  } catch (e) {
    // 后端未启动时静默
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <n-spin :show="loading">
    <div class="dashboard">
      <h3 style="margin-bottom: 16px;">🏠 仪表盘</h3>

      <n-grid :cols="4" :x-gap="12" :y-gap="12" responsive="screen">
        <n-grid-item>
          <n-card size="small">
            <n-statistic label="角色数">
              <template #prefix><n-icon><PeopleOutline /></n-icon></template>
              {{ charCount }} <span style="font-size:12px;color:#999">个</span>
            </n-statistic>
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card size="small">
            <n-statistic label="活跃角色">
              <template #prefix><n-icon :component="FlashOutline" /></template>
              {{ activeCount }} <span style="font-size:12px;color:#999">个</span>
            </n-statistic>
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card size="small">
            <n-statistic label="今日消息" :value="0">
              <template #prefix><n-icon><ChatbubblesOutline /></n-icon></template>
              <span style="font-size:12px;color:#999">条</span>
            </n-statistic>
          </n-card>
        </n-grid-item>
        <n-grid-item>
          <n-card size="small">
            <n-statistic label="Token 消耗">
              <template #prefix><n-icon :component="WalletOutline" /></template>
              0 <span style="font-size:12px;color:#999">K</span>
            </n-statistic>
          </n-card>
        </n-grid-item>
      </n-grid>

      <n-card title="🎭 活跃角色" style="margin-top: 20px;">
        <template v-if="charCount === 0">
          <n-tag type="info" size="small">暂无角色</n-tag>
          <p style="color: #999; margin-top: 8px;">
            前往「角色管理」导入你的第一个角色卡吧～
          </p>
        </template>
        <template v-else>
          <n-tag type="success" size="small">
            {{ charCount }} 个角色已就绪，{{ activeCount }} 个活跃
          </n-tag>
        </template>
      </n-card>

      <n-card title="💬 快速预览" style="margin-top: 16px;">
        <p style="color: #999;">
          连接 Telegram Bot 后，这里会显示实时对话流。
          <br/>配置 TG_BOT_TOKEN 并启动服务即可。
        </p>
      </n-card>
    </div>
  </n-spin>
</template>

<style scoped>
.dashboard { max-width: 1200px; }
@media (max-width: 768px) { .dashboard { max-width: 100%; } }
</style>
