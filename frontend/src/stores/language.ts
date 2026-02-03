import { defineStore } from 'pinia'
import { ref } from 'vue'
import { setLocale as updateI18nLocale } from '@/locales/i18n'

export const useLanguageStore = defineStore('language', () => {
  const storedLocale = localStorage.getItem('locale')
  const locale = ref(storedLocale === 'en' ? 'en' : 'zh')
  updateI18nLocale(locale.value)
  
  const setLocale = (newLocale: string) => {
    locale.value = newLocale
    localStorage.setItem('locale', newLocale)
    updateI18nLocale(newLocale)
  }
  
  const toggleLocale = () => {
    const newLocale = locale.value === 'zh' ? 'en' : 'zh'
    setLocale(newLocale)
  }
  
  const isChinese = () => locale.value === 'zh'
  
  return {
    locale,
    setLocale,
    toggleLocale,
    isChinese
  }
})
