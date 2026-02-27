<template>
  <div class="daily-news">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <el-icon class="title-icon"><Document /></el-icon>
          {{ $t('dailyNews.title') }}
        </h1>
        <p class="page-subtitle">{{ $t('dailyNews.subtitle') }}</p>
      </div>
    </div>

    <div class="content-layout">
      <div class="records-sidebar">
        <div class="sidebar-header">
          <span>{{ $t('dailyNews.history') }}</span>
        </div>
        <div class="records-list" v-loading="loading">
          <div 
            v-for="record in pushRecords" 
            :key="record.id"
            class="record-item"
            :class="{ active: selectedRecord?.id === record.id }"
            @click="selectRecord(record)"
          >
            <div class="record-date">{{ record.push_date }}</div>
            <div class="record-type">
              <el-tag :type="record.push_type === 'morning' ? 'warning' : 'primary'" size="small">
                {{ record.push_type === 'morning' ? $t('dailyNews.morning') : $t('dailyNews.evening') }}
              </el-tag>
            </div>
            <div class="record-count">{{ record.news_count }} {{ $t('dailyNews.newsUnit') }}</div>
          </div>
          <div v-if="!loading && pushRecords.length === 0" class="empty-records">
            {{ $t('common.empty') }}
          </div>
        </div>
      </div>

      <div class="news-content" v-loading="detailLoading">
        <template v-if="selectedRecord">
          <div class="content-header">
            <div class="header-info">
              <h2 class="content-title">
                {{ selectedRecord.push_date }}
                <el-tag :type="selectedRecord.push_type === 'morning' ? 'warning' : 'primary'">
                  {{ selectedRecord.push_type === 'morning' ? $t('dailyNews.morning') : $t('dailyNews.evening') }}
                </el-tag>
              </h2>
              <div class="time-range" v-if="timeRange">
                {{ $t('dailyNews.timeRange') }}: {{ timeRange.start }} ~ {{ timeRange.end }}
              </div>
            </div>
            <div class="stats-summary">
              <div class="stat-item">
                <span class="stat-num">{{ newsItems.length }}</span>
                <span class="stat-label">{{ $t('dailyNews.newsCount') }}</span>
              </div>
              <div class="stat-item danger" v-if="dangerousPosts.length > 0">
                <span class="stat-num">{{ dangerousPosts.length }}</span>
                <span class="stat-label">{{ $t('dailyNews.dangerCount') }}</span>
              </div>
            </div>
          </div>

          <div class="news-section" v-if="newsItems.length > 0">
            <h3 class="section-title">{{ $t('dailyNews.topNews') }}</h3>
            <div class="news-list">
              <div v-for="(item, index) in newsItems" :key="item.id" class="news-item">
                <div class="news-rank">{{ index + 1 }}</div>
                <div class="news-main">
                  <div class="news-header">
                    <el-tag size="small" :type="getCategoryType(item.category)">
                      {{ getCategoryName(item.category) }}
                    </el-tag>
                    <span class="news-author">{{ item.author_name || $t('common.anonymous') }}</span>
                    <span class="news-score">{{ $t('dailyNews.importance') }}: {{ (item.importance_score || 0).toFixed(1) }}</span>
                  </div>
                  <h4 class="news-title">{{ item.title || $t('dailyNews.noTitle') }}</h4>
                  <p class="news-summary" v-if="item.summary">{{ item.summary }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="danger-section" v-if="dangerousPosts.length > 0">
            <h3 class="section-title danger">
              <el-icon><WarningFilled /></el-icon>
              {{ $t('dailyNews.dangerWarning') }}
            </h3>
            <div class="danger-list">
              <div v-for="post in dangerousPosts" :key="post.id" class="danger-item">
                <div class="danger-header">
                  <span class="danger-score">{{ post.danger_score }}/10</span>
                  <el-tag type="danger" size="small">{{ post.danger_type }}</el-tag>
                  <span class="danger-author">{{ post.author_name || $t('common.anonymous') }}</span>
                </div>
                <div class="danger-title">{{ post.title || $t('dailyNews.noTitle') }}</div>
                <div class="danger-content" v-if="post.content">{{ post.content.slice(0, 200) }}...</div>
              </div>
            </div>
          </div>

          <div class="empty-content" v-if="newsItems.length === 0 && dangerousPosts.length === 0">
            <el-empty :description="$t('common.empty')" />
          </div>
        </template>

        <div class="empty-content" v-else>
          <el-empty :description="$t('dailyNews.selectRecord')" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useLanguageStore } from '@/stores/language'
import axios from 'axios'
import { Document, WarningFilled } from '@element-plus/icons-vue'

interface PushRecord {
  id: string
  push_type: string
  push_date: string
  news_count: number
  danger_count: number
  pushed_at: string
}

interface NewsItem {
  id: string
  title: string
  summary: string
  category: string
  author_name: string
  importance_score: number
}

interface DangerousPost {
  id: string
  title: string
  content: string
  danger_score: number
  danger_type: string
  author_name: string
}

const route = useRoute()
const languageStore = useLanguageStore()

const loading = ref(false)
const detailLoading = ref(false)
const pushRecords = ref<PushRecord[]>([])
const selectedRecord = ref<PushRecord | null>(null)
const newsItems = ref<NewsItem[]>([])
const dangerousPosts = ref<DangerousPost[]>([])
const timeRange = ref<{ start: string; end: string } | null>(null)

const categoryNames: Record<string, Record<string, string>> = {
  zh: {
    society: '社会',
    technology: '技术',
    economy: '经济',
    speech: '言论',
    other: '其他'
  },
  en: {
    society: 'Society',
    technology: 'Technology',
    economy: 'Economy',
    speech: 'Speech',
    other: 'Other'
  }
}

const getCategoryName = (category: string) => {
  return categoryNames[languageStore.locale]?.[category] || category
}

const getCategoryType = (category: string): '' | 'success' | 'warning' | 'info' | 'danger' => {
  const types: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
    society: 'warning',
    technology: 'success',
    economy: 'info',
    speech: '',
    other: 'info'
  }
  return types[category] || 'info'
}

const fetchPushRecords = async () => {
  loading.value = true
  try {
    const res = await axios.get('/api/push-records', { params: { limit: 30 } })
    pushRecords.value = res.data.data || []
    
    const pushParam = route.query.push as string
    if (pushParam) {
      const record = pushRecords.value.find(r => r.id === pushParam)
      if (record) {
        selectRecord(record)
        return
      }
    }
    
    if (pushRecords.value.length > 0 && !selectedRecord.value) {
      selectRecord(pushRecords.value[0])
    }
  } catch (error) {
    console.error('Failed to fetch push records:', error)
  } finally {
    loading.value = false
  }
}

const selectRecord = async (record: PushRecord) => {
  selectedRecord.value = record
  detailLoading.value = true
  
  try {
    const res = await axios.get(`/api/push-records/${record.id}`)
    const data = res.data.data
    if (data) {
      newsItems.value = data.news || []
      dangerousPosts.value = data.dangerous_posts || []
      timeRange.value = data.time_range
    }
  } catch (error) {
    console.error('Failed to fetch push record detail:', error)
  } finally {
    detailLoading.value = false
  }
}

onMounted(() => {
  fetchPushRecords()
})
</script>

<style scoped>
.daily-news {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.title-icon {
  color: var(--accent-primary);
}

.page-subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.content-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 24px;
}

.records-sidebar {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
}

.sidebar-header {
  padding: 16px;
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color);
}

.records-list {
  max-height: 600px;
  overflow-y: auto;
}

.record-item {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  cursor: pointer;
  transition: background 0.2s;
}

.record-item:hover {
  background: rgba(59, 130, 246, 0.05);
}

.record-item.active {
  background: rgba(59, 130, 246, 0.1);
  border-left: 3px solid var(--accent-primary);
}

.record-date {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.record-type {
  margin-bottom: 4px;
}

.record-count {
  font-size: 12px;
  color: var(--text-secondary);
}

.empty-records {
  padding: 24px;
  text-align: center;
  color: var(--text-secondary);
}

.news-content {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 24px;
  min-height: 500px;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.content-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.time-range {
  font-size: 13px;
  color: var(--text-secondary);
}

.stats-summary {
  display: flex;
  gap: 24px;
}

.stat-item {
  text-align: center;
}

.stat-num {
  display: block;
  font-size: 28px;
  font-weight: 700;
  color: var(--accent-primary);
}

.stat-item.danger .stat-num {
  color: var(--accent-danger);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title.danger {
  color: var(--accent-danger);
}

.news-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.news-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.news-rank {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--accent-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex-shrink: 0;
}

.news-main {
  flex: 1;
}

.news-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.news-author {
  font-size: 13px;
  color: var(--text-secondary);
}

.news-score {
  font-size: 12px;
  color: var(--text-muted);
}

.news-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.news-summary {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.6;
}

.danger-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--border-color);
}

.danger-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.danger-item {
  padding: 16px;
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 8px;
}

.danger-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.danger-score {
  font-weight: 700;
  color: var(--accent-danger);
}

.danger-author {
  font-size: 13px;
  color: var(--text-secondary);
  margin-left: auto;
}

.danger-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.danger-content {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.empty-content {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

@media (max-width: 768px) {
  .content-layout {
    grid-template-columns: 1fr;
  }
  
  .records-sidebar {
    order: 2;
  }
  
  .news-content {
    order: 1;
  }
  
  .content-header {
    flex-direction: column;
    gap: 16px;
  }
}
</style>
