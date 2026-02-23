# 微信公众号数据监控系统 - 部署手册

## 项目概述

本系统是一个微信公众号文章采集数据的可视化监控系统，包含：
- 采集信息概览页面（统计数据、热力图）
- 数据采集预检页面（账号文章发布时间统计）
- 支持日期选择和数据刷新

## 技术栈

- **后端**: FastAPI (Python)
- **前端**: React + Ant Design + ECharts
- **数据库**: MySQL + MongoDB
- **部署**: Docker + Docker Compose

## 目录结构

```
monitor_progress/
├── backend/                 # 后端服务
│   ├── main.py             # API主文件
│   ├── models.py           # 数据模型
│   ├── database.py         # 数据库连接
│   ├── requirements.txt    # Python依赖
│   └── Dockerfile          # 后端Docker镜像
├── frontend/               # 前端应用
│   ├── src/                # 源代码
│   ├── public/             # 静态资源
│   ├── package.json        # Node依赖
│   ├── Dockerfile          # 前端Docker镜像
│   └── nginx.conf          # Nginx配置
├── scripts/                # 脚本文件
│   ├── qinglong_refresh.sh # Shell版本刷新脚本
│   └── qinglong_refresh.js # JavaScript版本刷新脚本
├── docker-compose.yml      # Docker Compose配置
├── .env.example            # 环境变量示例
└── DEPLOY.md               # 部署手册
```

## 快速开始

### 1. 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- MySQL 5.7+ (已有数据库)
- MongoDB 4.4+ (已有数据库)

### 2. 配置环境变量

复制环境变量示例文件：

```bash
cd monitor_progress
cp .env.example .env
```

编辑 `.env` 文件，根据实际情况修改数据库连接信息：

```env
MYSQL_HOST=192.168.2.18
MYSQL_PORT=3307
MYSQL_USER=rss_user
MYSQL_PASSWORD=pass123456
MYSQL_DB=we_mp_rss

MONGO_HOST=192.168.2.18
MONGO_PORT=27017
MONGO_USER=admin
MONGO_PASSWORD=password123
MONGO_DB_NAME=url_spider_db
```

### 3. 启动服务

使用 Docker Compose 构建并启动服务：

```bash
docker-compose up -d --build
```

### 4. 访问应用

- 前端界面: http://localhost:3000
- 后端API文档: http://localhost:8000/docs

## 常用命令

### 查看服务状态

```bash
docker-compose ps
```

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看后端日志
docker-compose logs -f backend

# 查看前端日志
docker-compose logs -f frontend
```

### 停止服务

```bash
docker-compose down
```

### 重启服务

```bash
docker-compose restart
```

### 更新代码后重新构建

```bash
docker-compose up -d --build
```

## 青龙面板定时任务配置

### 方式一：使用 JavaScript 脚本（推荐）

1. 打开青龙面板
2. 进入「定时任务」→「新建任务」
3. 填写任务信息：
   - 名称：数据监控刷新
   - 命令/脚本：复制 `scripts/qinglong_refresh.js` 内容
   - 定时规则：`0 0 * * * *` （每小时执行一次）
4. 添加环境变量：
   - 名称：`API_URL`
   - 值：`http://your-backend-ip:8000`

### 方式二：使用 Shell 脚本

1. 将 `scripts/qinglong_refresh.sh` 上传到服务器
2. 在青龙面板中创建任务，执行该脚本
3. 配置定时规则和环境变量

## API 接口说明

### 获取统计数据

```
GET /api/stats?date=2026-02-21
```

### 获取热力图数据

```
GET /api/heatmap?date=2026-02-21&score_type=pre_value_score
```

### 获取月度统计数据

```
GET /api/monthly-stats?page=1&page_size=30
```

## 故障排查

### 后端连接数据库失败

1. 检查 `.env` 文件中的数据库配置是否正确
2. 确认数据库服务是否正常运行
3. 检查网络连接和防火墙设置

### 前端无法访问后端API

1. 确认后端服务是否正常启动
2. 检查 `docker-compose.yml` 中的端口映射
3. 查看 Nginx 配置是否正确

### 数据显示异常

1. 检查数据库中是否有数据
2. 查看后端日志确认查询是否成功
3. 确认表名和字段名是否正确

## 数据结构说明

### MySQL 表

- `feeds`: 公众号账号信息
- `articles`: 文章基础信息

### MongoDB 集合

- `articles`: 文章加工后的数据（包含评分、全文、大模型总结等）

## 维护建议

1. 定期备份 MySQL 和 MongoDB 数据
2. 监控 Docker 容器运行状态
3. 根据需要调整定时任务频率
4. 定期清理日志文件

## 技术支持

如有问题，请检查：
1. Docker 容器日志
2. 数据库连接状态
3. 网络连通性




修复 mongo 集合问题
```
db('url_spider_db').collection('articles').updateMany(
  { "article_type": { "$type": "array" } },
  [
    {
      "$set": {
        "article_type": {
          "$cond": {
            "if": { "$gt": [{ "$size": "$article_type" }, 0] },
            "then": { 
              "$reduce": {
                "input": "$article_type",
                "initialValue": "",
                "in": {
                  "$cond": {
                    "if": { "$gt": ["$$this", "$$value"] },
                    "then": "$$this",
                    "else": "$$value"
                  }
                }
              }
            },
            "else": ""
          }
        }
      }
    }
  ]
)

```