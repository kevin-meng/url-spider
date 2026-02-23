# 微信公众号数据监控系统

## 📍 项目位置

**绝对路径**: `/Users/kevin/obsidian_notes/url_spider/new/monitor_progress`

## 📋 项目概述

本项目是一个微信公众号数据监控系统，集成了前后端功能，用于监控、管理和分析微信公众号文章数据。系统提供了丰富的统计数据可视化、文章管理和链接解析功能，帮助用户更好地理解和利用公众号文章数据。

## 🛠️ 技术栈

### 前端
- **框架**: React 18+
- **UI 库**: Ant Design 5+
- **图表库**: ECharts (通过 echarts-for-react)
- **HTTP 客户端**: Axios
- **时间处理**: dayjs
- **Markdown 渲染**: react-markdown

### 后端
- **框架**: FastAPI
- **数据库**: MongoDB + MySQL
- **服务**: Clipper Service (网页剪藏) + LLM Service (大模型摘要)
- **任务队列**: 内存队列 + 优先级调度
- **并发控制**: asyncio

## 🚀 快速启动

### 本地启动

#### 1. 启动后端服务

```bash
cd /Users/kevin/obsidian_notes/url_spider/new/monitor_progress
# 激活虚拟环境
source /Users/kevin/obsidian_notes/url_spider/new/venv/bin/activate
# 安装依赖
pip install -r backend/requirements.txt
# 启动后端服务
python backend/main.py
```

#### 2. 启动前端服务

```bash
cd /Users/kevin/obsidian_notes/url_spider/new/monitor_progress/frontend
# 安装依赖
npm install
# 启动前端服务
npm start
```

### Docker 启动

```bash
cd /Users/kevin/obsidian_notes/url_spider/new/monitor_progress
docker-compose up -d --build
```

**服务地址**:
- 前端: `http://localhost:3013`
- 后端: `http://localhost:8013`

## 🎨 前端功能

### 1. 监控面板 (MonitorProgress)

**功能**: 展示统计数据、热力图和月度统计

**主要组件**:
- 统计卡片: 显示总公众号数、总文章数、今日文章数等关键指标
- 热力图: 展示不同评分区间的文章分布
- 月度统计表: 展示公众号月度发文数量

**API 调用**:
- `/api/stats`: 获取统计数据
- `/api/heatmap`: 获取热力图数据
- `/api/monthly-stats`: 获取月度统计数据

### 2. 文章管理 (ArticleManagement)

**功能**: 管理文章列表，支持筛选、排序和编辑

**主要功能**:
- 文章列表: 显示文章标题、评分、来源等信息
- 筛选功能: 支持按评分、标签、收藏状态等筛选
- 排序功能: 支持按评分、发布时间等排序
- 文章详情: 查看和编辑文章详情，包括概要、原因、标签等
- 折叠功能: 支持折叠基本信息和标签组

**API 调用**:
- `/api/articles`: 获取文章列表
- `/api/articles/{article_id}`: 获取文章详情

### 3. 链接解析 (LinkParser)

**功能**: 批量处理 URL 链接，包括检查数据库、抓取文章、生成摘要等

**主要功能**:
- URL 输入: 支持粘贴多个 URL 链接
- 批量处理: 支持批量提交 URL 进行处理
- 任务状态跟踪: 实时显示任务处理状态和进度
- 详情查看: 查看处理结果的详细信息
- 大模型摘要: 支持选择是否使用大模型生成摘要

**API 调用**:
- `/api/process-url`: 处理单条 URL
- `/api/batch-process-urls`: 批量处理 URL
- `/api/task-status/{task_id}`: 获取任务状态

## 🔗 后端接口

### 1. 统计数据接口

- **GET /api/stats**: 获取统计数据
  - 参数: `date` (可选，格式: YYYY-MM-DD)
  - 返回: 统计数据，包括总公众号数、总文章数、今日文章数等

- **GET /api/heatmap**: 获取热力图数据
  - 参数: `date` (格式: YYYY-MM-DD), `score_type` (可选，默认为 "pre_value_score")
  - 返回: 热力图数据，按评分区间和文章类型分布

- **GET /api/monthly-stats**: 获取月度统计数据
  - 参数: `page` (可选，默认为 1), `page_size` (可选，默认为 30)
  - 返回: 月度统计数据，按公众号和月份分组
  - 代码 
    - ```
    cd /Users/kevin/obsidian_notes/url_spider/new && source venv/bin/activate && python monitor_progress/backend/backfill_stats.py
    ```

### 2. 文章管理接口

- **GET /api/articles**: 获取文章列表
  - 参数: 
    - `page`: 页码 (默认为 1)
    - `page_size`: 每页大小 (默认为 10)
    - `score_type`: 评分类型 (默认为 "socre")
    - `scores`: 评分范围 (逗号分隔的字符串，如 "7,8,9,10")
    - `tags`: 标签 (逗号分隔的字符串)
    - `is_collected`: 是否收藏 (布尔值)
    - `is_followed`: 是否关注 (布尔值)
    - `is_enabled`: 是否启用 (布尔值)
    - `is_read`: 是否已读 (布尔值)
    - `sort_by`: 排序字段 (默认为 "publish_time")
    - `sort_order`: 排序顺序 (默认为 "desc")
    - `start_date`: 开始日期 (格式: YYYY-MM-DD)
    - `end_date`: 结束日期 (格式: YYYY-MM-DD)
  - 返回: 文章列表，包括分页信息

- **GET /api/articles/{article_id}**: 获取文章详情
  - 参数: `article_id` (文章 ID)
  - 返回: 文章详细信息

- **PUT /api/articles/{article_id}**: 更新文章信息
  - 参数: `article_id` (文章 ID)
  - 体: 要更新的文章字段
  - 返回: 更新后的文章信息

### 3. URL 处理接口

- **GET /api/check-url**: 检查 URL 是否存在于数据库中
  - 参数: `url` (要检查的 URL)
  - 返回: URL 存在状态和相关信息

- **POST /api/process-url**: 处理单条 URL 链接
  - 体: `{"url": "...", "use_llm_summary": true/false}`
  - 返回: 任务 ID 和状态

- **POST /api/batch-process-urls**: 批量处理 URL 链接
  - 体: `{"urls": ["..."], "use_llm_summary": true/false, "priority": "high/normal/low", "max_concurrency": 2}`
  - 返回: 批次任务 ID 和状态

- **GET /api/task-status/{task_id}**: 获取任务状态
  - 参数: `task_id` (任务 ID)
  - 返回: 任务状态、进度和结果

### 4. 服务接口

- **POST /api/clip**: 剪藏文章
  - 体: `{"url": "..."}`
  - 返回: 剪藏结果，包括标题、内容等

- **POST /api/summarize**: 生成文章摘要
  - 体: `{"markdown_content": "..."}`
  - 返回: 摘要结果

- **POST /api/evaluate**: 评估文章
  - 体: `{"articles": [{"title": "...", "description": "..."}]}`
  - 返回: 评估结果，包括评分和分类

### 5. 任务触发接口

- **POST /api/trigger/task1**: 触发任务 1 (获取并评估文章)
  - 返回: 触发状态

- **POST /api/trigger/task2**: 触发任务 2 (剪藏内容)
  - 返回: 触发状态

- **POST /api/trigger/task3**: 触发任务 3 (总结内容)
  - 返回: 触发状态

- **POST /api/trigger/task4**: 触发任务 4 (计算统计数据)
  - 返回: 触发状态

## 📂 项目结构

```
monitor_progress/
├── backend/                  # 后端代码
│   ├── services/             # 业务逻辑服务
│   │   ├── clipper_service.py  # 剪藏服务
│   │   └── llm_service.py       # LLM 服务
│   ├── tasks/                # 定时任务
│   │   ├── task1_fetch.py       # 任务 1: 获取并评估文章
│   │   ├── task2_clip.py        # 任务 2: 剪藏内容
│   │   ├── task3_summarize.py   # 任务 3: 总结内容
│   │   └── task4_stats.py       # 任务 4: 计算统计数据
│   ├── main.py               # 后端入口
│   ├── database.py           # 数据库连接
│   ├── stats_calculator.py   # 统计数据计算器
│   └── requirements.txt      # 后端依赖
├── frontend/                 # 前端代码
│   ├── src/                  # 源代码
│   │   ├── features/         # 功能模块
│   │   │   ├── monitor/         # 监控面板
│   │   │   │   ├── MonitorProgress.js
│   │   │   │   ├── HeatmapChart.js
│   │   │   │   └── MonthlyTable.js
│   │   │   └── article/         # 文章管理
│   │   │       ├── ArticleManagement.js
│   │   │       ├── ArticleList.js
│   │   │       ├── ArticleDetail.js
│   │   │       ├── FieldValue.js
│   │   │       └── LinkParser.js
│   │   ├── App.js             # 应用入口
│   │   └── index.js           # 渲染入口
│   ├── package.json          # 前端依赖
│   └── Dockerfile             # 前端 Docker 配置
├── prepare/                  # 准备数据的脚本
│   ├── add_feeds_sample.py    # 添加公众号样本
│   └── extract_data.py        # 提取数据
├── scripts/                  # 工具脚本
│   ├── qinglong_refresh.js    # 青龙面板刷新
│   └── qinglong_stats.js      # 青龙面板统计
├── docker-compose.yml         # Docker 编排配置
├── .env.example               # 环境变量示例
└── README.md                  # 项目说明
```

## 📊 数据流程

1. **数据收集**: 通过定时任务从 MySQL 数据库同步文章链接到 MongoDB
2. **数据处理**: 
   - 剪藏服务: 抓取文章内容并转换为 Markdown
   - LLM 服务: 对文章进行评分、分类和总结
3. **数据存储**: 将处理后的数据存储到 MongoDB 和 MySQL
4. **数据可视化**: 前端从后端 API 获取数据并进行可视化展示
5. **用户交互**: 用户可以通过前端界面管理文章、处理 URL 和查看统计数据

## 🔧 核心功能

### 1. 统计数据计算

- **每日统计**: 计算每日文章数量、剪藏率、摘要率等
- **热力图统计**: 计算不同评分区间的文章分布
- **月度统计**: 计算公众号月度发文数量

### 2. 文章管理

- **筛选功能**: 支持按评分、标签、收藏状态等筛选文章
- **排序功能**: 支持按评分、发布时间等排序文章
- **编辑功能**: 支持编辑文章详情，包括概要、原因、标签等

### 3. URL 处理

- **批量提交**: 支持粘贴多个 URL 进行批量处理
- **任务队列**: 支持任务优先级和并发控制
- **状态跟踪**: 实时显示任务处理状态和进度
- **结果查看**: 查看处理结果的详细信息

### 4. 剪藏服务

- **微信公众号特化**: 强制使用 `markdownify` 提取，确保图片和链接不丢失
- **通用网页**: 使用 `trafilatura` (带 Fallback 机制) 提取
- **并发处理**: 支持多线程并发剪藏，提高处理效率

### 5. LLM 服务

- **文章摘要**: 生成文章摘要，支持 Markdown 预处理
- **文章评估**: 对文章进行评分和分类
- **多模型支持**: 支持 OpenAI 和 Anthropic 模型

## 📝 配置说明

### 环境变量

参考 `.env.example` 文件配置环境变量，主要包括：

- MongoDB 连接信息
- MySQL 连接信息
- LLM API 密钥
- 服务端口和地址

### 定时任务

在青龙面板中配置定时任务，参考 `QINGLONG_GUIDE.md` 文件。

## 🔒 注意事项

1. **数据库连接**: 确保 MongoDB 和 MySQL 服务正常运行，且连接信息配置正确
2. **LLM API 密钥**: 确保配置了正确的 LLM API 密钥，否则无法使用摘要和评估功能
3. **并发控制**: 批量处理 URL 时，注意设置合理的并发数，避免系统过载
4. **定时任务**: 确保青龙面板中的定时任务配置正确，否则无法自动同步和处理文章
5. **Docker 网络**: 使用 Docker 启动时，确保容器间网络通信正常

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 📄 许可证

本项目使用 MIT 许可证。