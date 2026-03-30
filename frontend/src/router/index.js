import { createRouter, createWebHistory } from 'vue-router'
import TodayTrends from '../views/TodayTrends.vue'
import History from '../views/History.vue'
import Update from '../views/Update.vue'
import Keywords from '../views/Keywords.vue'
import Cleanup from '../views/Cleanup.vue'
import Logs from '../views/Logs.vue'

const routes = [
  {
    path: '/',
    name: 'TodayTrends',
    component: TodayTrends,
    meta: { title: '今日趋势' }
  },
  {
    path: '/history',
    name: 'History',
    component: History,
    meta: { title: '历史回顾' }
  },
  {
    path: '/update',
    name: 'Update',
    component: Update,
    meta: { title: '文献更新' }
  },
  {
    path: '/keywords',
    name: 'Keywords',
    component: Keywords,
    meta: { title: '关键词管理' }
  },
  {
    path: '/cleanup',
    name: 'Cleanup',
    component: Cleanup,
    meta: { title: '数据清理' }
  },
  {
    path: '/logs',
    name: 'Logs',
    component: Logs,
    meta: { title: '操作日志' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
