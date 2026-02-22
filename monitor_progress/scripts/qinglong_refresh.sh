#!/bin/bash

# 微信公众号数据监控系统 - 数据刷新脚本
# 用于青龙面板定时任务

# 配置
API_URL="${API_URL:-http://localhost:8000}"
LOG_FILE="${LOG_FILE:-/tmp/monitor_refresh.log}"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "========== 开始数据刷新任务 =========="

# 检查API是否可用
log "检查API服务状态..."
if curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/stats" | grep -q "200"; then
    log "API服务正常"
    
    # 预加载统计数据
    log "预加载统计数据..."
    curl -s "$API_URL/api/stats" > /dev/null
    log "统计数据加载完成"
    
    # 预加载热力图数据
    log "预加载热力图数据..."
    curl -s "$API_URL/api/heatmap" > /dev/null
    curl -s "$API_URL/api/heatmap?score_type=score" > /dev/null
    log "热力图数据加载完成"
    
    # 预加载月度统计数据
    log "预加载月度统计数据..."
    curl -s "$API_URL/api/monthly-stats" > /dev/null
    log "月度统计数据加载完成"
    
    log "========== 数据刷新任务完成 =========="
else
    log "错误: API服务不可用"
    log "========== 数据刷新任务失败 =========="
    exit 1
fi
