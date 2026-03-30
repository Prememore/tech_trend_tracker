<template>
  <div class="page-container">
    <!-- 配置区：时间范围选择 -->
    <div class="card mb-6">
      <div class="card-header">
        <h3 class="card-title">更新配置</h3>
      </div>
      <div class="card-body">
        <div class="section">
          <label class="section-label">时间范围</label>
          <div class="preset-buttons">
            <button
              v-for="preset in presets"
              :key="preset.value"
              class="btn btn-secondary btn-sm"
              :class="{ active: selectedDays === preset.value && !isCustom }"
              @click="selectPreset(preset.value)"
            >
              {{ preset.label }}
            </button>
          </div>
        </div>
        
        <div class="section custom-input-section">
          <label class="section-label">自定义天数</label>
          <div class="custom-input-wrapper">
            <input
              v-model.number="customDays"
              type="number"
              min="1"
              max="365"
              class="input custom-input"
              placeholder="输入 1-365"
              @focus="isCustom = true"
              @input="validateCustomInput"
            />
            <span class="input-suffix">天</span>
          </div>
          <span v-if="inputError" class="error-text">{{ inputError }}</span>
        </div>

        <div class="section">
          <button
            class="btn btn-primary btn-lg"
            :disabled="isUpdating || !canStartUpdate"
            @click="startUpdate"
          >
            <span v-if="isUpdating" class="spinner-sm"></span>
            <span>{{ isUpdating ? '更新中...' : '开始更新' }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 状态区：进度显示 -->
    <div class="card mb-6" v-if="showStatus">
      <div class="card-header">
        <h3 class="card-title">更新状态</h3>
        <span class="tag" :class="statusTagClass">{{ statusText }}</span>
      </div>
      <div class="card-body">
        <div class="status-content">
          <div v-if="status === 'running'" class="running-status">
            <div class="spinner"></div>
            <p class="status-message">正在从 arXiv 获取文献数据...</p>
          </div>
          <div v-else-if="status === 'completed'" class="success-status">
            <div class="status-icon success">✓</div>
            <p class="status-message">更新完成</p>
          </div>
          <div v-else-if="status === 'failed'" class="error-status">
            <div class="status-icon error">✗</div>
            <p class="status-message">更新失败</p>
            <p v-if="errorMessage" class="error-detail">{{ errorMessage }}</p>
          </div>
          <div v-else-if="status === 'idle'" class="idle-status">
            <p class="status-message">系统空闲，等待更新任务</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 结果区：统计卡片 -->
    <div class="card" v-if="showResult && result">
      <div class="card-header">
        <h3 class="card-title">更新结果</h3>
      </div>
      <div class="card-body">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ result.fetched }}</div>
            <div class="stat-label">原始抓取</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ result.filtered }}</div>
            <div class="stat-label">过滤后</div>
          </div>
          <div class="stat-card highlight">
            <div class="stat-value">{{ result.saved }}</div>
            <div class="stat-label">新增入库</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ result.total }}</div>
            <div class="stat-label">数据库总量</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="showError" class="error-toast">
      <div class="error-toast-content">
        <span class="error-icon">⚠</span>
        <span>{{ errorMessage }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { triggerUpdate, fetchUpdateStatus } from '../api/index.js'

// 预设按钮配置
const presets = [
  { label: '今天', value: 1 },
  { label: '3天', value: 3 },
  { label: '7天', value: 7 },
  { label: '30天', value: 30 },
  { label: '90天', value: 90 }
]

// 状态
const selectedDays = ref(1)
const customDays = ref('')
const isCustom = ref(false)
const inputError = ref('')
const isUpdating = ref(false)
const status = ref('idle')
const result = ref(null)
const errorMessage = ref('')
const showError = ref(false)
const showStatus = ref(false)
const showResult = ref(false)

// 轮询定时器
let pollTimer = null

// 计算属性
const canStartUpdate = computed(() => {
  if (isCustom.value) {
    return customDays.value >= 1 && customDays.value <= 365 && !inputError.value
  }
  return true
})

const statusText = computed(() => {
  const statusMap = {
    idle: '空闲',
    running: '更新中',
    completed: '已完成',
    failed: '失败'
  }
  return statusMap[status.value] || status.value
})

const statusTagClass = computed(() => {
  const classMap = {
    idle: '',
    running: 'tag-primary',
    completed: 'tag-success',
    failed: 'tag-danger'
  }
  return classMap[status.value] || ''
})

// 方法
const selectPreset = (days) => {
  selectedDays.value = days
  isCustom.value = false
  customDays.value = ''
  inputError.value = ''
}

const validateCustomInput = () => {
  const value = customDays.value
  if (value === '' || value === null || value === undefined) {
    inputError.value = ''
    return
  }
  if (value < 1) {
    inputError.value = '天数不能小于 1'
  } else if (value > 365) {
    inputError.value = '天数不能大于 365'
  } else {
    inputError.value = ''
  }
}

const getDays = () => {
  if (isCustom.value && customDays.value) {
    return customDays.value
  }
  return selectedDays.value
}

const showErrorMessage = (message) => {
  errorMessage.value = message
  showError.value = true
  setTimeout(() => {
    showError.value = false
  }, 3000)
}

const pollStatus = async () => {
  try {
    const data = await fetchUpdateStatus()
    status.value = data.status
    
    if (data.status === 'completed') {
      result.value = data.result
      showResult.value = true
      isUpdating.value = false
      stopPolling()
    } else if (data.status === 'failed') {
      errorMessage.value = data.error || '更新过程中发生错误'
      isUpdating.value = false
      stopPolling()
    } else if (data.status === 'idle') {
      // 如果状态变为空闲但之前正在更新，说明更新完成
      if (isUpdating.value) {
        isUpdating.value = false
        stopPolling()
      }
    }
  } catch (error) {
    console.error('轮询状态失败:', error)
  }
}

const startPolling = () => {
  stopPolling()
  pollTimer = setInterval(pollStatus, 2000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const startUpdate = async () => {
  if (isUpdating.value) return
  
  const days = getDays()
  if (!days || days < 1 || days > 365) {
    showErrorMessage('请输入有效的天数 (1-365)')
    return
  }

  try {
    isUpdating.value = true
    showStatus.value = true
    showResult.value = false
    result.value = null
    status.value = 'running'
    
    const response = await triggerUpdate(days)
    
    if (response.status === 'running' || response.message?.includes('已启动')) {
      // 更新任务已启动，开始轮询
      startPolling()
    } else {
      isUpdating.value = false
      showErrorMessage('启动更新任务失败')
    }
  } catch (error) {
    isUpdating.value = false
    status.value = 'failed'
    
    if (error.response?.status === 409) {
      showErrorMessage('已有更新任务在执行')
    } else if (error.message?.includes('Network Error')) {
      showErrorMessage('网络错误，请检查后端服务是否启动')
    } else {
      showErrorMessage(error.message || '启动更新失败')
    }
  }
}

// 生命周期
onMounted(() => {
  // 页面加载时检查一次状态
  pollStatus()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.page-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

.section {
  margin-bottom: 24px;
}

.section:last-child {
  margin-bottom: 0;
}

.section-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-700);
  margin-bottom: 12px;
}

.preset-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.preset-buttons .btn.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

.custom-input-section {
  max-width: 200px;
}

.custom-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.custom-input {
  padding-right: 40px;
}

.input-suffix {
  position: absolute;
  right: 14px;
  font-size: 14px;
  color: var(--gray-500);
  pointer-events: none;
}

.error-text {
  display: block;
  font-size: 12px;
  color: var(--danger);
  margin-top: 6px;
}

/* 状态显示 */
.status-content {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 120px;
}

.running-status,
.success-status,
.error-status,
.idle-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.status-message {
  font-size: 14px;
  color: var(--gray-600);
}

.status-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
}

.status-icon.success {
  background: rgba(16, 185, 129, 0.1);
  color: var(--success);
}

.status-icon.error {
  background: rgba(239, 68, 68, 0.1);
  color: var(--danger);
}

.error-detail {
  font-size: 13px;
  color: var(--danger);
  max-width: 400px;
  text-align: center;
}

/* 统计卡片 */
.stats-grid {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.stat-card {
  flex: 1;
  min-width: 120px;
  padding: 20px;
  background: var(--gray-50);
  border-radius: var(--radius);
  text-align: center;
  border: 1px solid var(--gray-200);
}

.stat-card.highlight {
  background: var(--primary-bg);
  border-color: var(--primary-light);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--gray-800);
  margin-bottom: 4px;
}

.stat-card.highlight .stat-value {
  color: var(--primary);
}

.stat-label {
  font-size: 13px;
  color: var(--gray-500);
}

/* 小 spinner */
.spinner-sm {
  width: 16px;
  height: 16px;
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

/* 错误提示 */
.error-toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 1000;
  animation: slideUp 0.3s ease;
}

.error-toast-content {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: var(--danger);
  color: white;
  border-radius: var(--radius);
  font-size: 14px;
  box-shadow: var(--shadow-lg);
}

.error-icon {
  font-size: 16px;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

/* 响应式 */
@media (max-width: 600px) {
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
  }
  
  .preset-buttons {
    gap: 8px;
  }
  
  .preset-buttons .btn {
    padding: 8px 12px;
    font-size: 13px;
  }
}
</style>
