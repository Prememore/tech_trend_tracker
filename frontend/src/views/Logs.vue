<template>
  <div class="page-container">
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">📝 操作日志</h3>
        <div class="header-actions">
          <button 
            class="btn btn-danger btn-sm" 
            :disabled="isLoading || selectedIds.length === 0" 
            @click="confirmBatchDelete"
          >
            批量删除 ({{ selectedIds.length }})
          </button>
          <button 
            class="btn btn-danger-outline btn-sm" 
            :disabled="isLoading || logs.length === 0" 
            @click="confirmClearAll"
          >
            清空全部
          </button>
          <button class="btn btn-secondary btn-sm" :disabled="isLoading" @click="refreshLogs">
            <span v-if="isLoading" class="btn-spinner"></span>
            <span v-else>🔄</span>
            刷新
          </button>
        </div>
      </div>
      <div class="card-body">
        <!-- 加载状态 -->
        <div v-if="isLoading && logs.length === 0" class="loading">
          <div class="spinner"></div>
        </div>

        <!-- 空状态 -->
        <div v-else-if="logs.length === 0" class="empty-state">
          <div class="empty-icon">📋</div>
          <h3 class="empty-title">暂无操作记录</h3>
          <p class="empty-desc">系统操作日志将显示在这里</p>
        </div>

        <!-- 日志表格 -->
        <div v-else class="table-container">
          <table class="table">
            <thead>
              <tr>
                <th style="width: 40px">
                  <input 
                    type="checkbox" 
                    :checked="isAllSelected" 
                    @change="toggleSelectAll"
                  />
                </th>
                <th style="width: 60px">序号</th>
                <th style="width: 140px">操作类型</th>
                <th>操作目标</th>
                <th style="width: 100px">删除数量</th>
                <th style="width: 160px">操作时间</th>
                <th style="width: 80px">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(log, index) in logs" :key="log.id || log.timestamp + index">
                <td>
                  <input 
                    type="checkbox" 
                    :value="log.id" 
                    v-model="selectedIds"
                    :disabled="!log.id"
                  />
                </td>
                <td>{{ logs.length - index }}</td>
                <td>
                  <span class="tag" :class="getOperationTagClass(log)">
                    {{ getOperationLabel(log) }}
                  </span>
                </td>
                <td>{{ getTargetText(log) }}</td>
                <td class="count-cell">{{ log.count !== undefined ? log.count : '-' }}</td>
                <td class="time-cell">{{ formatTime(log.timestamp) }}</td>
                <td>
                  <button 
                    class="btn-delete" 
                    @click="confirmDelete(log)"
                    :disabled="!log.id"
                    title="删除"
                  >
                    🗑️
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 删除确认弹窗 -->
    <div v-if="showConfirmDialog" class="modal-overlay" @click.self="closeConfirmDialog">
      <div class="modal">
        <div class="modal-header">
          <h3 class="modal-title">⚠️ 确认删除</h3>
        </div>
        <div class="modal-body">
          <p>{{ confirmMessage }}</p>
          <div v-if="confirmType === 'clear'" class="confirm-input">
            <p class="input-hint">请输入 <strong>CONFIRM</strong> 以确认清空全部日志</p>
            <input 
              v-model="confirmInput" 
              type="text" 
              placeholder="输入 CONFIRM"
              @keyup.enter="executeDelete"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary btn-sm" @click="closeConfirmDialog">取消</button>
          <button 
            class="btn btn-danger btn-sm" 
            @click="executeDelete"
            :disabled="confirmType === 'clear' && confirmInput !== 'CONFIRM'"
          >
            确认删除
          </button>
        </div>
      </div>
    </div>

    <!-- 提示信息 -->
    <div v-if="showToast" class="toast" :class="toastClass">
      {{ toastMessage }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { fetchLogs, deleteLog, deleteLogs, clearLogs } from '../api/index.js'

// 响应式数据
const logs = ref([])
const isLoading = ref(false)
const showToast = ref(false)
const toastMessage = ref('')
const toastClass = ref('toast-success')
const selectedIds = ref([])

// 确认弹窗相关
const showConfirmDialog = ref(false)
const confirmMessage = ref('')
const confirmType = ref('') // 'single', 'batch', 'clear'
const confirmInput = ref('')
const pendingDeleteLog = ref(null)

// 操作类型映射
const operationMap = {
  delete_by_days: { label: '按天数删除', class: 'tag-warning' },
  delete_by_date: { label: '按日期删除', class: 'tag-warning' },
  delete_before: { label: '删除之前', class: 'tag-warning' },
  delete_all: { label: '清空全部', class: 'tag-danger' },
  update: { label: '数据更新', class: 'tag-primary' },
  reset_keywords: { label: '重置关键词', class: 'tag-primary' },
  update_keywords: { label: '更新关键词', class: 'tag-success' },
  cleanup: { label: '数据清理', class: 'tag-warning' }
}

// 页面加载时获取日志
onMounted(() => {
  loadLogs()
})

// 计算是否全选
const isAllSelected = computed(() => {
  const selectableLogs = logs.value.filter(log => log.id)
  return selectableLogs.length > 0 && selectedIds.value.length === selectableLogs.length
})

// 全选/取消全选
const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = logs.value.filter(log => log.id).map(log => log.id)
  }
}

// 确认删除单条
const confirmDelete = (log) => {
  pendingDeleteLog.value = log
  confirmMessage.value = `确定要删除这条日志吗？\n操作类型: ${getOperationLabel(log)}`
  confirmType.value = 'single'
  showConfirmDialog.value = true
}

// 确认批量删除
const confirmBatchDelete = () => {
  if (selectedIds.value.length === 0) return
  confirmMessage.value = `确定要删除选中的 ${selectedIds.value.length} 条日志吗？`
  confirmType.value = 'batch'
  showConfirmDialog.value = true
}

// 确认清空全部
const confirmClearAll = () => {
  confirmMessage.value = `确定要清空全部 ${logs.value.length} 条日志吗？此操作不可恢复！`
  confirmType.value = 'clear'
  confirmInput.value = ''
  showConfirmDialog.value = true
}

// 关闭确认弹窗
const closeConfirmDialog = () => {
  showConfirmDialog.value = false
  confirmMessage.value = ''
  confirmType.value = ''
  confirmInput.value = ''
  pendingDeleteLog.value = null
}

// 执行删除
const executeDelete = async () => {
  isLoading.value = true
  try {
    if (confirmType.value === 'single' && pendingDeleteLog.value) {
      await deleteLog(pendingDeleteLog.value.id)
      showToastMessage('日志已删除', 'success')
    } else if (confirmType.value === 'batch') {
      await deleteLogs(selectedIds.value)
      showToastMessage(`已删除 ${selectedIds.value.length} 条日志`, 'success')
      selectedIds.value = []
    } else if (confirmType.value === 'clear') {
      await clearLogs()
      showToastMessage('已清空全部日志', 'success')
      selectedIds.value = []
    }
    closeConfirmDialog()
    await loadLogs()
  } catch (error) {
    console.error('删除失败:', error)
    showToastMessage('删除失败，请重试', 'error')
  } finally {
    isLoading.value = false
  }
}

// 加载日志
const loadLogs = async () => {
  isLoading.value = true
  try {
    const data = await fetchLogs()
    if (data && data.logs) {
      logs.value = data.logs.reverse() // 最新的在前
    } else {
      logs.value = []
    }
  } catch (error) {
    console.error('获取日志失败:', error)
    showToastMessage('获取日志失败，请检查网络连接', 'error')
  } finally {
    isLoading.value = false
  }
}

// 刷新日志
const refreshLogs = () => {
  loadLogs()
  showToastMessage('日志已刷新', 'success')
}

// 获取操作类型标签
const getOperationLabel = (log) => {
  const operation = log.operation || log.type
  return operationMap[operation]?.label || operation || '未知操作'
}

// 获取操作类型样式
const getOperationTagClass = (log) => {
  const operation = log.operation || log.type
  return operationMap[operation]?.class || 'tag-primary'
}

// 获取目标文本
const getTargetText = (log) => {
  if (log.target) return log.target
  if (log.message) return log.message
  if (log.source) return `来源: ${log.source}`
  return '-'
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()

  const timeStr = date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })

  if (isToday) {
    return `今天 ${timeStr}`
  }

  const dateStr = date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric'
  })

  return `${dateStr} ${timeStr}`
}

// 显示提示
const showToastMessage = (message, type = 'success') => {
  toastMessage.value = message
  toastClass.value = type === 'error' ? 'toast-error' : 'toast-success'
  showToast.value = true
  setTimeout(() => {
    showToast.value = false
  }, 3000)
}
</script>

<style scoped>
.page-container {
  min-height: 400px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.btn-danger-outline {
  background: transparent;
  color: var(--danger);
  border: 1px solid var(--danger);
}

.btn-danger-outline:hover:not(:disabled) {
  background: var(--danger);
  color: white;
}

.btn-delete {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.btn-delete:hover:not(:disabled) {
  opacity: 1;
  background: var(--gray-100);
}

.btn-delete:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* 复选框样式 */
input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

input[type="checkbox"]:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.btn-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid var(--gray-400);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 表格样式 */
.table-container {
  overflow-x: auto;
}

.count-cell {
  font-weight: 600;
  color: var(--danger);
}

.time-cell {
  color: var(--gray-500);
  font-size: 13px;
  white-space: nowrap;
}

/* 标签样式覆盖 */
.tag {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 9999px;
  font-weight: 500;
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

/* 弹窗样式 */
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
  z-index: 1001;
}

.modal {
  background: white;
  border-radius: var(--radius);
  width: 90%;
  max-width: 400px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--gray-200);
}

.modal-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.modal-body {
  padding: 20px;
}

.modal-body p {
  margin: 0 0 16px 0;
  line-height: 1.5;
  white-space: pre-line;
}

.confirm-input {
  margin-top: 12px;
}

.input-hint {
  font-size: 13px;
  color: var(--gray-600);
  margin-bottom: 8px;
}

.confirm-input input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  font-size: 14px;
}

.confirm-input input:focus {
  outline: none;
  border-color: var(--primary);
}

.modal-footer {
  padding: 12px 20px 16px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 空状态样式 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-700);
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
  color: var(--gray-500);
}
</style>
