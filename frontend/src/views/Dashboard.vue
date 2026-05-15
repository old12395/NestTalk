<script setup lang="ts">
import {
  NGrid, NGridItem, NCard, NStatistic, NIcon,
  NTag, NH3,
} from 'naive-ui'
import { PeopleOutline, ChatbubblesOutline, FlashOutline, WalletOutline } from '@vicons/ionicons5'

const stats = [
  { label: '角色数', value: 0, icon: PeopleOutline, suffix: '个' },
  { label: '今日消息', value: 0, icon: ChatbubblesOutline, suffix: '条' },
  { label: 'Token 消耗', value: 0, icon: FlashOutline, suffix: 'K' },
  { label: '今日费用', value: '0.00', icon: WalletOutline, prefix: '$' },
]
</script>

<template>
  <div class="dashboard">
    <h3 style="margin-bottom: 16px;">🏠 仪表盘</h3>

    <!-- 统计卡片 -->
    <n-grid :cols="4" :x-gap="12" :y-gap="12" responsive="screen">
      <n-grid-item v-for="item in stats" :key="item.label">
        <n-card size="small">
          <n-statistic :label="item.label">
            <template #prefix>
              <n-icon :component="item.icon" />
            </template>
            {{ item.prefix }}{{ item.value }}{{ item.suffix }}
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 活跃角色 -->
    <n-card title="🎭 活跃角色" style="margin-top: 20px;">
      <n-tag type="info" size="small">暂无活跃角色</n-tag>
      <p style="color: #999; margin-top: 8px;">
        导入角色卡后，这里会显示角色状态。
      </p>
    </n-card>

    <!-- 最近对话 -->
    <n-card title="💬 最近对话" style="margin-top: 16px;">
      <p style="color: #999;">还没有对话记录</p>
    </n-card>
  </div>
</template>

<style scoped>
.dashboard {
  max-width: 1200px;
}

@media (max-width: 768px) {
  .dashboard {
    max-width: 100%;
  }
}
</style>
