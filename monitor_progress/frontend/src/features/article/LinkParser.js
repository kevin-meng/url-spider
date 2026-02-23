import React, { useState, useEffect } from 'react';
import { Button, Input, Space, Table, Tag, message, Modal, Checkbox, Form, Progress, Alert } from 'antd';
import axios from 'axios';

const { TextArea } = Input;

// 后端接口地址
const MONITOR_API_BASE = ''; // 使用相对路径，与 App.js 保持一致

const LinkParser = () => {
  const [urls, setUrls] = useState('');
  const [useLLMSummary, setUseLLMSummary] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [results, setResults] = useState([]);
  const [currentProgress, setCurrentProgress] = useState(0);
  const [totalProgress, setTotalProgress] = useState(0);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [currentDetail, setCurrentDetail] = useState(null);
  const [form] = Form.useForm();

  // 处理URL输入
  const handleUrlChange = (e) => {
    setUrls(e.target.value);
  };

  // 处理大模型摘要勾选
  const handleLLMSummaryChange = (e) => {
    setUseLLMSummary(e.target.checked);
  };

  // 轮询任务状态
  const pollTaskStatus = async (taskId, url, index, total) => {
    try {
      const response = await axios.get(`${MONITOR_API_BASE}/api/task-status/${taskId}`);
      const taskStatus = response.data;

      // 更新结果状态
      setResults(prev => {
        const newResults = [...prev];
        const existingIndex = newResults.findIndex(item => item.taskId === taskId);
        if (existingIndex >= 0) {
          newResults[existingIndex] = {
            ...newResults[existingIndex],
            status: taskStatus.status === 'completed' ? 'success' : 
                    taskStatus.status === 'failed' ? 'error' : 'processing',
            message: taskStatus.message,
            progress: taskStatus.progress || 0,
            currentStage: taskStatus.current_stage,
            articleId: taskStatus.result?.article_id,
            data: taskStatus.result?.data
          };
        }
        return newResults;
      });

      // 如果任务未完成，继续轮询
      if (taskStatus.status === 'processing') {
        setTimeout(() => pollTaskStatus(taskId, url, index, total), 2000);
      } else {
        // 任务完成后更新整体进度
        setCurrentProgress(prev => Math.min(100, prev + (100 / total)));
      }

    } catch (error) {
      console.error('获取任务状态失败:', error);
      setResults(prev => {
        const newResults = [...prev];
        const existingIndex = newResults.findIndex(item => item.taskId === taskId);
        if (existingIndex >= 0) {
          newResults[existingIndex] = {
            ...newResults[existingIndex],
            status: 'error',
            message: '获取任务状态失败: ' + (error.message || '未知错误')
          };
        }
        return newResults;
      });
    }
  };

  // 处理URL
  const processUrl = async (url, index, total) => {
    try {
      // 调用后端的process-url接口处理完整流程
      const response = await axios.post(`${MONITOR_API_BASE}/api/process-url`, {
        url,
        use_llm_summary: useLLMSummary
      });
      
      const result = response.data;
      
      // 如果返回了task_id，开始轮询任务状态
      if (result.task_id) {
        // 创建初始结果记录
        const initialResult = {
          url,
          taskId: result.task_id,
          status: 'processing',
          message: result.message,
          progress: 0,
          currentStage: '初始化',
          data: null
        };
        
        // 添加到结果列表
        setResults(prev => [...prev, initialResult]);
        
        // 开始轮询任务状态
        setTimeout(() => pollTaskStatus(result.task_id, url, index, total), 1000);
        
        return initialResult;
      } else {
        // 兼容旧接口格式
        const oldFormatResult = {
          url,
          status: result.status,
          message: result.message,
          data: result.data
        };
        
        // 添加到结果列表
        setResults(prev => [...prev, oldFormatResult]);
        
        return oldFormatResult;
      }
    } catch (error) {
      console.error('处理URL失败:', error);
      const errorResult = {
        url,
        status: 'error',
        message: `处理失败: ${error.message || '未知错误'}`,
        data: null
      };
      
      // 添加到结果列表
      setResults(prev => [...prev, errorResult]);
      
      return errorResult;
    }
  };

  // 轮询批次任务状态
  const pollBatchTaskStatus = async (taskId, urlList) => {
    try {
      const response = await axios.get(`${MONITOR_API_BASE}/api/task-status/${taskId}`);
      const taskStatus = response.data;

      // 更新整体进度
      setCurrentProgress(taskStatus.progress || 0);

      // 如果是批次任务，更新子任务状态
      if (taskStatus.sub_task_statuses) {
        const subTaskStatuses = taskStatus.sub_task_statuses || [];
        
        // 更新结果列表
        setResults(prev => {
          const newResults = [...prev];
          subTaskStatuses.forEach(subTask => {
            const existingIndex = newResults.findIndex(item => item.taskId === subTask.task_id);
            if (existingIndex >= 0) {
              newResults[existingIndex] = {
                ...newResults[existingIndex],
                status: subTask.status === 'completed' ? 'success' : 
                        subTask.status === 'failed' ? 'error' : 'processing',
                message: subTask.message,
                progress: subTask.progress || 0,
                currentStage: subTask.current_stage,
                articleId: subTask.result?.article_id,
                data: subTask.result?.data
              };
            }
          });
          return newResults;
        });
      }

      // 如果任务未完成，继续轮询
      if (taskStatus.status === 'processing' || taskStatus.status === 'queued') {
        setTimeout(() => pollBatchTaskStatus(taskId, urlList), 2000);
      } else {
        // 任务完成后更新整体进度
        setCurrentProgress(100);
        setProcessing(false);
        
        // 发送浏览器通知
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification('任务完成', {
            body: `批次任务已完成，共处理 ${urlList.length} 个URL`,
            icon: '/favicon.ico'
          });
        }
        
        message.success('处理完成');
      }

    } catch (error) {
      console.error('获取任务状态失败:', error);
      setProcessing(false);
      message.error('获取任务状态失败');
    }
  };

  // 处理提交
  const handleSubmit = async () => {
    if (!urls.trim()) {
      message.warning('请输入URL链接');
      return;
    }

    setProcessing(true);
    setResults([]);
    setCurrentProgress(0);

    // 分割URLs，支持多行输入
    const urlList = urls.split('\n').filter(url => url.trim());
    setTotalProgress(urlList.length);

    try {
      // 请求通知权限
      if ('Notification' in window && Notification.permission !== 'denied') {
        await Notification.requestPermission();
      }

      // 调用批量处理接口
      const response = await axios.post(`${MONITOR_API_BASE}/api/batch-process-urls`, {
        urls: urlList,
        use_llm_summary: useLLMSummary,
        priority: 'normal'
      });

      const result = response.data;
      
      // 如果返回了task_id，开始轮询任务状态
      if (result.task_id) {
        // 为每个URL创建初始结果记录
        const initialResults = urlList.map(url => ({
          url,
          taskId: result.sub_task_ids ? result.sub_task_ids[urlList.indexOf(url)] : null,
          status: 'queued',
          message: '任务已加入队列，等待处理',
          progress: 0,
          currentStage: '排队中',
          data: null
        }));
        
        // 添加到结果列表
        setResults(initialResults);
        
        // 开始轮询任务状态
        setTimeout(() => pollBatchTaskStatus(result.task_id, urlList), 1000);
      } else {
        message.error('获取任务ID失败');
        setProcessing(false);
      }
    } catch (error) {
      message.error('处理过程中出现错误: ' + (error.message || '未知错误'));
      console.error(error);
      setProcessing(false);
    }
  };

  // 查看详情
  const handleViewDetail = (record) => {
    setCurrentDetail(record.data);
    setDetailModalVisible(true);
  };

  // 关闭详情模态框
  const handleCloseDetailModal = () => {
    setDetailModalVisible(false);
    setCurrentDetail(null);
  };

  // 状态标签
  const getStatusTag = (status) => {
    switch (status) {
      case 'success':
        return <Tag color="green">成功</Tag>;
      case 'error':
        return <Tag color="red">失败</Tag>;
      case 'exists':
        return <Tag color="blue">已存在</Tag>;
      default:
        return <Tag color="gray">未知</Tag>;
    }
  };

  // 表格列定义
  const columns = [
    {
      title: 'URL',
      dataIndex: 'url',
      key: 'url',
      ellipsis: true,
      width: 400
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => getStatusTag(status)
    },
    {
      title: '当前阶段',
      dataIndex: 'currentStage',
      key: 'currentStage',
      ellipsis: true
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress) => progress !== undefined ? (
        <Progress percent={progress} size="small" />
      ) : null
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button 
          type="link" 
          disabled={!record.data}
          onClick={() => handleViewDetail(record)}
        >
          查看详情
        </Button>
      )
    }
  ];

  // 渲染详情内容
  const renderDetailContent = () => {
    if (!currentDetail) return null;

    return (
      <div style={{ maxHeight: 600, overflow: 'auto' }}>
        {Object.entries(currentDetail).map(([key, value]) => (
          <div key={key} style={{ marginBottom: 12 }}>
            <h4 style={{ marginBottom: 4, fontSize: '14px', fontWeight: 'bold', color: '#1890ff' }}>
              {key}
            </h4>
            <div style={{ 
              padding: 12, 
              border: '1px dashed #d9d9d9', 
              borderRadius: 8, 
              background: '#fafafa',
              fontSize: '13px'
            }}>
              {typeof value === 'object' ? (
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(value, null, 2)}
                </pre>
              ) : (
                <span>{value}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <h2 style={{ marginBottom: 24 }}>链接解析工具</h2>
      
      <Alert 
        message="使用说明" 
        description="在下方输入框中粘贴一个或多个URL链接（每行一个），系统会自动检查并处理这些链接。" 
        type="info" 
        style={{ marginBottom: 24 }} 
      />

      <Form form={form} layout="vertical" style={{ maxWidth: 800 }}>
        <Form.Item 
          label="URL链接" 
          rules={[{ required: true, message: '请输入URL链接' }]}
        >
          <TextArea 
            rows={6} 
            placeholder="请输入一个或多个URL链接，每行一个"
            value={urls}
            onChange={handleUrlChange}
          />
        </Form.Item>

        <Form.Item>
          <Checkbox 
            checked={useLLMSummary}
            onChange={handleLLMSummaryChange}
          >
            使用大模型摘要
          </Checkbox>
        </Form.Item>

        <Form.Item>
          <Space>
            <Button 
              type="primary" 
              onClick={handleSubmit}
              loading={processing}
            >
              开始处理
            </Button>
            <Button onClick={() => setUrls('')}>
              清空
            </Button>
          </Space>
        </Form.Item>
      </Form>

      {processing && (
        <div style={{ margin: '24px 0' }}>
          <Progress 
            percent={currentProgress} 
            status="active" 
            format={(percent) => `${percent}%`}
          />
          <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
            正在处理：{results.length}/{totalProgress}
          </div>
        </div>
      )}

      {results.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h3 style={{ marginBottom: 16 }}>处理结果</h3>
          <Table 
            dataSource={results} 
            columns={columns} 
            rowKey="url" 
            pagination={{ pageSize: 10 }}
          />
        </div>
      )}

      {/* 详情模态框 */}
      <Modal
        title="链接详情"
        open={detailModalVisible}
        onCancel={handleCloseDetailModal}
        footer={[
          <Button key="close" onClick={handleCloseDetailModal}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {renderDetailContent()}
      </Modal>
    </div>
  );
};

export default LinkParser;