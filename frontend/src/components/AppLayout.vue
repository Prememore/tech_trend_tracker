<template>
  <div class="app-layout">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h1 class="app-title">技术趋势追踪器</h1>
      </div>
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: $route.path === item.path }"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <header class="content-header">
        <h2 class="page-title">{{ pageTitle }}</h2>
      </header>
      <div class="content-body">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { path: '/', label: '今日趋势', icon: '📊' },
  { path: '/history', label: '历史回顾', icon: '📜' },
  { path: '/update', label: '文献更新', icon: '🔄' },
  { path: '/keywords', label: '关键词管理', icon: '🏷️' },
  { path: '/cleanup', label: '数据清理', icon: '🧹' },
  { path: '/logs', label: '操作日志', icon: '📝' }
]

const pageTitle = computed(() => {
  return route.meta?.title || '技术趋势追踪器'
})
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}

/* 侧边栏样式 */
.sidebar {
  width: 220px;
  background: linear-gradient(180deg, #1a1f2e 0%, #252b3d 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.app-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin: 0;
  line-height: 1.4;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 4px;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.nav-item.active {
  background: #3b82f6;
  color: #fff;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
}

.nav-icon {
  font-size: 18px;
  margin-right: 12px;
  width: 24px;
  text-align: center;
}

.nav-label {
  font-size: 14px;
  font-weight: 500;
}

/* 主内容区样式 */
.main-content {
  flex: 1;
  margin-left: 220px;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.content-header {
  background: #fff;
  padding: 20px 32px;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
}

.content-body {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .sidebar {
    width: 64px;
  }

  .sidebar-header {
    padding: 16px 8px;
  }

  .app-title {
    font-size: 12px;
    text-align: center;
  }

  .nav-item {
    padding: 12px;
    justify-content: center;
  }

  .nav-icon {
    margin-right: 0;
  }

  .nav-label {
    display: none;
  }

  .main-content {
    margin-left: 64px;
  }

  .content-header,
  .content-body {
    padding-left: 16px;
    padding-right: 16px;
  }
}
</style>
