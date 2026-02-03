<script setup lang="ts">
import { RouterView, useRoute } from 'vue-router'
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { 
  DataLine, 
  Document, 
  Share, 
  UserFilled,
  Monitor,
  Switch
} from '@element-plus/icons-vue'
import { useLanguageStore } from '@/stores/language'

const route = useRoute()
const languageStore = useLanguageStore()
const { t, locale } = useI18n()
const activeMenu = computed(() => route.path)

const menuItems = [
  { path: '/dashboard', name: 'dashboard', labelKey: 'menu.dashboard', icon: DataLine },
  { path: '/feed', name: 'feed', labelKey: 'menu.feed', icon: Document },
  { path: '/agents', name: 'agents', labelKey: 'menu.agents', icon: UserFilled },
  { path: '/network', name: 'network', labelKey: 'menu.network', icon: Share },
]

const toggleLanguage = () => {
  languageStore.toggleLocale()
}

// 监听语言变化更新标题
watch(() => locale.value, (newLocale) => {
  const titleKey = route.meta.labelKey as string || (route.name ? `menu.${String(route.name)}` : '')
  if (titleKey) {
    document.title = `${t(titleKey)} - ${t('app.name')}`
  }
}, { immediate: true })

// 监听路由变化更新标题
watch(() => route.path, () => {
  const titleKey = route.meta.labelKey as string || (route.name ? `menu.${String(route.name)}` : '')
  if (titleKey) {
    document.title = `${t(titleKey)} - ${t('app.name')}`
  }
})
</script>

<template>
  <div class="app-container">
    <main class="main-content">
      <header class="top-header">
        <div class="header-left">
          <div class="brand">
            <div class="logo-icon">
              <el-icon size="22"><Monitor /></el-icon>
            </div>
            <div class="logo-text">
              <h1>{{ t('app.name') }}</h1>
              <span class="tagline">{{ t('app.tagline') }}</span>
            </div>
          </div>
          <nav class="top-tabs">
            <router-link
              v-for="item in menuItems"
              :key="item.path"
              :to="item.path"
              :class="['tab-item', { active: activeMenu === item.path }]"
            >
              <el-icon size="16"><component :is="item.icon" /></el-icon>
              <span>{{ t(item.labelKey) }}</span>
            </router-link>
          </nav>
        </div>
        
        <div class="header-actions">
          <button class="lang-switch-btn" @click="toggleLanguage">
            <el-icon size="14"><Switch /></el-icon>
            <span>{{ locale === 'zh' ? t('common.english') : t('common.chinese') }}</span>
          </button>
        </div>
      </header>
      
      <div class="content-wrapper">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  /* 深色科技主题配色 */
  --bg-primary: #0a0f1c;
  --bg-secondary: #111827;
  --bg-tertiary: #1f2937;
  --bg-card: rgba(30, 41, 59, 0.4);
  --bg-card-hover: rgba(30, 41, 59, 0.6);
  
  --accent-primary: #3b82f6;
  --accent-secondary: #06b6d4;
  --accent-success: #10b981;
  --accent-warning: #f59e0b;
  --accent-danger: #ef4444;
  
  --text-primary: #f9fafb;
  --text-secondary: #9ca3af;
  --text-muted: #6b7280;
  
  --border-color: rgba(75, 85, 99, 0.4);
  --border-glow: rgba(59, 130, 246, 0.3);
  
  --sidebar-width: 260px;
  --sidebar-collapsed-width: 64px;
  --header-height: 64px;
}

/* 响应式侧边栏宽度 */
@media (max-width: 1024px) {
  :root {
    --sidebar-width: 200px;
  }
}

@media (max-width: 768px) {
  :root {
    --sidebar-width: 0px;
  }
  
  .sidebar {
    width: 260px;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    z-index: 200;
  }
  
  .sidebar.open {
    transform: translateX(0);
  }
  
  .sidebar-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 99;
  }
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
  overflow-x: hidden;
}

/* 防止内容溢出 */
* {
  box-sizing: border-box;
}

img, svg {
  max-width: 100%;
  height: auto;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--bg-tertiary);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--bg-primary);
  width: 100vw;
  overflow-x: hidden;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3);
  flex-shrink: 0;
}

.logo-icon :deep(svg) {
  width: 22px;
  height: 22px;
}

.logo-text h1 {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, var(--text-primary), var(--accent-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

.tagline {
  font-size: 12px;
  color: var(--text-muted);
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  width: 100%;
  max-width: none;
}

/* 顶部导航 */
.top-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 64px;
  padding: 0 24px;
  background: rgba(17, 24, 39, 0.8);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 40px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.top-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid var(--border-color);
  border-radius: 999px;
  flex-wrap: wrap;
}

.tab-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 999px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.tab-item :deep(svg) {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.tab-item:hover {
  color: var(--text-primary);
  background: rgba(59, 130, 246, 0.15);
}

.tab-item.active {
  color: var(--text-primary);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(6, 182, 212, 0.25));
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: 0 6px 18px rgba(59, 130, 246, 0.2);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.lang-switch-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(6, 182, 212, 0.2));
  border: 1px solid rgba(59, 130, 246, 0.4);
  border-radius: 20px;
  color: var(--accent-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.lang-switch-btn:hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(6, 182, 212, 0.3));
  border-color: var(--accent-primary);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.lang-switch-btn .el-icon {
  color: var(--accent-primary);
}

/* 内容包装器 */
.content-wrapper {
  flex: 1;
  padding: 24px 32px;
  background: var(--bg-primary);
  width: 100%;
  max-width: 100%;
  overflow-x: visible;
}

@media (max-width: 1024px) {
  .content-wrapper {
    padding: 20px 24px;
  }
}

@media (max-width: 768px) {
  .content-wrapper {
    padding: 16px;
  }
  
  .top-header {
    padding: 0 16px;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .header-left {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .top-tabs {
    width: 100%;
    overflow-x: auto;
    justify-content: flex-start;
  }
}

/* Element Plus 深色主题覆盖 */
:deep(.el-card) {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

:deep(.el-card__header) {
  border-bottom: 1px solid var(--border-color);
  padding: 16px 20px;
}

:deep(.el-table) {
  background: transparent;
}

:deep(.el-table th) {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

:deep(.el-table td) {
  background: transparent;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color);
}

:deep(.el-table--enable-row-hover .el-table__body tr:hover > td) {
  background: var(--bg-card-hover);
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  border: none;
}

:deep(.el-input__wrapper) {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  box-shadow: none;
}

:deep(.el-input__inner) {
  color: var(--text-primary);
}
</style>
