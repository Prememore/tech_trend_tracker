<template>
  <div class="page-container">
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">🧹 数据清理</h3>
      </div>
      <div class="card-body">
        <!-- 清理策略选择 -->
        <div class="cleanup-section">
          <label class="section-label">选择清理策略</label>
          <div class="strategy-options">
            <label
              v-for="option in strategyOptions"
              :key="option.value"
              class="strategy-option"
              :class="{ active: selectedMode === option.value }"
            >
              <input
                v-model="selectedMode"
                type="radio"
                :value="option.value"
                name="cleanup-mode"
              />
              <span class="option-icon">{{ option.icon }}</span>
              <div class="option-content">
                <span class="option-title">{{ option.label }}</span>
                <span class="option-desc">{{ option.desc }}</span>
              </div>
            </label>
          </div>
        </div>

        <!-- 策略参数输入 -->
        <div class="cleanup-section">
          <label class="section-label">参数设置</label>
          <div class="param-input-area">
            <!-- 按天数保留 -->
            <div v-if="selectedMode === 'days'" class="param-row">
              <span class="param-label">保留最近</span>
              <input
                v-model.number="daysValue"
                type="number"
                class="input param-input"
                min="1"
                placeholder="30"
              />
              <span class="param-unit">天的数据</span>
            </div>

            <!-- 按指定日期删除 -->
            <div v-else-if="selectedMode === 'date'" class="param-row">
              <span class="param-label">删除日期</span>
              <input
                v-model="dateValue"
                type="date"
                class="input param-input date-input"
              />
              <span class="param-hint">的单日数据</span>
            </div>

            <!-- 按日期之前删除 -->
            <div v-else-if="selectedMode === 'before'" class="param-row">
              <span class="param-label">删除</span>
              <input
                v-model="beforeDateValue"
                type="date"
                class="input param-input date-input"
              />
              <span class="param-hint">之前的所有数据</span>
            </div>

            <!-- 清空全部 -->
            <div v-else-if="selectedMode === 'all'" class="param-row danger-row">
              <span class="danger-icon">⚠️</span>
              <span class="danger-text">此操作将清空所有数据，请谨慎操作！</span>
            </div>
          </div>
        </div>

        <!-- 预览区 -->
        <div v-if="previewData" class="cleanup-section preview-section">
          <label class="section-label">清理预览</label>
          <div class="preview-card">
            <div class="preview-count">
              <span class="count-number">{{ previewData.total_count }}</span>
              <span class="count-label">条数据将被删除</span>
            </div>
            <div v-if="previewData.affected_dates && previewData.affected_dates.length > 0" class="preview-samples">
              <p class="samples-title">受影响日期：</p>
              <ul class="samples-list">
                <li v-for="(item, index) in previewData.affected_dates.slice(0, 5)" :key="index">
                  {{ item.date }} ({{ item.count }} 条)
                </li>
                <li v-if="previewData.affected_dates.length > 5" class="more-items">
                  ... 还有 {{ previewData.affected_dates.length - 5 }} 个日期
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- 操作按钮区 -->
        <div class="actions-row">
          <button
            class="btn btn-secondary"
            :disabled="isPreviewing || !canPreview"
            @click="previewCleanupData"
          >
            <span v-if="isPreviewing" class="btn-spinner"></span>
            <span v-else>👁️</span>
            预览
          </button>
          <button
            class="btn"
            :class="selectedMode === 'all' ? 'btn-danger' : 'btn-primary'"
            :disabled="isExecuting || !canExecute"
            @click="confirmExecute"
          >
            <span v-if="isExecuting" class="btn-spinner"></span>
            <span v-else>🗑️</span>
            执行清理
          </button>
        </div>
      </div>
    </div>

    <!-- 成功提示 -->
    <div v-if="showSuccess" class="toast" :class="toastType">
      {{ successMessage }}
    </div>

    <!-- 确认对话框 -->
    <div v-if="showConfirmModal" class="modal-overlay" @click.self="closeConfirmModal">
      <div class="modal">
        <div class="modal-header">
          <h4>确认执行清理</h4>
        </div>
        <div class="modal-body">
          <p v-if="selectedMode !== 'all'">
            确定要执行此清理操作吗？
            <span v-if="previewData" class="highlight">
              将删除 {{ previewData.total_count }} 条数据
            </span>
          </p>
          <div v-else class="danger-confirm">
            <p class="danger-text">⚠️ 您即将清空所有数据！</p>
            <p class="confirm-instruction">请输入 "CONFIRM" 以确认此操作：</p>
            <input
              v-model="confirmInput"
              type="text"
              class="input confirm-input"
              placeholder="输入 CONFIRM"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeConfirmModal">取消</button>
          <button
            class="btn"
            :class="selectedMode === 'all' ? 'btn-danger' : 'btn-primary'"
            :disabled="selectedMode === 'all' && confirmInput !== 'CONFIRM'"
            @click="executeCleanupData"
          >
            确认执行
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { previewCleanup, executeCleanup } from '../api/index.js'

// 策略选项
const strategyOptions = [
  {
    value: 'days',
    label: '按天数保留',
    desc: '保留最近N天的数据',
    icon: '📅'
  },
  {
    value: 'date',
    label: '按指定日期删除',
    desc: '删除指定单日的数据',
    icon: '📆'
  },
  {
    value: 'before',
    label: '按日期之前删除',
    desc: '删除指定日期之前的所有数据',
    icon: '🗓️'
  },
  {
    value: 'all',
    label: '清空全部',
    desc: '删除所有数据（危险操作）',
    icon: '⚠️'
  }
]

// 响应式数据
const selectedMode = ref('days')
const daysValue = ref(30)
const dateValue = ref('')
const beforeDateValue = ref('')
const previewData = ref(null)
const isPreviewing = ref(false)
const isExecuting = ref(false)
const showSuccess = ref(false)
const successMessage = ref('')
const toastType = ref('toast-success')
const showConfirmModal = ref(false)
const confirmInput = ref('')

// 计算属性
const canPreview = computed(() => {
  switch (selectedMode.value) {
    case 'days':
      return daysValue.value > 0
    case 'date':
      return dateValue.value !== ''
    case 'before':
      return beforeDateValue.value !== ''
    case 'all':
      return true
    default:
      return false
  }
})

const canExecute = computed(() => {
  if (selectedMode.value === 'all') {
    return true
  }
  return previewData.value !== null
})

// 获取清理参数
const getCleanupParams = () => {
  switch (selectedMode.value) {
    case 'days':
      return { mode: 'days', value: String(daysValue.value) }
    case 'date':
      return { mode: 'date', value: dateValue.value }
    case 'before':
      return { mode: 'before', value: beforeDateValue.value }
    case 'all':
      return { mode: 'all' }
    default:
      return {}
  }
}

// 预览清理
const previewCleanupData = async () => {
  isPreviewing.value = true
  try {
    const params = getCleanupParams()
    const data = await previewCleanup(params)
    previewData.value = data
    showToast('预览数据已更新', 'success')
  } catch (error) {
    console.error('预览清理失败:', error)
    showToast('预览失败，请重试', 'error')
  } finally {
    isPreviewing.value = false
  }
}

// 确认执行
const confirmExecute = () => {
  confirmInput.value = ''
  showConfirmModal.value = true
}

// 关闭确认对话框
const closeConfirmModal = () => {
  showConfirmModal.value = false
  confirmInput.value = ''
}

// 执行清理
const executeCleanupData = async () => {
  isExecuting.value = true
  showConfirmModal.value = false
  try {
    const params = getCleanupParams()
    const result = await executeCleanup(params)
    showToast(`清理完成！共删除 ${result.deleted_count || previewData.value?.total_count || 0} 条数据`, 'success')
    previewData.value = null
  } catch (error) {
    console.error('执行清理失败:', error)
    showToast('清理失败，请重试', 'error')
  } finally {
    isExecuting.value = false
  }
}

// 显示提示
const showToast = (message, type = 'success') => {
  successMessage.value = message
  toastType.value = type === 'error' ? 'toast-error' : 'toast-success'
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

.cleanup-section {
  margin-bottom: 28px;
}

.cleanup-section:last-of-type {
  margin-bottom: 20px;
}

.section-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-800);
  margin-bottom: 12px;
}

/* 策略选项 */
.strategy-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.strategy-option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border: 2px solid var(--gray-200);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s ease;
  background: white;
}

.strategy-option:hover {
  border-color: var(--gray-300);
}

.strategy-option.active {
  border-color: var(--primary);
  background: var(--primary-bg);
}

.strategy-option input[type="radio"] {
  display: none;
}

.option-icon {
  font-size: 24px;
  line-height: 1;
}

.option-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.option-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--gray-800);
}

.option-desc {
  font-size: 12px;
  color: var(--gray-500);
}

/* 参数输入 */
.param-input-area {
  background: var(--gray-50);
  border-radius: var(--radius);
  padding: 20px;
}

.param-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.param-label {
  font-size: 14px;
  color: var(--gray-700);
}

.param-input {
  width: 100px;
  text-align: center;
}

.param-input.date-input {
  width: 160px;
}

.param-unit,
.param-hint {
  font-size: 14px;
  color: var(--gray-600);
}

.danger-row {
  color: var(--danger);
  font-weight: 500;
}

.danger-icon {
  font-size: 20px;
}

.danger-text {
  color: var(--danger);
}

/* 预览区 */
.preview-section {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.preview-card {
  background: var(--gray-50);
  border: 1px solid var(--gray-200);
  border-radius: var(--radius);
  padding: 20px;
}

.preview-count {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 16px;
}

.count-number {
  font-size: 32px;
  font-weight: 700;
  color: var(--danger);
}

.count-label {
  font-size: 14px;
  color: var(--gray-600);
}

.samples-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--gray-700);
  margin-bottom: 8px;
}

.samples-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.samples-list li {
  font-size: 13px;
  color: var(--gray-600);
  padding: 4px 0;
  padding-left: 16px;
  position: relative;
}

.samples-list li::before {
  content: '•';
  position: absolute;
  left: 4px;
  color: var(--gray-400);
}

.samples-list .more-items {
  color: var(--gray-500);
  font-style: italic;
}

.samples-list .more-items::before {
  content: none;
}

/* 操作按钮 */
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
  max-width: 420px;
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
  margin: 0;
  font-size: 14px;
  color: var(--gray-700);
  line-height: 1.6;
}

.modal-body .highlight {
  color: var(--danger);
  font-weight: 600;
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid var(--gray-200);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 危险确认 */
.danger-confirm {
  text-align: center;
}

.danger-confirm .danger-text {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.confirm-instruction {
  font-size: 13px;
  color: var(--gray-500);
  margin-bottom: 12px;
}

.confirm-input {
  width: 100%;
  text-align: center;
  font-weight: 600;
  letter-spacing: 1px;
}

@media (max-width: 640px) {
  .strategy-options {
    grid-template-columns: 1fr;
  }
}
</style>
