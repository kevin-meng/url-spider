# URL Spider Service

本项目是一个自动化文章采集、剪藏与评估系统，支持并发处理、超时控制和历史数据补数。

## 📍 项目位置

**绝对路径**: `/Users/kevin/obsidian_notes/url_spider/new`

## 🛠️ 核心功能

1.  **自动同步**: 从 MySQL 数据库同步文章链接到 MongoDB。
2.  **智能剪藏**:
    *   自动识别网页正文并转换为 Markdown。
    *   **微信公众号特化**: 强制使用 `markdownify` 提取，确保图片和链接不丢失。
    *   **通用网页**: 使用 `trafilatura` (带 Fallback 机制) 提取。
    *   **并发处理**: 支持多线程并发剪藏，提高处理效率。
    *   **超时控制**: 自动在 1小时45分钟后终止，避免无限运行。
3.  **价值评估** (可选): 调用 LLM 对文章进行评分和分类。
4.  **自动总结** (可选): 
    *   生成文章摘要。
    *   **Markdown 预处理**: 自动移除图片、链接和元数据，节省大模型 tokens。
    *   **评分优先处理**: 从高分到低分依次处理文章 (10 → 3)。
    *   **并发处理**: 支持多线程并发总结。

## 🚀 快速启动

### 本地启动

```bash
cd /Users/kevin/obsidian_notes/url_spider/new/url_spider_service/
python main.py
```

### Docker 启动 (可选)

```bash
cd /Users/kevin/obsidian_notes/url_spider/new/url_spider_service/
docker-compose up -d --build
```

**重启服务** (代码修改后):
```bash
docker-compose restart
```

**查看日志**:
```bash
docker-compose logs -f
```

## 📦 本地开发与维护

### 1. 激活虚拟环境
```bash
source /Users/kevin/obsidian_notes/url_spider/new/venv/bin/activate
```

### 2. 运行定时任务

**任务 1 (同步)**: 从 MySQL 同步文章到 MongoDB
```bash
cd /Users/kevin/obsidian_notes/url_spider/new/url_spider_service/
python tasks/task1_fetch.py
```

**任务 2 (剪藏)**: 处理过去两天的文章
```bash
python tasks/task2_clip.py
```

**任务 3 (总结)**: 按评分优先处理文章
```bash
python tasks/task3_summarize.py
```

### 3. 手动运行补数脚本 (历史数据处理)

**剪藏补数**: 处理历史遗留数据
```bash
python backfill_clipper.py
```

**总结补数**: 按评分优先处理历史文章
```bash
python backfill_summarize.py
```

### 4. 检查处理进度

```bash
python check_progress.py
```

## 🔗 接口说明

服务暴露端口: `8013`

*   **触发任务 1 (同步)**: `POST http://localhost:8013/api/trigger/task1`
*   **触发任务 2 (剪藏)**: `POST http://localhost:8013/api/trigger/task2`
*   **触发任务 3 (总结)**: `POST http://localhost:8013/api/trigger/task3`

详细配置请参考: `QINGLONG_GUIDE.md`

## 🧪 测试

所有测试文件已整理到 `tests/` 目录：

```bash
cd /Users/kevin/obsidian_notes/url_spider/new/url_spider_service/
python -m pytest tests/ -v
```

### 常用测试脚本

*   **测试单篇文章剪藏**: `python tests/test_clip_single.py`
*   **批量测试剪藏**: `python tests/test_clip_multiple.py`
*   **测试总结功能**: `python tests/test_task3_summarize.py`
*   **测试 Markdown 预处理**: `python tests/test_preprocess.py`

## 📂 目录结构

```
url_spider_service/
├── backfill_clipper.py        # 剪藏补数脚本
├── backfill_evaluate.py       # 评估补数脚本
├── backfill_summarize.py      # 总结补数脚本
├── check_progress.py          # 进度检查脚本
├── database.py                # 数据库操作模块
├── main.py                    # 主服务入口
├── services/                  # 业务逻辑服务
│   ├── clipper_service.py     # 剪藏服务
│   └── llm_service.py         # LLM 服务
├── tasks/                     # 定时任务
│   ├── task1_fetch.py         # 同步任务
│   ├── task2_clip.py          # 剪藏任务
│   └── task3_summarize.py      # 总结任务
├── tests/                     # 测试目录
│   ├── test_clip_single.py    # 单篇剪藏测试
│   ├── test_clip_multiple.py  # 批量剪藏测试
│   ├── test_task2_clip.py     # 剪藏任务测试
│   ├── test_task3_summarize.py # 总结任务测试
│   ├── test_preprocess.py     # Markdown 预处理测试
│   └── ...
└── docker-compose.yml         # Docker 配置
inbox/                         # 本地剪藏结果 (测试用)
tmp/                           # 临时/归档文件目录
venv/                          # Python 虚拟环境
```

## 📝 技术特点

*   **并发处理**: 使用 asyncio Semaphore 控制并发数量
*   **超时控制**: 基于信号的超时处理机制
*   **Markdown 预处理**: 正则表达式移除不必要内容
*   **评分优先**: 从高分到低分依次处理文章
*   **进度跟踪**: 实时显示处理进度和完成情况
*   **错误处理**: 完善的异常捕获和错误提示

## 🛠️ 依赖项

主要依赖项：
*   Python 3.13+
*   asyncio
*   pymongo
*   mysql-connector-python
*   markdownify
*   trafilatura
*   requests

## 📄 配置文件

*   `requirements.txt`: Python 依赖包
*   `docker-compose.yml`: Docker 容器配置

## 🔒 注意事项

*   确保 MongoDB 和 MySQL 服务正常运行
*   配置文件中的数据库连接信息需要根据实际环境修改
*   剪藏和总结任务会消耗较多网络带宽和计算资源
*   LLM 调用需要配置正确的 API 密钥

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。
