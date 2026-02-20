# URL Spider Service (Mac2 Old)

本项目是一个自动化文章采集、剪藏与评估系统，部署在这台旧款 Mac (Mac2 Old) 上。

## 📍 项目位置

**绝对路径**: `/Users/alex/Projects/url_spider/new`

## 🛠️ 核心功能

1.  **自动同步**: 从 MySQL 数据库同步文章链接到 MongoDB。
2.  **智能剪藏**:
    *   自动识别网页正文并转换为 Markdown。
    *   **微信公众号特化**: 强制使用 `markdownify` 提取，确保图片和链接不丢失。
    *   **通用网页**: 使用 `trafilatura` (带 Fallback 机制) 提取。
3.  **价值评估** (可选): 调用 LLM 对文章进行评分和分类。
4.  **自动总结** (可选): 生成文章摘要。

## 🚀 快速启动 (Docker)

进入服务目录并启动容器：

```bash
cd /Users/alex/Projects/url_spider/new/url_spider_service/
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
source /Users/alex/Projects/url_spider/new/venv/bin/activate
```

### 2. 手动运行补数脚本 (存量数据处理)
用于处理历史遗留数据，将 MySQL 中的旧文章剪藏到 MongoDB。
```bash
cd /Users/alex/Projects/url_spider/new/url_spider_service/
python backfill_clipper.py
```

### 3. 测试剪藏效果
测试单篇文章剪藏，结果会保存为 `test_clip_result.md`。
```bash
python test_clip_single.py
```
批量测试 (微信 + 通用):
```bash
python test_clip_multiple.py
```

## 🔗 接口说明 (青龙面板集成)

服务暴露端口: `8013` (映射到宿主机 `192.168.2.18`)

*   **触发任务 1 (同步)**: `POST http://192.168.2.18:8013/api/trigger/task1`
*   **触发任务 2 (剪藏)**: `POST http://192.168.2.18:8013/api/trigger/task2`
*   **触发任务 3 (总结)**: `POST http://192.168.2.18:8013/api/trigger/task3`

详细青龙配置请参考: `QINGLONG_GUIDE.md`

## 📂 目录结构

*   `url_spider_service/`: 核心服务代码
    *   `services/`: 业务逻辑 (Clipper, LLM)
    *   `tasks/`: 定时任务脚本
    *   `docker-compose.yml`: 容器编排
*   `inbox/`: 本地剪藏结果 (测试用)
*   `tmp/`: 临时/归档文件目录
