/*
微信公众号数据监控系统 - 数据刷新脚本 (JavaScript版本)
用于青龙面板定时任务

使用说明：
1. 将此脚本添加到青龙面板
2. 设置定时规则：0 0 * * * * （每小时执行一次）
3. 配置环境变量 API_URL 为你的后端API地址
*/

const API_URL = process.env.API_URL || 'http://localhost:8000';

async function request(path) {
    const url = `${API_URL}${path}`;
    try {
        const response = await fetch(url);
        if (response.ok) {
            console.log(`✓ ${path} 请求成功`);
            return true;
        } else {
            console.log(`✗ ${path} 请求失败: ${response.status}`);
            return false;
        }
    } catch (error) {
        console.log(`✗ ${path} 请求异常: ${error.message}`);
        return false;
    }
}

async function main() {
    console.log('========== 开始数据刷新任务 ==========');
    console.log(`API地址: ${API_URL}`);
    
    const results = await Promise.all([
        request('/api/stats'),
        request('/api/heatmap'),
        request('/api/heatmap?score_type=score'),
        request('/api/monthly-stats')
    ]);
    
    const successCount = results.filter(r => r).length;
    console.log(`========== 任务完成: ${successCount}/${results.length} 成功 ==========`);
    
    if (successCount < results.length) {
        process.exit(1);
    }
}

main().catch(error => {
    console.error('任务执行异常:', error);
    process.exit(1);
});
