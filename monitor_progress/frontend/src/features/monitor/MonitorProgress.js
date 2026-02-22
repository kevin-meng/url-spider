import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress, Pagination, Table, Tag, Divider, Tabs } from 'antd';
import { FileTextOutlined, CheckCircleOutlined, RobotOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import axios from 'axios';
import dayjs from 'dayjs';

const API_BASE = 'http://localhost:8000';

const MonitorProgress = ({ selectedDate, setSelectedDate, scoreType, setScoreType }) => {
  const [stats, setStats] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);
  const [monthlyData, setMonthlyData] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [activeTab, setActiveTab] = useState('1');

  useEffect(() => {
    fetchStats();
    fetchHeatmap();
    fetchMonthlyStats();
  }, [selectedDate, scoreType, currentPage]);

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/stats`, {
        params: { date: selectedDate.format('YYYY-MM-DD') }
      });
      setStats(response.data);
    } catch (error) {
      console.error('获取统计数据失败:', error);
    }
  };

  const fetchHeatmap = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/heatmap`, {
        params: { 
          date: selectedDate.format('YYYY-MM-DD'),
          score_type: scoreType
        }
      });
      setHeatmapData(response.data);
    } catch (error) {
      console.error('获取热力图数据失败:', error);
    }
  };

  const fetchMonthlyStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/monthly-stats`, {
        params: { page: currentPage, page_size: 30 }
      });
      setMonthlyData(response.data);
    } catch (error) {
      console.error('获取月度统计数据失败:', error);
    }
  };

  const getHeatmapOption = () => {
    if (!heatmapData) return {};
    return {
      tooltip: {
        position: 'top',
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        textStyle: { color: '#fff', fontSize: 14 },
        formatter: function (params) {
          return `<div style="padding: 8px;">
                    <div style="font-weight: bold; margin-bottom: 4px;">文章类型: ${heatmapData.yAxis[params.value[1]]}</div>
                    <div>评分: <span style="color: #1890ff; font-weight: bold;">${heatmapData.xAxis[params.value[0]]}</span></div>
                    <div>数量: <span style="color: #52c41a; font-weight: bold;">${params.value[2]}</span></div>
                  </div>`;
        }
      },
      grid: { height: '70%', top: '8%', left: '5%', right: '5%' },
      xAxis: {
        type: 'category',
        data: heatmapData.xAxis,
        name: '评分',
        nameLocation: 'middle',
        nameGap: 30,
        nameTextStyle: { fontSize: 14, fontWeight: 'bold' },
        axisLabel: { fontSize: 13, fontWeight: 'bold' },
        splitArea: { show: true, areaStyle: { color: ['rgba(250,250,250,0.3)', 'rgba(240,240,240,0.3)'] } }
      },
      yAxis: {
        type: 'category',
        data: heatmapData.yAxis,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { fontSize: 13, fontWeight: 'bold', interval: 0, color: '#333' },
        splitArea: { show: true, areaStyle: { color: ['rgba(250,250,250,0.3)', 'rgba(240,240,240,0.3)'] } }
      },
      visualMap: {
        show: false,
        min: 0,
        max: Math.max(...heatmapData.data.map(d => d[2]), 1),
        inRange: { color: ['#f0f9ff', '#bae7ff', '#91d5ff', '#69c0ff', '#40a9ff', '#1890ff', '#096dd9', '#0050b3'] }
      },
      series: [{
        name: '文章数量',
        type: 'heatmap',
        data: heatmapData.data,
        label: {
          show: true,
          fontSize: 12,
          fontWeight: 'bold',
          color: '#333',
          formatter: function (params) { return params.value[2] > 0 ? params.value[2] : ''; }
        },
        emphasis: { itemStyle: { shadowBlur: 15, shadowColor: 'rgba(0, 0, 0, 0.3)' } },
        itemStyle: { borderRadius: 4 }
      }]
    };
  };

  const getMonthlyTableColumns = () => {
    if (!monthlyData) return [];
    const columns = [
      {
        title: '序号',
        key: 'index',
        fixed: 'left',
        width: 70,
        align: 'center',
        render: (_, __, index) => (
          <span style={{ fontWeight: 'bold', color: '#8c8c8c' }}>
            {index + 1 + (currentPage - 1) * monthlyData.page_size}
          </span>
        )
      },
      { 
        title: '公众号名称', 
        dataIndex: 'mp_name', 
        key: 'mp_name', 
        fixed: 'left', 
        width: 220,
        render: (text) => (<span style={{ fontWeight: 500 }}>{text}</span>)
      }
    ];
    monthlyData.months.forEach(month => {
      columns.push({
        title: month,
        dataIndex: month,
        key: month,
        width: 85,
        align: 'center',
        render: (value) => {
          let bgColor = '#fafafa';
          let textColor = '#666';
          if (value > 0) {
            const intensity = Math.min(value / 15, 0.85);
            bgColor = `rgba(24, 144, 255, ${intensity * 0.2 + 0.1})`;
            textColor = value > 5 ? '#0050b3' : '#1890ff';
          }
          return (
            <div style={{ background: bgColor, color: textColor, padding: '8px 4px', borderRadius: '6px', fontWeight: value > 0 ? 600 : 400, fontSize: '13px' }}>
              {value > 0 ? value : '-'}
            </div>
          );
        }
      });
    });
    return columns;
  };

  const tabItems = [
    {
      key: '1',
      label: (
        <span>
          <FileTextOutlined style={{ marginRight: 8 }} />
          采集信息概览
        </span>
      ),
      children: stats && (
        <div>
          <Row gutter={[24, 24]} style={{ marginBottom: 32 }}>
            <Col xs={24} sm={12} md={6}>
              <Card hoverable style={{ borderRadius: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)', border: 'none' }}>
                <Statistic title={<span style={{ color: '#8c8c8c', fontSize: '14px' }}>总账号数</span>} value={stats.total_feeds} valueStyle={{ color: '#1890ff', fontWeight: 'bold', fontSize: '32px' }} />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card hoverable style={{ borderRadius: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)', border: 'none' }}>
                <Statistic title={<span style={{ color: '#8c8c8c', fontSize: '14px' }}>总文章数</span>} value={stats.total_articles} valueStyle={{ color: '#52c41a', fontWeight: 'bold', fontSize: '32px' }} />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card hoverable style={{ borderRadius: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)', border: 'none' }}>
                <Statistic title={<span style={{ color: '#8c8c8c', fontSize: '14px' }}>今日更新账号</span>} value={stats.today_feeds} valueStyle={{ color: '#722ed1', fontWeight: 'bold', fontSize: '32px' }} />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card hoverable style={{ borderRadius: 12, boxShadow: '0 4px 12px rgba(0,0,0,0.08)', border: 'none' }}>
                <Statistic title={<span style={{ color: '#8c8c8c', fontSize: '14px' }}>今日新增文章</span>} value={stats.today_articles} valueStyle={{ color: '#fa8c16', fontWeight: 'bold', fontSize: '32px' }} />
              </Card>
            </Col>
          </Row>

          <Divider orientation="left" style={{ fontSize: '16px', fontWeight: 600, color: '#262626' }}>
            <CheckCircleOutlined style={{ marginRight: 8 }} />
            加工进度
          </Divider>

          <Row gutter={[24, 24]} style={{ marginBottom: 32 }}>
            <Col xs={24} md={8}>
              <Card 
                style={{ borderRadius: 16, boxShadow: '0 4px 20px rgba(24,144,255,0.15)', border: '1px solid #e6f7ff', background: 'linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%)' }}
                title={
                  <span style={{ display: 'flex', alignItems: 'center' }}>
                    <Tag color="blue" style={{ marginRight: 8 }}>预加工</Tag>
                    <span style={{ fontSize: '14px' }}>pre_value_score ≥ 1</span>
                  </span>
                }
              >
                <div style={{ textAlign: 'center', padding: '16px 0' }}>
                  <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#1890ff', marginBottom: 8 }}>{stats.today_preprocessed}</div>
                  <div style={{ fontSize: '14px', color: '#8c8c8c', marginBottom: 16 }}>/ {stats.today_mongo_articles_count} 篇 (MongoDB)</div>
                  <Progress 
                    percent={stats.today_preprocessed_rate} 
                    status="active"
                    strokeColor={{ '0%': '#91d5ff', '100%': '#1890ff' }}
                    strokeWidth={14}
                    format={(percent) => `${percent}%`}
                    showInfo={false}
                  />
                  <div style={{ marginTop: 12, fontSize: '16px', fontWeight: 600, color: '#1890ff' }}>{stats.today_preprocessed_rate}%</div>
                </div>
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card 
                style={{ borderRadius: 16, boxShadow: '0 4px 20px rgba(82,196,145,0.15)', border: '1px solid #f6ffed', background: 'linear-gradient(135deg, #f6ffed 0%, #fcfff5 100%)' }}
                title={
                  <span style={{ display: 'flex', alignItems: 'center' }}>
                    <Tag color="green" style={{ marginRight: 8 }}>全文获取</Tag>
                    <span style={{ fontSize: '14px' }}>full_content 非空</span>
                  </span>
                }
              >
                <div style={{ textAlign: 'center', padding: '16px 0' }}>
                  <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#52c41a', marginBottom: 8 }}>{stats.today_full_content}</div>
                  <div style={{ fontSize: '14px', color: '#8c8c8c', marginBottom: 16 }}>/ {stats.today_mongo_articles_count} 篇 (MongoDB)</div>
                  <Progress 
                    percent={stats.today_full_content_rate} 
                    status="active"
                    strokeColor={{ '0%': '#95de64', '100%': '#52c41a' }}
                    strokeWidth={14}
                    format={(percent) => `${percent}%`}
                    showInfo={false}
                  />
                  <div style={{ marginTop: 12, fontSize: '16px', fontWeight: 600, color: '#52c41a' }}>{stats.today_full_content_rate}%</div>
                </div>
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card 
                style={{ borderRadius: 16, boxShadow: '0 4px 20px rgba(114,46,209,0.15)', border: '1px solid #f9f0ff', background: 'linear-gradient(135deg, #f9f0ff 0%, #fcf5ff 100%)' }}
                title={
                  <span style={{ display: 'flex', alignItems: 'center' }}>
                    <Tag color="purple" style={{ marginRight: 8 }}><RobotOutlined /> 大模型总结</Tag>
                    <span style={{ fontSize: '14px' }}>pre_value_score ≥ 3</span>
                  </span>
                }
              >
                <div style={{ textAlign: 'center', padding: '16px 0' }}>
                  <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#722ed1', marginBottom: 8 }}>{stats.today_llm_summary}</div>
                  <div style={{ fontSize: '14px', color: '#8c8c8c', marginBottom: 16 }}>/ {stats.high_score_articles} 篇 (pre_value_score ≥ 3)</div>
                  <Progress 
                    percent={stats.today_llm_summary_rate} 
                    status="active"
                    strokeColor={{ '0%': '#d3adf7', '100%': '#722ed1' }}
                    strokeWidth={14}
                    format={(percent) => `${percent}%`}
                    showInfo={false}
                  />
                  <div style={{ marginTop: 12, fontSize: '16px', fontWeight: 600, color: '#722ed1' }}>{stats.today_llm_summary_rate}%</div>
                </div>
              </Card>
            </Col>
          </Row>

          <Divider orientation="left" style={{ fontSize: '16px', fontWeight: 600, color: '#262626' }}>
            文章评分分布热力图
          </Divider>

          <Card style={{ borderRadius: 16, boxShadow: '0 4px 20px rgba(0,0,0,0.08)', border: 'none' }}
            extra={
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ color: '#8c8c8c', fontSize: '14px' }}>评分类型:</span>
                <select 
                  value={scoreType} 
                  onChange={(e) => setScoreType(e.target.value)}
                  style={{ padding: '6px 12px', borderRadius: '8px', border: '1px solid #d9d9d9', fontSize: '14px', background: '#fff', cursor: 'pointer' }}
                >
                  <option value="pre_value_score">pre_value_score</option>
                  <option value="score">score</option>
                </select>
              </div>
            }
          >
            {heatmapData && <ReactECharts option={getHeatmapOption()} style={{ height: '1500px' }} />}
          </Card>
        </div>
      )
    },
    {
      key: '2',
      label: (
        <span>
          <CheckCircleOutlined style={{ marginRight: 8 }} />
          数据采集预检
        </span>
      ),
      children: (
        <Card 
          title="账号文章发布时间统计（近24个月）"
          style={{ borderRadius: 16, boxShadow: '0 4px 20px rgba(0,0,0,0.08)', border: 'none' }}
        >
          {monthlyData && (
            <>
              <Table
                columns={getMonthlyTableColumns()}
                dataSource={monthlyData.data}
                rowKey="mp_id"
                pagination={false}
                scroll={{ x: monthlyData.months.length * 85 + 310 }}
                size="middle"
                style={{ marginTop: 16 }}
              />
              <div style={{ marginTop: 32, textAlign: 'center' }}>
                <Pagination
                  current={currentPage}
                  total={monthlyData.total}
                  pageSize={monthlyData.page_size}
                  onChange={(page) => setCurrentPage(page)}
                  showSizeChanger={false}
                  showQuickJumper
                  showTotal={(total) => `共 ${total} 个账号`}
                  size="large"
                />
              </div>
            </>
          )}
        </Card>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        size="large"
        type="card"
        tabBarStyle={{ marginBottom: '24px', fontSize: '15px' }}
        items={tabItems}
      />
    </div>
  );
};

export default MonitorProgress;
