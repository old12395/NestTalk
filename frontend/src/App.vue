<script setup lang="ts">
import { darkTheme, zhCN, dateZhCN } from 'naive-ui'
import { useSettingsStore } from './stores/settings'
import AppLayout from './layouts/AppLayout.vue'

const settings = useSettingsStore()
</script>

<template>
  <n-config-provider
    :theme="settings.isDark ? darkTheme : null"
    :locale="zhCN"
    :date-locale="dateZhCN"
  >
    <n-message-provider>
      <n-dialog-provider>
        <AppLayout />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>
