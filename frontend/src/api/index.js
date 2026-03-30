import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log(`[API Request] ${config.method.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('[API Error]', error.message)
    return Promise.reject(error)
  }
)

// ==================== 文章相关 API ====================

// 获取今日文章
export const fetchTodayArticles = () => {
  return api.get('/articles/today')
}

// 获取历史文章
export const fetchHistoryArticles = (date) => {
  return api.get('/articles/history', { params: { date } })
}

// 获取所有日期列表
export const fetchDates = () => {
  return api.get('/articles/dates')
}

// 获取文章详情
export const fetchArticleDetail = (id) => {
  return api.get(`/articles/${id}`)
}

// ==================== 更新相关 API ====================

// 触发文献更新
export const triggerUpdate = (days = 1) => {
  return api.post('/update', { days })
}

// 获取更新状态
export const fetchUpdateStatus = () => {
  return api.get('/update/status')
}

// ==================== 关键词管理 API ====================

// 获取关键词配置
export const fetchKeywords = () => {
  return api.get('/keywords')
}

// 更新关键词配置
export const updateKeywords = (data) => {
  return api.put('/keywords', data)
}

// 重置关键词为默认
export const resetKeywords = () => {
  return api.post('/keywords/reset')
}

// ==================== 数据清理 API ====================

// 执行清理
export const executeCleanup = (params) => {
  return api.post('/cleanup', params)
}

// 预览清理结果
export const previewCleanup = (params) => {
  return api.get('/cleanup/preview', { params })
}

// ==================== 日志和统计 API ====================

// 获取操作日志
export const fetchLogs = () => {
  return api.get('/logs')
}

// 删除单条日志
export const deleteLog = (id) => {
  return api.delete(`/logs/${id}`)
}

// 批量删除日志
export const deleteLogs = (ids) => {
  return api.delete('/logs', { data: { ids } })
}

// 清空全部日志
export const clearLogs = () => {
  return api.delete('/logs', { data: {} })
}

// 获取统计数据
export const fetchStats = () => {
  return api.get('/stats')
}

export default api
