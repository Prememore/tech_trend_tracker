<template>
  <div class="article-list">
    <div v-if="articles.length === 0" class="empty-state">
      <div class="empty-icon">📄</div>
      <div class="empty-title">暂无论文数据</div>
      <div class="empty-desc">当前列表为空，请稍后再试</div>
    </div>
    
    <div v-else class="table-container">
      <table class="table">
        <thead>
          <tr>
            <th style="width: 60px">序号</th>
            <th style="width: 100px; cursor: pointer" @click="toggleSort">
              相关度
              <span class="sort-icon">{{ sortDesc ? '▼' : '▲' }}</span>
            </th>
            <th>标题</th>
            <th style="width: 150px">来源</th>
            <th style="width: 160px">发布时间</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(article, index) in sortedArticles"
            :key="article.id"
            class="article-row"
            @click="openDetail(article)"
          >
            <td>{{ index + 1 }}</td>
            <td>
              <span
                class="relevance-score"
                :class="getRelevanceClass(article.relevance_score)"
              >
                {{ formatRelevance(article.relevance_score) }}
              </span>
            </td>
            <td>
              <div class="article-title">{{ article.title }}</div>
            </td>
            <td>
              <span class="source-tag">{{ article.source }}</span>
            </td>
            <td>{{ formatDate(article.published_at) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <ArticleDetail
      v-if="selectedArticle"
      :article="selectedArticle"
      @close="selectedArticle = null"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ArticleDetail from './ArticleDetail.vue'

const props = defineProps({
  articles: {
    type: Array,
    required: true,
    default: () => []
  }
})

const sortDesc = ref(true)
const selectedArticle = ref(null)

const sortedArticles = computed(() => {
  return [...props.articles].sort((a, b) => {
    const scoreA = a.relevance_score || 0
    const scoreB = b.relevance_score || 0
    return sortDesc.value ? scoreB - scoreA : scoreA - scoreB
  })
})

const toggleSort = () => {
  sortDesc.value = !sortDesc.value
}

const getRelevanceClass = (score) => {
  if (score >= 0.6) return 'high'
  if (score >= 0.4) return 'medium'
  return 'low'
}

const formatRelevance = (score) => {
  if (score === undefined || score === null) return '-'
  return `${(score * 100).toFixed(0)}%`
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const openDetail = (article) => {
  selectedArticle.value = article
}
</script>

<style scoped>
.article-list {
  width: 100%;
}

.article-row {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.article-row:hover {
  background-color: var(--gray-100);
}

.article-title {
  font-weight: 500;
  color: var(--gray-800);
  max-width: 500px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.relevance-score {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 9999px;
  min-width: 50px;
}

.relevance-score.high {
  background: rgba(16, 185, 129, 0.15);
  color: var(--success);
}

.relevance-score.medium {
  background: rgba(245, 158, 11, 0.15);
  color: var(--warning);
}

.relevance-score.low {
  background: rgba(148, 163, 184, 0.2);
  color: var(--gray-500);
}

.source-tag {
  display: inline-block;
  padding: 2px 8px;
  font-size: 12px;
  color: var(--gray-600);
  background: var(--gray-100);
  border-radius: 4px;
}

.sort-icon {
  font-size: 10px;
  margin-left: 4px;
  color: var(--gray-400);
}

.empty-state {
  background: white;
  border-radius: var(--radius);
  border: 1px solid var(--gray-200);
}
</style>
