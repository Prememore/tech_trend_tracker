<template>
  <div class="today-trends">
    <!-- 统计卡片 -->
    <div class="stats-cards">
      <div class="stat-card">
        <div class="stat-icon">📚</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_articles || 0 }}</div>
          <div class="stat-label">数据库总论文数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📰</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.today_count || 0 }}</div>
          <div class="stat-label">今日论文数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📅</div>
        <div class="stat-content">
          <div class="stat-value">{{ dateRange }}</div>
          <div class="stat-label">数据时间范围</div>
        </div>
      </div>
    </div>

    <!-- 今日论文列表 -->
    <div class="content-section">
      <div class="section-header">
        <h3 class="section-title">
          📊 今日论文
          <span v-if="todayDate" class="date-badge">{{ todayDate }}</span>
        </h3>
        <span class="article-count">共 {{ articles.length }} 篇</span>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <div class="loading">
          <div class="spinner"></div>
        </div>
        <p class="loading-text">正在加载今日论文...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="articles.length === 0" class="empty-state-container">
        <div class="empty-state">
          <div class="empty-icon">📭</div>
          <div class="empty-title">今日暂无新论文</div>
          <div class="empty-desc">请尝试更新文献以获取最新内容</div>
          <router-link to="/update" class="btn btn-primary mt-4">
            前往更新文献
          </router-link>
        </div>
      </div>

      <!-- 论文列表 -->
      <ArticleList v-else :articles="articles" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchTodayArticles, fetchStats } from '../api'
import ArticleList from '../components/ArticleList.vue'

const loading = ref(true)
const articles = ref([])
const todayDate = ref('')
const stats = ref({
  total_articles: 0,
  today_count: 0,
  date_range: null
})

const dateRange = computed(() => {
  if (!stats.value.date_range) return '-'
  const { earliest, latest } = stats.value.date_range
  if (!earliest || !latest) return '-'
  
  const earliestDate = new Date(earliest).toLocaleDateString('zh-CN')
  const latestDate = new Date(latest).toLocaleDateString('zh-CN')
  
  if (earliestDate === latestDate) {
    return earliestDate
  }
  return `${earliestDate} ~ ${latestDate}`
})

const loadTodayArticles = async () => {
  try {
    loading.value = true
    const response = await fetchTodayArticles()
    if (response) {
      articles.value = response.articles || []
      todayDate.value = response.date || new Date().toISOString().split('T')[0]
    }
  } catch (error) {
    console.error('获取今日论文失败:', error)
    articles.value = []
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await fetchStats()
    if (response) {
      stats.value = response
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

onMounted(() => {
  loadTodayArticles()
  loadStats()
})
</script>

<style scoped>
.today-trends {
  padding-bottom: 24px;
}

.stats-cards {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.stat-card {
  flex: 1;
  min-width: 200px;
  background: white;
  border-radius: var(--radius);
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--gray-200);
  transition: all 0.2s ease;
}

.stat-card:hover {
  box-shadow: var(--shadow);
  transform: translateY(-2px);
}

.stat-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-bg);
  border-radius: var(--radius);
  font-size: 24px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--gray-800);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--gray-500);
  margin-top: 4px;
}

.content-section {
  background: white;
  border-radius: var(--radius);
  border: 1px solid var(--gray-200);
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--gray-200);
  background: var(--gray-50);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.date-badge {
  font-size: 12px;
  font-weight: 500;
  color: var(--primary);
  background: var(--primary-bg);
  padding: 2px 10px;
  border-radius: 9999px;
}

.article-count {
  font-size: 13px;
  color: var(--gray-500);
}

.loading-container {
  padding: 60px 20px;
  text-align: center;
}

.loading-text {
  margin-top: 16px;
  color: var(--gray-500);
  font-size: 14px;
}

.empty-state-container {
  padding: 20px;
}

.empty-state {
  background: var(--gray-50);
  border-radius: var(--radius);
  border: 2px dashed var(--gray-200);
}

.mt-4 {
  margin-top: 16px;
}

@media (max-width: 768px) {
  .stats-cards {
    flex-direction: column;
  }
  
  .stat-card {
    min-width: auto;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
