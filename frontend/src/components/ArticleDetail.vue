<template>
  <Teleport to="body">
    <div class="modal-overlay" @click="handleClose">
      <div class="modal-container" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">论文详情</h3>
          <button class="close-btn" @click="handleClose">×</button>
        </div>
        
        <div class="modal-body">
          <div class="detail-section">
            <h2 class="article-title">{{ article.title }}</h2>
            
            <div class="meta-info">
              <div class="meta-item">
                <span class="meta-label">来源：</span>
                <span class="meta-value">{{ article.source || '-' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">发布时间：</span>
                <span class="meta-value">{{ formatDate(article.published_at) }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">相关度：</span>
                <span
                  class="relevance-badge"
                  :class="getRelevanceClass(article.relevance_score)"
                >
                  {{ formatRelevance(article.relevance_score) }}
                </span>
              </div>
            </div>
            
            <div v-if="article.tags" class="tags-section">
              <span class="meta-label">标签：</span>
              <span class="tag tag-primary">{{ article.tags }}</span>
            </div>
          </div>
          
          <div class="detail-section">
            <h4 class="section-title">摘要</h4>
            <p class="article-summary">{{ article.summary || '暂无摘要' }}</p>
          </div>
        </div>
        
        <div class="modal-footer">
          <a
            :href="article.link"
            target="_blank"
            rel="noopener noreferrer"
            class="btn btn-primary"
          >
            打开原文
            <svg class="external-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
              <polyline points="15 3 21 3 21 9"></polyline>
              <line x1="10" y1="14" x2="21" y2="3"></line>
            </svg>
          </a>
          <button class="btn btn-secondary" @click="handleClose">关闭</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
const props = defineProps({
  article: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close'])

const handleClose = () => {
  emit('close')
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
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  backdrop-filter: blur(4px);
}

.modal-container {
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  width: 100%;
  max-width: 700px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: modal-in 0.2s ease;
}

@keyframes modal-in {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--gray-200);
}

.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--gray-400);
  font-size: 24px;
  cursor: pointer;
  border-radius: var(--radius);
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: var(--gray-100);
  color: var(--gray-600);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.article-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--gray-800);
  line-height: 1.4;
  margin: 0 0 16px 0;
}

.meta-info {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.meta-label {
  font-size: 13px;
  color: var(--gray-500);
}

.meta-value {
  font-size: 13px;
  color: var(--gray-700);
  font-weight: 500;
}

.relevance-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 9999px;
}

.relevance-badge.high {
  background: rgba(16, 185, 129, 0.15);
  color: var(--success);
}

.relevance-badge.medium {
  background: rgba(245, 158, 11, 0.15);
  color: var(--warning);
}

.relevance-badge.low {
  background: rgba(148, 163, 184, 0.2);
  color: var(--gray-500);
}

.tags-section {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-700);
  margin: 0 0 12px 0;
}

.article-summary {
  font-size: 14px;
  line-height: 1.8;
  color: var(--gray-600);
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
}

.modal-footer {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--gray-200);
  justify-content: flex-end;
}

.external-icon {
  width: 14px;
  height: 14px;
  margin-left: 4px;
}

@media (max-width: 768px) {
  .modal-container {
    max-height: 95vh;
    margin: 10px;
  }
  
  .modal-header,
  .modal-body,
  .modal-footer {
    padding-left: 16px;
    padding-right: 16px;
  }
  
  .meta-info {
    flex-direction: column;
    gap: 8px;
  }
  
  .article-title {
    font-size: 18px;
  }
}
</style>
