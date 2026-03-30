<template>
  <div class="history-page">
    <div class="history-layout">
      <!-- 左侧日期选择 -->
      <aside class="date-sidebar">
        <div class="sidebar-header">
          <h3 class="sidebar-title">📅 历史日期</h3>
        </div>
        
        <!-- 加载状态 -->
        <div v-if="datesLoading" class="sidebar-loading">
          <div class="spinner"></div>
          <span>加载中...</span>
        </div>
        
        <!-- 日期列表 -->
        <div v-else class="date-list">
          <button
            v-for="date in dates"
            :key="date"
            class="date-item"
            :class="{ active: selectedDate === date }"
            @click="selectDate(date)"
          >
            <span class="date-text">{{ formatDateLabel(date) }}</span>
            <span v-if="date === today" class="today-badge">今天</span>
          </button>
        </div>
        
        <!-- 无数据提示 -->
        <div v-if="!datesLoading && dates.length === 0" class="sidebar-empty">
          <span class="empty-icon">📭</span>
          <span>暂无历史数据</span>
        </div>
      </aside>

      <!-- 右侧内容区 -->
      <main class="content-area">
        <div class="content-header">
          <h3 class="content-title">
            {{ selectedDate ? formatDateTitle(selectedDate) : '请选择日期' }}
          </h3>
          <span v-if="selectedDate" class="article-count">
            共 {{ articles.length }} 篇论文
          </span>
        </div>

        <!-- 加载状态 -->
        <div v-if="articlesLoading" class="loading-container">
          <div class="loading">
            <div class="spinner"></div>
          </div>
          <p class="loading-text">正在加载论文数据...</p>
        </div>

        <!-- 未选择日期 -->
        <div v-else-if="!selectedDate" class="empty-state-container">
          <div class="empty-state">
            <div class="empty-icon">📅</div>
            <div class="empty-title">请选择日期</div>
            <div class="empty-desc">从左侧选择日期查看历史论文</div>
          </div>
        </div>

        <!-- 空数据 -->
        <div v-else-if="articles.length === 0" class="empty-state-container">
          <div class="empty-state">
            <div class="empty-icon">📄</div>
            <div class="empty-title">该日期暂无论文</div>
            <div class="empty-desc">{{ selectedDate }} 没有收录论文</div>
          </div>
        </div>

        <!-- 论文列表 -->
        <ArticleList v-else :articles="articles" />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchDates, fetchHistoryArticles } from '../api'
import ArticleList from '../components/ArticleList.vue'

const dates = ref([])
const selectedDate = ref('')
const articles = ref([])
const datesLoading = ref(true)
const articlesLoading = ref(false)

const today = new Date().toISOString().split('T')[0]

const formatDateLabel = (dateStr) => {
  const date = new Date(dateStr)
  const month = date.getMonth() + 1
  const day = date.getDate()
  const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  const weekDay = weekDays[date.getDay()]
  return `${month}月${day}日 ${weekDay}`
}

const formatDateTitle = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
}

const loadDates = async () => {
  try {
    datesLoading.value = true
    const response = await fetchDates()
    if (response && response.dates) {
      dates.value = response.dates
      // 默认选中最近的日期
      if (dates.value.length > 0 && !selectedDate.value) {
        selectedDate.value = dates.value[0]
        loadArticles(dates.value[0])
      }
    }
  } catch (error) {
    console.error('获取日期列表失败:', error)
    dates.value = []
  } finally {
    datesLoading.value = false
  }
}

const loadArticles = async (date) => {
  if (!date) return
  
  try {
    articlesLoading.value = true
    const response = await fetchHistoryArticles(date)
    if (response) {
      articles.value = response.articles || []
    }
  } catch (error) {
    console.error('获取历史论文失败:', error)
    articles.value = []
  } finally {
    articlesLoading.value = false
  }
}

const selectDate = (date) => {
  if (selectedDate.value === date) return
  selectedDate.value = date
  loadArticles(date)
}

onMounted(() => {
  loadDates()
})
</script>

<style scoped>
.history-page {
  height: 100%;
}

.history-layout {
  display: flex;
  gap: 24px;
  min-height: calc(100vh - 140px);
}

/* 左侧日期侧边栏 */
.date-sidebar {
  width: 220px;
  flex-shrink: 0;
  background: white;
  border-radius: var(--radius);
  border: 1px solid var(--gray-200);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--gray-200);
  background: var(--gray-50);
}

.sidebar-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-700);
  margin: 0;
}

.sidebar-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  gap: 12px;
  color: var(--gray-500);
  font-size: 13px;
}

.date-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.date-item {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  margin-bottom: 4px;
  border: none;
  background: transparent;
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  color: var(--gray-700);
  text-align: left;
}

.date-item:hover {
  background: var(--gray-100);
}

.date-item.active {
  background: var(--primary);
  color: white;
}

.date-text {
  font-weight: 500;
}

.today-badge {
  font-size: 10px;
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  font-weight: 600;
}

.date-item.active .today-badge {
  background: rgba(255, 255, 255, 0.3);
}

.sidebar-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--gray-500);
  font-size: 13px;
  gap: 8px;
}

.sidebar-empty .empty-icon {
  font-size: 32px;
  opacity: 0.5;
}

/* 右侧内容区 */
.content-area {
  flex: 1;
  background: white;
  border-radius: var(--radius);
  border: 1px solid var(--gray-200);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--gray-200);
  background: var(--gray-50);
}

.content-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0;
}

.article-count {
  font-size: 13px;
  color: var(--gray-500);
}

.loading-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.loading-text {
  margin-top: 16px;
  color: var(--gray-500);
  font-size: 14px;
}

.empty-state-container {
  flex: 1;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-state {
  background: var(--gray-50);
  border-radius: var(--radius);
  border: 2px dashed var(--gray-200);
}

/* 响应式适配 */
@media (max-width: 768px) {
  .history-layout {
    flex-direction: column;
  }
  
  .date-sidebar {
    width: 100%;
    max-height: 200px;
  }
  
  .date-list {
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    padding: 12px;
    gap: 8px;
  }
  
  .date-item {
    flex-shrink: 0;
    margin-bottom: 0;
    white-space: nowrap;
  }
  
  .content-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
