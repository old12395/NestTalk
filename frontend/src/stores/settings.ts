import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  const isDark = ref(false)
  const isMobileMenuOpen = ref(false)

  function toggleDark() {
    isDark.value = !isDark.value
  }

  function toggleMobileMenu() {
    isMobileMenuOpen.value = !isMobileMenuOpen.value
  }

  return { isDark, isMobileMenuOpen, toggleDark, toggleMobileMenu }
})
