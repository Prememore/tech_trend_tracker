# 技术趋势追踪器（Tech Trend Tracker）

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Vue](https://img.shields.io/badge/Vue-3.5+-green)

一个**智能学术文献监测系统**，专注于追踪 arXiv 平台上的最新论文。系统采用分布式架构设计，集成 Web 前端、REST API 后端、智能过滤引擎和本地化数据存储，支持自动定时更新、动态关键词管理和灵活的数据清理策略。

**特点**：全本地化部署、无数据外传、支持多镜像源、实时更新监控。

---

## 功能特性

- **自动化抓取**
  - 从 arXiv API 实时抓取论文（支持多个镜像源）
  - 可配置的时间范围（1-365 天）
  - 国内稳定镜像源（清华/Azure/官方三选一）
  - 完整的错误处理和重试机制

- **智能过滤**
  - 基于关键词的多层级相关性评分（主要/次要关键词）
  - 支持标题/摘要/两者混合匹配
  - 可调节的相关性阈值（0.0-1.0）
  - 自动 LaTeX 标记清理

- **关键词管理**
  - 动态关键词配置（无需重启服务）
  - 支持 JSON 格式持久化存储
  - 预置强化学习和混沌控制领域关键词库，也可自定义关键词
  - Web 界面一键添加/编辑/删除

- **数据清理**
  - 灵活的清理策略（按天数/按日期/按范围/全清空）
  - 清理前预览受影响数据
  - 完整的操作日志记录

- **Web 界面**
  - Vue 3 + Vite 前端
  - 实时任务进度监控
  - 论文详情浏览和搜索
  - 操作日志查看
  - 响应式设计，支持多设备访问

- **API 文档**
  - 自动生成的 Swagger UI（`/docs`）
  - 全 RESTful 接口设计
  - 异步后台任务处理

- **本地化存储**
  - SQLite 本地数据库（无网络依赖）
  - 日期统计和趋势分析
  - 完整的数据持久化

---

## 技术栈

### 后端
| 组件 | 版本 | 说明 |
|------|------|------|
| **Python** | 3.9+ | 核心运行环境 |
| **FastAPI** | >=0.104.0 | Web 框架 |
| **uvicorn** | >=0.24.0 | ASGI 服务器 |
| **requests** | 2.31.0 | HTTP 客户端 |
| **feedparser** | 6.0.10 | RSS/Atom 解析 |
| **PyYAML** | 6.0.1 | 配置文件处理 |
| **APScheduler** | 3.10.4 | 定时任务调度 |
| **rich** | 13.7.1 | 终端美化输出 |

### 前端
| 组件 | 版本 | 说明 |
|------|------|------|
| **Vue** | 3.5.30 | 前端框架 |
| **Vue Router** | 4.6.4 | 路由管理 |
| **Vite** | 8.0.1 | 构建工具 |
| **Axios** | 1.13.6 | HTTP 客户端 |

### 数据存储
- **SQLite** - 本地关系型数据库，零配置部署

---

## 项目结构

```
tech_trend_tracker/
├── api/                          # FastAPI 应用核心
│   ├── app.py                    # FastAPI 应用入口
│   └── routes/                   # API 路由模块
│       ├── articles.py           # 论文查询 API
│       ├── update.py             # 文献更新 API
│       ├── keywords.py           # 关键词管理 API
│       ├── cleanup.py            # 数据清理 API
│       └── logs.py               # 操作日志 API
├── core/                         # 核心业务逻辑
│   ├── collector.py              # arXiv 采集器
│   ├── filter.py                 # 相关性过滤器
│   ├── keyword_manager.py        # 关键词管理器
│   ├── storage.py                # SQLite 数据库操作
│   └── text_utils.py             # 文本处理工具（LaTeX 清理）
├── frontend/                     # Vue 3 Web 前端
│   ├── src/
│   │   ├── components/           # 可复用组件
│   │   ├── views/                # 页面视图
│   │   │   ├── TodayTrends.vue   # 今日趋势
│   │   │   ├── History.vue       # 历史查询
│   │   │   ├── Keywords.vue      # 关键词管理
│   │   │   ├── Update.vue        # 手动更新
│   │   │   ├── Cleanup.vue       # 数据清理
│   │   │   └── Logs.vue          # 操作日志
│   │   ├── api/                  # API 通信模块
│   │   ├── router/               # 路由配置
│   │   ├── App.vue               # 根组件
│   │   └── main.js               # 入口
│   ├── dist/                     # 构建产物
│   └── vite.config.js            # Vite 配置
├── config/                       # 配置文件
│   ├── sources.yaml              # arXiv 源配置
│   └── keywords.json             # 关键词配置
├── data/                         # 数据文件
│   └── trends.db                 # SQLite 数据库
├── main.py                       # Web 服务启动入口
├── run_daily.py                  # 每日更新脚本
└── requirements.txt              # Python 依赖
```

---

## 快速开始

### 环境要求
- Python 3.9 或更高版本
- pip 包管理工具
- 可选：Node.js 16+（仅用于前端开发/构建）

### 1. 安装依赖

#### 后端依赖
```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境（macOS/Linux）
source .venv/bin/activate
# 或 Windows
# .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 前端依赖（可选，仅用于开发或重新构建前端）
```bash
cd frontend
npm install
```

### 2. 初始化数据

首次运行前，执行一次数据更新以初始化数据库：

```bash
python run_daily.py
```

这会根据 `config/sources.yaml` 中的配置从 arXiv 抓取最近 30 天（默认）的论文。

### 3. 启动 Web 服务

```bash
# 生产模式
python main.py

# 或指定监听地址和端口
python main.py --host 0.0.0.0 --port 8000

# 开发模式（启用热重载）
python main.py --reload
```

服务启动后，访问以下地址：
- **Web 界面**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs（Swagger UI）

---

## 配置说明

### 主配置文件：`config/sources.yaml`

```yaml
settings:
  search_days: 30                               # 抓取时间范围（天）
  arxiv_api_url: "https://arxiv.org/api/query"  # arXiv API 端点
  match_scope: "title"                          # 匹配范围：title/summary/both
  relevance_threshold: 0.3                      # 相关性阈值（0.0-1.0）

keywords:
  primary:                                      # 一级关键词（高优先级）
    - "reinforcement learning"
    - "deep reinforcement learning"
    - "ppo"
    - "sac"
    - "ddpg"
    - "td3"
    - "chaos synchronization"
    - "chaotic synchronization"
    - "chaos control"
  
  secondary:                                    # 二级关键词（低优先级）
    - "multiagent"
    - "robotic"
```

| 参数 | 类型 | 说明 | 范围 |
|------|------|------|------|
| `search_days` | int | 向前检索的天数 | 1-365 |
| `match_scope` | str | 关键词匹配范围 | `title`/`summary`/`both` |
| `relevance_threshold` | float | 最低相关性得分 | 0.0-1.0 |

通过 Web 界面或 API 可以动态修改关键词，无需重启服务。

---

## API 端点列表

### 论文查询

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/articles/today` | 获取今日论文列表 |
| `GET` | `/api/articles/history?date=YYYY-MM-DD` | 获取指定日期论文 |
| `GET` | `/api/articles/dates` | 获取有数据的日期列表 |
| `GET` | `/api/articles/{article_id}` | 获取单篇论文详情 |

### 文献更新

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/update` | 触发异步更新任务 |
| `GET` | `/api/update/status` | 查询更新任务状态 |

### 关键词管理

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/keywords` | 获取当前关键词配置 |
| `PUT` | `/api/keywords` | 更新关键词配置 |
| `POST` | `/api/keywords/reset` | 重置为默认关键词 |

### 数据清理

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/cleanup` | 执行数据清理 |
| `GET` | `/api/cleanup/preview` | 预览待清理数据 |

### 操作日志

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/logs` | 获取操作日志列表 |
| `DELETE` | `/api/logs/{log_id}` | 删除单条日志 |
| `DELETE` | `/api/logs` | 批量删除或清空日志 |

### 统计信息

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/stats` | 获取数据库统计信息 |

---

## 定时任务配置

### macOS / Linux（使用 cron）

```bash
# 编辑 crontab
crontab -e

# 添加每天凌晨 2 点自动更新
0 2 * * * cd /path/to/tech_trend_tracker && source .venv/bin/activate && python run_daily.py
```

### 手动触发更新

```bash
# 方式 1：命令行
python run_daily.py

# 方式 2：API 调用
curl -X POST http://localhost:8000/api/update \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'

# 方式 3：Web 界面 → 点击"文献更新"页面
```

---

## 开发和扩展

### 前端开发
```bash
cd frontend
npm run dev  # 启动开发服务器（http://localhost:5173）
```

### 添加新的 API 端点
在 `api/routes/` 中创建新的路由文件，然后在 `api/app.py` 中注册。

### 自定义过滤逻辑
编辑 `core/filter.py` 中的 `RelevanceFilter` 类。

---

## 许可证

MIT License

---
