<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useSettingsStore } from '@/stores/settings'
import {
  NLayout, NLayoutHeader, NLayoutSider, NLayoutContent,
  NMenu, NButton, NIcon, NSpace, NDrawer, NDrawerContent,
  NGrid, NGridItem, NTag, NH3,
} from 'naive-ui'
import {
  HomeOutline, PeopleOutline, BookOutline,
  SettingsOutline, ChatbubblesOutline, HardwareChipOutline,
  CloudOutline, NotificationsOutline, BulbOutline,
  CogOutline, MoonOutline, SunnyOutline, MenuOutline,
  HeartOutline,
} from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()
const settings = useSettingsStore()
const drawerOpen = ref(false)

const menuOptions = [
  { label: '对话', key: '/chat', icon: ChatbubblesOutline },
  { label: '仪表盘', key: '/dashboard', icon: HomeOutline },
  { label: '角色管理', key: '/characters', icon: PeopleOutline },
  { label: '世界书', key: '/worldbooks', icon: BookOutline },
  { label: '预设管理', key: '/presets', icon: SettingsOutline },
  { label: '模型配置', key: '/models', icon: HardwareChipOutline },
  { label: '平台连接', key: '/platforms', icon: CloudOutline },
  { label: '主动交互', key: '/proactive', icon: NotificationsOutline },
  { label: '记忆管理', key: '/memories', icon: BulbOutline },
  { label: '系统设置', key: '/settings', icon: CogOutline },
]

const activeKey = computed(() => route.path)

function navigate(key: string) {
  router.push(key)
  drawerOpen.value = false
}
</script>

<template>
  <n-layout class="app-layout">
    <!-- PC 端侧边栏 -->
    <n-layout-sider
      class="pc-sidebar"
      bordered
      collapse-mode="width"
      :width="220"
      :collapsed-width="64"
      show-trigger
    >
      <div class="logo">
        <n-icon size="24" color="#7c3aed"><HeartOutline /></n-icon>
        <span class="logo-text">NestTalk</span>
      </div>
      <n-menu
        :value="activeKey"
        :options="menuOptions.map(o => ({
          ...o,
          icon: () => h(NIcon, null, { default: () => h(o.icon) }),
        }))"
        @update:value="navigate"
      />
    </n-layout-sider>

    <n-layout>
      <!-- 顶部栏（移动端菜单按钮） -->
      <n-layout-header bordered class="header">
        <div class="header-left">
          <n-button
            class="mobile-menu-btn"
            quaternary
            @click="drawerOpen = true"
          >
            <n-icon size="22"><MenuOutline /></n-icon>
          </n-button>
          <span class="header-title">NestTalk</span>
        </div>
        <div class="header-right">
          <n-button quaternary @click="settings.toggleDark()">
            <n-icon size="20">
              <SunnyOutline v-if="settings.isDark" />
              <MoonOutline v-else />
            </n-icon>
          </n-button>
        </div>
      </n-layout-header>

      <!-- 内容区 -->
      <n-layout-content class="content">
        <router-view />
      </n-layout-content>
    </n-layout>

    <!-- 移动端抽屉菜单 -->
    <n-drawer v-model:show="drawerOpen" :width="260" placement="left">
      <n-drawer-content title="NestTalk" closable>
        <n-menu
          :value="activeKey"
          :options="menuOptions.map(o => ({
            ...o,
            icon: () => h(NIcon, null, { default: () => h(o.icon) }),
          }))"
          @update:value="navigate"
        />
      </n-drawer-content>
    </n-drawer>
  </n-layout>
</template>

<script lang="ts">
import { h } from 'vue'
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px;
  font-size: 18px;
  font-weight: 700;
  color: #7c3aed;
}
.logo-text {
  white-space: nowrap;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 56px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.header-title {
  font-weight: 600;
  font-size: 16px;
}
.header-right {
  display: flex;
  align-items: center;
}
.content {
  padding: 20px;
  min-height: calc(100vh - 56px);
}

.mobile-menu-btn {
  display: none;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .pc-sidebar {
    display: none;
  }
  .mobile-menu-btn {
    display: inline-flex;
  }
  .content {
    padding: 12px;
  }
}
</style>
