/**
 * 青龙面板任务脚本：计算统计数据
 * 功能：调用后端 API 触发统计数据计算任务
 */

const axios = require('axios');

// 后端 API 地址
const API_URL = 'http://localhost:8000/api/trigger/task4';

console.log('开始执行统计数据计算任务...');

async function runTask() {
    try {
        const response = await axios.post(API_URL);
        console.log('任务触发成功:', response.data);
        console.log('统计数据计算任务已在后台启动');
    } catch (error) {
        console.error('任务触发失败:', error.message);
        if (error.response) {
            console.error('错误响应:', error.response.data);
        }
        throw error;
    }
}

runTask()
    .then(() => {
        console.log('任务执行完成');
        process.exit(0);
    })
    .catch((error) => {
        console.error('任务执行失败:', error);
        process.exit(1);
    });
