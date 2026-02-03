import { createI18n } from 'vue-i18n'
import { messages } from '@/locales'

let i18nInstance: ReturnType<typeof createI18n> | null = null

export const getI18n = () => {
  if (!i18nInstance) {
    const storedLocale = localStorage.getItem('locale')
    const initialLocale = storedLocale === 'en' ? 'en' : 'zh'
    i18nInstance = createI18n({
      legacy: false,
      locale: initialLocale,
      fallbackLocale: 'zh',
      messages
    })
  }
  return i18nInstance
}

export const setLocale = (newLocale: string) => {
  localStorage.setItem('locale', newLocale)
  if (i18nInstance) {
    const globalLocale = i18nInstance.global.locale as { value: string }
    globalLocale.value = newLocale
  }
}

export default getI18n()
