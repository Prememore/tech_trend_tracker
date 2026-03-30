<template>
  <div class="page-container">
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">🏷️ 关键词管理</h3>
      </div>
      <div class="card-body">
        <!-- 主关键词区 -->
        <div class="keyword-section">
          <label class="section-label">主关键词</label>
          <p class="section-desc">用于精确匹配文献的核心关键词</p>
          <div class="tags-container">
            <span
              v-for="(keyword, index) in primaryKeywords"
              :key="index"
              class="tag tag-primary keyword-tag"
            >
              {{ keyword }}
              <button class="tag-remove" @click="removePrimaryKeyword(index)">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M8.5 3.5L3.5 8.5M3.5 3.5L8.5 8.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
              </button>
            </span>
          </div>
          <div class="add-keyword-row">
            <input
              v-model="newPrimaryKeyword"
              type="text"
              class="input keyword-input"
              placeholder="输入新主关键词..."
              @keyup.enter="addPrimaryKeyword"
            />
            <button class="btn btn-primary btn-sm" @click="addPrimaryKeyword">
              添加
            </button>
          </div>
        </div>

        <!-- 次要关键词区 -->
        <div class="keyword-section">
          <label class="section-label">次要关键词</label>
          <p class="section-desc">用于辅助匹配的扩展关键词</p>
          <div class="tags-container">
            <span
              v-for="(keyword, index) in secondaryKeywords"
              :key="index"
              class="tag tag-success keyword-tag"
            >
              {{ keyword }}
              <button class="tag-remove" @click="removeSecondaryKeyword(index)">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M8.5 3.5L3.5 8.5M3.5 3.5L8.5 8.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
              </button>
            </span>
          </div>
          <div class="add-keyword-row">
            <input
              v-model="newSecondaryKeyword"
              type="text"
              class="input keyword-input"
              placeholder="输入新次要关键词..."
              @keyup.enter="addSecondaryKeyword"
            />
            <button class="btn btn-primary btn-sm" @click="addSecondaryKeyword">
              添加
            </button>
          </div>
        </div>

        <!-- 操作按钮区 -->
        <div class="actions-row">
          <button class="btn btn-primary" :disabled="isSaving" @click="saveKeywords">
            <span v-if="isSaving" class="btn-spinner"></span>
            <span v-else>💾</span>
            保存配置
          </button>
          <button class="btn btn-secondary" :disabled="isResetting" @click="confirmReset">
            <span v-if="isResetting" class="btn-spinner"></span>
            <span v-else>🔄</span>
            重置为默认
          </button>
        </div>
      </div>
    </div>

    <!-- 成功提示 -->
    <div v-if="showSuccess" class="toast toast-success">
      {{ successMessage }}
    </div>

    <!-- 确认对话框 -->
    <div v-if="showConfirmModal" class="modal-overlay" @click.self="closeConfirmModal">
      <div class="modal">
        <div class="modal-header">
          <h4>确认重置</h4>
        </div>
        <div class="modal-body">
          <p>确定要将关键词重置为默认配置吗？</p>
          <p class="text-muted">此操作将覆盖当前所有关键词设置。</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeConfirmModal">取消</button>
          <button class="btn btn-danger" @click="resetToDefault">确定重置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchKeywords, updateKeywords, resetKeywords } from '../api/index.js'

// 响应式数据
const primaryKeywords = ref([])
const secondaryKeywords = ref([])
const newPrimaryKeyword = ref('')
const newSecondaryKeyword = ref('')
const isSaving = ref(false)
const isResetting = ref(false)
const showSuccess = ref(false)
const successMessage = ref('')
const showConfirmModal = ref(false)

// 页面加载时获取关键词配置
onMounted(async () => {
  try {
    const data = await fetchKeywords()
    if (data) {
      // 后端直接返回关键词配置对象
      primaryKeywords.value = data.primary || []
      secondaryKeywords.value = data.secondary || []
    }
  } catch (error) {
    console.error('获取关键词配置失败:', error)
    showSuccessMessage('获取配置失败，请检查网络连接', 'error')
  }
})

// 添加主关键词
const addPrimaryKeyword = () => {
  const keyword = newPrimaryKeyword.value.trim()
  if (keyword && !primaryKeywords.value.includes(keyword)) {
    primaryKeywords.value.push(keyword)
    newPrimaryKeyword.value = ''
  }
}

// 删除主关键词
const removePrimaryKeyword = (index) => {
  primaryKeywords.value.splice(index, 1)
}

// 添加次要关键词
const addSecondaryKeyword = () => {
  const keyword = newSecondaryKeyword.value.trim()
  if (keyword && !secondaryKeywords.value.includes(keyword)) {
    secondaryKeywords.value.push(keyword)
    newSecondaryKeyword.value = ''
  }
}

// 删除次要关键词
const removeSecondaryKeyword = (index) => {
  secondaryKeywords.value.splice(index, 1)
}

// 保存关键词配置
const saveKeywords = async () => {
  isSaving.value = true
  try {
    await updateKeywords({
      primary: primaryKeywords.value,
      secondary: secondaryKeywords.value
    })
    showSuccessMessage('配置保存成功！')
  } catch (error) {
    console.error('保存关键词配置失败:', error)
    showSuccessMessage('保存失败，请重试', 'error')
  } finally {
    isSaving.value = false
  }
}

// 确认重置对话框
const confirmReset = () => {
  showConfirmModal.value = true
}

// 关闭确认对话框
const closeConfirmModal = () => {
  showConfirmModal.value = false
}

// 重置为默认
const resetToDefault = async () => {
  isResetting.value = true
  showConfirmModal.value = false
  try {
    const data = await resetKeywords()
    if (data && data.keywords) {
      primaryKeywords.value = data.keywords.primary || []
      secondaryKeywords.value = data.keywords.secondary || []
    }
    showSuccessMessage('已重置为默认配置！')
  } catch (error) {
    console.error('重置关键词配置失败:', error)
    showSuccessMessage('重置失败，请重试', 'error')
  } finally {
    isResetting.value = false
  }
}

// 显示成功提示
const showSuccessMessage = (message, type = 'success') => {
  successMessage.value = message
  showSuccess.value = true
  setTimeout(() => {
    showSuccess.value = false
  }, 3000)
}
</script>

<style scoped>
.page-container {
  min-height: 400px;
}

.keyword-section {
  margin-bottom: 32px;
}

.keyword-section:last-of-type {
  margin-bottom: 24px;
}

.section-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: 4px;
}

.section-desc {
  font-size: 13px;
  color: var(--gray-500);
  margin-bottom: 12px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
  min-height: 32px;
}

.keyword-tag {
  padding: 6px 12px;
  font-size: 13px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.tag-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  border-radius: 50%;
  opacity: 0.6;
  transition: all 0.2s ease;
}

.tag-remove:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.1);
}

.add-keyword-row {
  display: flex;
  gap: 8px;
}

.keyword-input {
  flex: 1;
  max-width: 300px;
}

.actions-row {
  display: flex;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--gray-200);
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Toast 提示 */
.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 12px 20px;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 500;
  animation: slideIn 0.3s ease;
  z-index: 1000;
}

.toast-success {
  background: var(--success);
  color: white;
}

.toast-error {
  background: var(--danger);
  color: white;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 模态框 */
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
}

.modal {
  background: white;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  width: 90%;
  max-width: 400px;
  animation: modalSlideIn 0.2s ease;
}

@keyframes modalSlideIn {
  from {
    transform: scale(0.95);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--gray-200);
}

.modal-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0;
}

.modal-body {
  padding: 20px 24px;
}

.modal-body p {
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--gray-700);
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--gray-200);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.text-muted {
  color: var(--gray-500);
}
</style>
