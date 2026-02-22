import React, { useState, useEffect } from 'react';
import { Layout, DatePicker, Tabs, Card, Row, Col, Statistic, Progress, Pagination, Table, Tag, Divider, List, Button, Select, Input, Spin, message, Form, InputNumber, Space, Typography, Empty, Badge, Menu } from 'antd';
import ReactECharts from 'echarts-for-react';
import { StarOutlined, StarFilled, EyeOutlined, CheckCircleOutlined, CloseCircleOutlined, EditOutlined, SaveOutlined, CloseOutlined, ReadOutlined, ReadFilled, FileTextOutlined, MenuFoldOutlined, MenuUnfoldOutlined, HomeOutlined, AppstoreOutlined, FileSearchOutlined, ArrowUpOutlined, RobotOutlined } from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.locale('zh-cn');
dayjs.extend(relativeTime);

const { Header, Content, Sider } = Layout;
const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;
const { RangePicker } = DatePicker;

const API_BASE = 'http://localhost:8000';

const ARTICLE_FIELDS = [
  { key: '概要', label: '概要', type: 'text' },
  { key: 'socre', label: '评分', type: 'number' },
  { key: 'reason', label: '原因', type: 'text' },
  { key: 'tags', label: '标签', type: 'tags_comma' },
  { key: '书籍', label: '书籍', type: 'tags_hash' },
  { key: '事件', label: '事件', type: 'tags_hash' },
  { key: '产品服务', label: '产品服务', type: 'tags_hash' },
  { key: '人物', label: '人物', type: 'tags_hash' },
  { key: '地点', label: '地点', type: 'tags_hash' },
  { key: '概念实体', label: '概念实体', type: 'tags_hash' },
  { key: '组织公司', label: '组织公司', type: 'tags_hash' },
  { key: '生命之花', label: '生命之花', type: 'lines_semicolon' },
  { key: '相关问题', label: '相关问题', type: 'lines_semicolon' },
  { key: '问题库', label: '问题库', type: 'lines_semicolon' },
  { key: '原则库', label: '原则库', type: 'lines_period' },
  { key: '四精练', label: '四精练', type: 'lines_semicolon' },
  { key: '量化的结论', label: '量化的结论', type: 'lines_semicolon' },
  { key: '点子库', label: '点子库', type: 'text' },
  { key: '梳理点子想法', label: '梳理点子想法', type: 'text' },
  { key: '备注', label: '备注', type: 'text' }
];

const MonitorProgress = ({ activeTab, setActiveTab, selectedDate, setSelectedDate }) => {
  const [stats, setStats] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);
  const [scoreType, setScoreType] = useState('pre_value_score');
  const [monthlyData, setMonthlyData] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);

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
        textStyle: {
          color: '#fff',
          fontSize: 14
        },
        formatter: function (params) {
          return `<div style="padding: 8px;">
                    <div style="font-weight: bold; margin-bottom: 4px;">文章类型: ${heatmapData.yAxis[params.value[1]]}</div>
                    <div>评分: <span style="color: #1890ff; font-weight: bold;">${heatmapData.xAxis[params.value[0]]}</span></div>
                    <div>数量: <span style="color: #52c41a; font-weight: bold;">${params.value[2]}</span></div>
                  </div>`;
        }
      },
      grid: { 
        height: '70%', 
        top: '8%',
        left: '5%',
        right: '5%'
      },
      xAxis: {
        type: 'category',
        data: heatmapData.xAxis,
        name: '评分',
        nameLocation: 'middle',
        nameGap: 30,
        nameTextStyle: {
          fontSize: 14,
          fontWeight: 'bold'
        },
        axisLabel: {
          fontSize: 13,
          fontWeight: 'bold'
        },
        splitArea: { 
          show: true,
          areaStyle: {
            color: ['rgba(250,250,250,0.3)', 'rgba(240,240,240,0.3)']
          }
        }
      },
      yAxis: {
        type: 'category',
        data: heatmapData.yAxis,
        axisLine: {
          show: false
        },
        axisTick: {
          show: false
        },
        axisLabel: {
          fontSize: 13,
          fontWeight: 'bold',
          interval: 0,
          color: '#333'
        },
        splitArea: { 
          show: true,
          areaStyle: {
            color: ['rgba(250,250,250,0.3)', 'rgba(240,240,240,0.3)']
          }
        }
      },
      visualMap: {
        show: false,
        min: 0,
        max: Math.max(...heatmapData.data.map(d => d[2]), 1),
        inRange: {
          color: ['#f0f9ff', '#bae7ff', '#91d5ff', '#69c0ff', '#40a9ff', '#1890ff', '#096dd9', '#0050b3']
        }
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
          formatter: function (params) {
            return params.value[2] > 0 ? params.value[2] : '';
          }
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 15,
            shadowColor: 'rgba(0, 0, 0, 0.3)'
          }
        },
        itemStyle: {
          borderRadius: 4
        }
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
        render: (text) => (
          <span style={{ fontWeight: 500 }}>{text}</span>
        )
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
            <div style={{
              background: bgColor,
              color: textColor,
              padding: '8px 4px',
              borderRadius: '6px',
              fontWeight: value > 0 ? 600 : 400,
              fontSize: '13px'
            }}>
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
              <Card 
                hoverable
                style={{ 
                  borderRadius: 12, 
                  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                  border: 'none'
                }}
              >
                <Statistic 
                  title={<span style={{ color: '#8c8c8c', fontSize: '14px' }}>总账号数</span>}
                  value={stats.total_feeds} 
                  valueStyle={{ color: '#1890ff', fontWeight: 'bold', fontSize: '32px' }}
                  prefix={<ArrowUpOutlined />}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card 
                hoverable
                style={{ 
                  borderRadius: 12, 
                  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                  border: 'none'
                }}
              >
                <Statistic 
                  title={<span style={{ color: '#8c8c8c', fontSize: '14px' }}>总文章数</span>}
                  value={stats.total_articles} 
                  valueStyle={{ color: '#52c41a', fontWeight: 'bold', fontSize: '32px' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card 
                hoverable
                style={{ 
                  borderRadius: 12, 
                  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                  border: 'none'
                }}
              >
                <Statistic 
                  title={<span style={{ color: '#8c8c8c', fontSize: '14px' }}>今日更新账号</span>}
                  value={stats.today_feeds} 
                  valueStyle={{ color: '#722ed1', fontWeight: 'bold', fontSize: '32px' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Card 
                hoverable
                style={{ 
                  borderRadius: 12, 
                  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                  border: 'none'
                }}
              >
                <Statistic 
                  title={<span style={{ color: '#8c8c8c', fontSize: '14px' }}>今日新增文章</span>}
                  value={stats.today_articles} 
                  valueStyle={{ color: '#fa8c16', fontWeight: 'bold', fontSize: '32px' }}
                />
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
                style={{ 
                  borderRadius: 16, 
                  boxShadow: '0 4px 20px rgba(24,144,255,0.15)',
                  border: '1px solid #e6f7ff',
                  background: 'linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%)'
                }}
                title={
                  <span style={{ display: 'flex', alignItems: 'center' }}>
                    <Tag color="blue" style={{ marginRight: 8 }}>预加工</Tag>
                    <span style={{ fontSize: '14px' }}>pre_value_score ≥ 1</span>
                  </span>
                }
              >
                <div style={{ textAlign: 'center', padding: '16px 0' }}>
                  <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#1890ff', marginBottom: 8 }}>
                    {stats.today_preprocessed}
                  </div>
                  <div style={{ fontSize: '14px', color: '#8c8c8c', marginBottom: 16 }}>
                    / {stats.today_mongo_articles_count} 篇 (MongoDB)
                  </div>
                  <Progress 
                    percent={stats.today_preprocessed_rate} 
                    status="active"
                    strokeColor={{
                      '0%': '#91d5ff',
                      '100%': '#1890ff'
                    }}
                    strokeWidth={14}
                    format={(percent) => `${percent}%`}
                    showInfo={false}
                  />
                  <div style={{ marginTop: 12, fontSize: '16px', fontWeight: 600, color: '#1890ff' }}>
                    {stats.today_preprocessed_rate}%
                  </div>
                </div>
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card 
                style={{ 
                  borderRadius: 16, 
                  boxShadow: '0 4px 20px rgba(82,196,145,0.15)',
                  border: '1px solid #f6ffed',
                  background: 'linear-gradient(135deg, #f6ffed 0%, #fcfff5 100%)'
                }}
                title={
                  <span style={{ display: 'flex', alignItems: 'center' }}>
                    <Tag color="green" style={{ marginRight: 8 }}>全文获取</Tag>
                    <span style={{ fontSize: '14px' }}>full_content 非空</span>
                  </span>
                }
              >
                <div style={{ textAlign: 'center', padding: '16px 0' }}>
                  <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#52c41a', marginBottom: 8 }}>
                    {stats.today_full_content}
                  </div>
                  <div style={{ fontSize: '14px', color: '#8c8c8c', marginBottom: 16 }}>
                    / {stats.today_mongo_articles_count} 篇 (MongoDB)
                  </div>
                  <Progress 
                    percent={stats.today_full_content_rate} 
                    status="active"
                    strokeColor={{
                      '0%': '#95de64',
                      '100%': '#52c41a'
                    }}
                    strokeWidth={14}
                    format={(percent) => `${percent}%`}
                    showInfo={false}
                  />
                  <div style={{ marginTop: 12, fontSize: '16px', fontWeight: 600, color: '#52c41a' }}>
                    {stats.today_full_content_rate}%
                  </div>
                </div>
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card 
                style={{ 
                  borderRadius: 16, 
                  boxShadow: '0 4px 20px rgba(114,46,209,0.15)',
                  border: '1px solid #f9f0ff',
                  background: 'linear-gradient(135deg, #f9f0ff 0%, #fcf5ff 100%)'
                }}
                title={
                  <span style={{ display: 'flex', alignItems: 'center' }}>
                    <Tag color="purple" style={{ marginRight: 8 }}><RobotOutlined /> 大模型总结</Tag>
                    <span style={{ fontSize: '14px' }}>pre_value_score ≥ 3</span>
                  </span>
                }
              >
                <div style={{ textAlign: 'center', padding: '16px 0' }}>
                  <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#722ed1', marginBottom: 8 }}>
                    {stats.today_llm_summary}
                  </div>
                  <div style={{ fontSize: '14px', color: '#8c8c8c', marginBottom: 16 }}>
                    / {stats.high_score_articles} 篇 (pre_value_score ≥ 3)
                  </div>
                  <Progress 
                    percent={stats.today_llm_summary_rate} 
                    status="active"
                    strokeColor={{
                      '0%': '#d3adf7',
                      '100%': '#722ed1'
                    }}
                    strokeWidth={14}
                    format={(percent) => `${percent}%`}
                    showInfo={false}
                  />
                  <div style={{ marginTop: 12, fontSize: '16px', fontWeight: 600, color: '#722ed1' }}>
                    {stats.today_llm_summary_rate}%
                  </div>
                </div>
              </Card>
            </Col>
          </Row>

          <Divider orientation="left" style={{ fontSize: '16px', fontWeight: 600, color: '#262626' }}>
            文章评分分布热力图
          </Divider>

          <Card 
            style={{ 
              borderRadius: 16, 
              boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
              border: 'none'
            }}
            extra={
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ color: '#8c8c8c', fontSize: '14px' }}>评分类型:</span>
                <select 
                  value={scoreType} 
                  onChange={(e) => setScoreType(e.target.value)}
                  style={{ 
                    padding: '6px 12px', 
                    borderRadius: '8px',
                    border: '1px solid #d9d9d9',
                    fontSize: '14px',
                    background: '#fff',
                    cursor: 'pointer'
                  }}
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
          style={{ 
            borderRadius: 16, 
            boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
            border: 'none'
          }}
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 600, color: '#262626' }}>
          📊 数据监控
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ color: '#8c8c8c', fontSize: '14px' }}>选择日期:</span>
          <DatePicker
            value={selectedDate}
            onChange={(date) => setSelectedDate(date)}
            style={{ width: 180 }}
            size="large"
          />
        </div>
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab} size="large" type="card" tabBarStyle={{ marginBottom: '24px', fontSize: '15px' }} items={tabItems} />
    </div>
  );
};

const ArticleManagement = () => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(30);
  const [total, setTotal] = useState(0);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [editing, setEditing] = useState(false);
  const [form] = Form.useForm();
  const [allTags, setAllTags] = useState([]);
  const [dateRange, setDateRange] = useState([dayjs().startOf('day'), dayjs().endOf('day')]);
  const [filters, setFilters] = useState({
    scoreType: 'socre',
    scores: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    tags: undefined,
    isCollected: [true, false],
    isFollowed: [true, false],
    isDiscarded: [true, false],
    isRead: [true, false],
    sortBy: 'socre',
    sortOrder: 'desc'
  });

  useEffect(() => {
    fetchArticles();
    fetchTags();
  }, [currentPage, pageSize, filters, dateRange]);

  const fetchArticles = async () => {
    setLoading(true);
    try {
      const params = { page: currentPage, page_size: pageSize };
      if (filters.scoreType) params.score_type = filters.scoreType;
      if (filters.tags) params.tags = filters.tags;
      if (filters.isCollected && filters.isCollected.length > 0) params.is_collected = filters.isCollected;
      if (filters.isFollowed && filters.isFollowed.length > 0) params.is_followed = filters.isFollowed;
      if (filters.isDiscarded && filters.isDiscarded.length > 0) params.is_enabled = filters.isDiscarded.map(val => !val);
      if (filters.isRead && filters.isRead.length > 0) params.is_read = filters.isRead;
      if (filters.scores && filters.scores.length > 0) params.scores = filters.scores;
      if (filters.sortBy) params.sort_by = filters.sortBy;
      if (filters.sortOrder) params.sort_order = filters.sortOrder;
      
      if (dateRange[0]) params.start_date = dateRange[0].format('YYYY-MM-DD');
      if (dateRange[1]) params.end_date = dateRange[1].format('YYYY-MM-DD');

      const response = await axios.get(`${API_BASE}/api/articles`, { params });
      setArticles(response.data.data);
      setTotal(response.data.total);
    } catch (error) {
      message.error('获取文章列表失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTags = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/tags`);
      setAllTags(response.data.tags);
    } catch (error) {
      console.error('获取标签失败:', error);
    }
  };

  const fetchArticleDetail = async (articleId) => {
    try {
      const response = await axios.get(`${API_BASE}/api/articles/${articleId}`);
      setSelectedArticle(response.data);
      form.setFieldsValue(response.data);
      setEditing(false);
    } catch (error) {
      message.error('获取文章详情失败');
      console.error(error);
    }
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      await axios.put(`${API_BASE}/api/articles/${selectedArticle._id}`, values);
      message.success('保存成功');
      setEditing(false);
      fetchArticleDetail(selectedArticle._id);
      fetchArticles();
    } catch (error) {
      message.error('保存失败');
      console.error(error);
    }
  };

  const handleCancel = () => {
    setEditing(false);
    form.setFieldsValue(selectedArticle);
  };

  const handleToggleFlag = async (articleId, field, value) => {
    try {
      await axios.put(`${API_BASE}/api/articles/${articleId}`, { [field]: value });
      message.success('更新成功');
      fetchArticles();
      if (selectedArticle && selectedArticle._id === articleId) {
        fetchArticleDetail(articleId);
      }
    } catch (error) {
      message.error('更新失败');
      console.error(error);
    }
  };

  const parseTags = (value, separator) => {
    if (!value || typeof value !== 'string') return [];
    return value.split(separator).filter(t => t.trim()).map(t => t.trim());
  };

  const parseLines = (value, separator) => {
    if (!value || typeof value !== 'string') return [];
    return value.split(separator).filter(t => t.trim()).map(t => t.trim());
  };

  const renderFieldValue = (field, value) => {
    if (!value) return <Text type="secondary">暂无内容</Text>;

    switch (field.type) {
      case 'tags_comma':
        return (
          <Space wrap>
            {parseTags(value, ',').map((tag, idx) => (
              <Tag key={idx} color="blue">{tag}</Tag>
            ))}
          </Space>
        );
      case 'tags_hash':
        return (
          <Space wrap>
            {parseTags(value, '#').map((tag, idx) => (
              <Tag key={idx} color="purple">{tag}</Tag>
            ))}
          </Space>
        );
      case 'lines_semicolon':
        return (
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {parseLines(value, ';').map((line, idx) => (
              <li key={idx} style={{ marginBottom: 8 }}>{line}</li>
            ))}
          </ul>
        );
      case 'lines_period':
        return (
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {parseLines(value, '。').map((line, idx) => (
              <li key={idx} style={{ marginBottom: 8 }}>{line}。</li>
            ))}
          </ul>
        );
      case 'number':
        return <Text strong style={{ fontSize: 24 }}>{value}</Text>;
      default:
        return <Text style={{ whiteSpace: 'pre-wrap' }}>{value}</Text>;
    }
  };

  const renderArticleItem = (article) => {
    const preValueScore = article.pre_value_score || 0;
    const score = article.socre || 0;
    const publishTime = article.publish_time ? dayjs.unix(article.publish_time) : null;
    const isDiscarded = article.is_enabled === false;
    const isRead = article.is_read === true;

    return (
      <div
        key={article._id}
        style={{ 
          padding: '16px 20px', 
          cursor: 'pointer',
          backgroundColor: selectedArticle?._id === article._id ? '#e6f7ff' : '#fff',
          borderRadius: 8,
          marginBottom: 12,
          boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          border: selectedArticle?._id === article._id ? '1px solid #91d5ff' : '1px solid #f0f0f0',
          opacity: isDiscarded ? 0.6 : 1,
          transition: 'all 0.2s'
        }}
        onClick={() => fetchArticleDetail(article._id)}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ flex: 1, marginRight: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <a 
                href={article.url} 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ 
                  fontSize: 15, 
                  fontWeight: 500, 
                  color: selectedArticle?._id === article._id ? '#1890ff' : '#262626',
                  lineHeight: 1.4
                }}
                onClick={(e) => e.stopPropagation()}
              >
                {article.title}
              </a>
              <Badge status={isRead ? 'success' : 'default'} />
            </div>
            <div style={{ 
              color: '#666', 
              marginBottom: 10, 
              display: '-webkit-box', 
              WebkitLineClamp: 2, 
              WebkitBoxOrient: 'vertical', 
              overflow: 'hidden',
              lineHeight: 1.5,
              fontSize: 13
            }}>
              {article.description}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
              <Space size={4}>
                <Tag color="blue" style={{ fontSize: 11, padding: '0 8px', lineHeight: '20px', height: 22, borderRadius: 4 }}>
                  pre: {preValueScore}
                </Tag>
                <Tag color="green" style={{ fontSize: 11, padding: '0 8px', lineHeight: '20px', height: 22, borderRadius: 4 }}>
                  s: {score}
                </Tag>
              </Space>
              <Space size={4} wrap>
                {(typeof article.article_type === 'string' ? article.article_type.split(',').filter(t => t.trim()) : Array.isArray(article.article_type) ? article.article_type : []).slice(0, 4).map((tag, idx) => (
                  <Tag key={idx} style={{ fontSize: 11, padding: '0 8px', lineHeight: '20px', height: 22, borderRadius: 4 }}>
                    {tag.trim()}
                  </Tag>
                ))}
                {(typeof article.article_type === 'string' ? article.article_type.split(',').filter(t => t.trim()).length : Array.isArray(article.article_type) ? article.article_type.length : 0) > 4 && (
                  <Tag style={{ fontSize: 11, padding: '0 8px', lineHeight: '20px', height: 22, borderRadius: 4 }}>
                    +{(typeof article.article_type === 'string' ? article.article_type.split(',').filter(t => t.trim()).length : Array.isArray(article.article_type) ? article.article_type.length : 0) - 4}
                  </Tag>
                )}
              </Space>
              <span style={{ fontSize: 12, color: '#999' }}>
                {article.source || '未知'}
              </span>
              <span style={{ fontSize: 12, color: '#999' }}>
                {publishTime ? publishTime.fromNow() : ''}
              </span>
              <Button
                type="text"
                icon={isRead ? <ReadFilled style={{ color: '#52c41a', fontSize: 14 }} /> : <ReadOutlined style={{ fontSize: 14 }} />}
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleToggleFlag(article._id, 'is_read', !isRead);
                }}
              />
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <Button
              type="text"
              icon={article.is_collected ? <StarFilled style={{ color: '#faad14', fontSize: 16 }} /> : <StarOutlined style={{ fontSize: 16 }} />}
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                handleToggleFlag(article._id, 'is_collected', !article.is_collected);
              }}
            />
            <Button
              type="text"
              icon={article.is_followed ? <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 16 }} /> : <EyeOutlined style={{ fontSize: 16 }} />}
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                handleToggleFlag(article._id, 'is_followed', !article.is_followed);
              }}
            />
            <Button
              type="text"
              danger={isDiscarded}
              icon={isDiscarded ? <CloseCircleOutlined style={{ fontSize: 16 }} /> : <CheckCircleOutlined style={{ fontSize: 16 }} />}
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                handleToggleFlag(article._id, 'is_enabled', isDiscarded);
              }}
            />
          </div>
        </div>
      </div>
    );
  };

  const renderArticleDetail = () => {
    if (!selectedArticle) {
      return (
        <div style={{ 
          height: '100%', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: '#999'
        }}>
          <Empty description="点击左侧文章查看详情" />
        </div>
      );
    }

    const isDiscarded = selectedArticle.is_enabled === false;

    return (
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <div style={{ 
          padding: '20px 24px', 
          borderBottom: '1px solid #f0f0f0',
          background: '#fafafa',
          flexShrink: 0
        }}>
          <Title level={4} style={{ marginBottom: 12, lineHeight: 1.4 }}>
            <a href={selectedArticle.url} target="_blank" rel="noopener noreferrer" style={{ color: '#1890ff' }}>
              {selectedArticle.title}
            </a>
          </Title>
          <Space wrap style={{ marginBottom: 16 }}>
            <Tag color="blue">pre_value_score: {selectedArticle.pre_value_score || 0}</Tag>
            <Tag color="green">score: {selectedArticle.socre || 0}</Tag>
            {(typeof selectedArticle.article_type === 'string' ? selectedArticle.article_type.split(',').filter(t => t.trim()) : Array.isArray(selectedArticle.article_type) ? selectedArticle.article_type : []).map((tag, idx) => (
              <Tag key={idx}>{tag.trim()}</Tag>
            ))}
          </Space>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space>
              <Button
                icon={selectedArticle.is_collected ? <StarFilled /> : <StarOutlined />}
                type={selectedArticle.is_collected ? 'primary' : 'default'}
                onClick={() => handleToggleFlag(selectedArticle._id, 'is_collected', !selectedArticle.is_collected)}
              >
                {selectedArticle.is_collected ? '已收藏' : '收藏'}
              </Button>
              <Button
                icon={selectedArticle.is_followed ? <CheckCircleOutlined /> : <EyeOutlined />}
                type={selectedArticle.is_followed ? 'primary' : 'default'}
                onClick={() => handleToggleFlag(selectedArticle._id, 'is_followed', !selectedArticle.is_followed)}
              >
                {selectedArticle.is_followed ? '已关注' : '关注'}
              </Button>
              <Button
                danger={isDiscarded}
                icon={isDiscarded ? <CloseCircleOutlined /> : <CheckCircleOutlined />}
                type={isDiscarded ? 'primary' : 'default'}
                onClick={() => handleToggleFlag(selectedArticle._id, 'is_enabled', isDiscarded)}
              >
                {isDiscarded ? '已弃用' : '弃用'}
              </Button>
            </Space>
            {editing ? (
              <Space>
                <Button type="primary" icon={<SaveOutlined />} onClick={handleSave}>
                  保存
                </Button>
                <Button icon={<CloseOutlined />} onClick={handleCancel}>
                  取消
                </Button>
              </Space>
            ) : (
              <Button type="primary" icon={<EditOutlined />} onClick={() => setEditing(true)}>
                编辑
              </Button>
            )}
          </div>
        </div>

        <div style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: '24px',
          background: '#fff'
        }}>
          {editing ? (
            <Form
              form={form}
              layout="vertical"
            >
              {ARTICLE_FIELDS.map((field) => (
                <Form.Item key={field.key} label={field.label} style={{ marginBottom: 16 }}>
                  {field.type === 'number' ? (
                    <Form.Item name={field.key} noStyle>
                      <InputNumber min={0} max={10} style={{ width: '100%' }} />
                    </Form.Item>
                  ) : (
                    <Form.Item name={field.key} noStyle>
                      <TextArea rows={field.type === 'text' ? 4 : 6} />
                    </Form.Item>
                  )}
                </Form.Item>
              ))}
            </Form>
          ) : (
            <div>
              {ARTICLE_FIELDS.map((field) => (
                <div key={field.key} style={{ marginBottom: 24 }}>
                  <Text strong style={{ 
                    display: 'block', 
                    marginBottom: 10, 
                    fontSize: 13,
                    color: '#595959',
                    textTransform: 'uppercase',
                    letterSpacing: 0.5
                  }}>
                    {field.label}
                  </Text>
                  <div style={{ 
                    padding: '14px 16px', 
                    background: '#fafafa', 
                    borderRadius: 6,
                    fontSize: 14,
                    lineHeight: 1.6,
                    border: '1px solid #f0f0f0'
                  }}>
                    {renderFieldValue(field, selectedArticle[field.key])}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div style={{ 
      height: 'calc(100vh - 140px)',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <div style={{ 
        background: '#fff', 
        padding: '16px 24px', 
        borderBottom: '1px solid #f0f0f0',
        boxShadow: '0 1px 4px rgba(0,0,0,0.05)',
        zIndex: 10
      }}>
        <Space size="small" wrap>
          <RangePicker
            value={dateRange}
            onChange={(dates) => setDateRange(dates)}
            size="small"
            style={{ width: 240 }}
          />
          <Select
            placeholder="评分类型"
            style={{ width: 120 }}
            value={filters.scoreType}
            onChange={(value) => setFilters({ ...filters, scoreType: value })}
            size="small"
          >
            <Option value="pre_value_score">pre_value</Option>
            <Option value="socre">score</Option>
          </Select>
          <Select
            mode="multiple"
            placeholder="评分"
            style={{ width: 180 }}
            value={filters.scores}
            onChange={(value) => setFilters({ ...filters, scores: value })}
            size="small"
          >
            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((score) => (
              <Option key={score} value={score}>{score}</Option>
            ))}
          </Select>
          <Select
            mode="tags"
            style={{ width: 180 }}
            placeholder="标签"
            value={filters.tags ? filters.tags.split(',') : []}
            onChange={(value) => setFilters({ ...filters, tags: value.join(',') })}
            size="small"
          >
            {allTags.map((tag) => (
              <Option key={tag.name} value={tag.name}>{tag.name} ({tag.count})</Option>
            ))}
          </Select>
          <Select
            mode="multiple"
            placeholder="收藏"
            style={{ width: 90 }}
            value={filters.isCollected}
            onChange={(value) => setFilters({ ...filters, isCollected: value })}
            size="small"
          >
            <Option value={false}>未收藏</Option>
            <Option value={true}>已收藏</Option>
          </Select>
          <Select
            mode="multiple"
            placeholder="关注"
            style={{ width: 90 }}
            value={filters.isFollowed}
            onChange={(value) => setFilters({ ...filters, isFollowed: value })}
            size="small"
          >
            <Option value={false}>未关注</Option>
            <Option value={true}>已关注</Option>
          </Select>
          <Select
            mode="multiple"
            placeholder="弃用"
            style={{ width: 90 }}
            value={filters.isDiscarded}
            onChange={(value) => setFilters({ ...filters, isDiscarded: value })}
            size="small"
          >
            <Option value={false}>未弃用</Option>
            <Option value={true}>已弃用</Option>
          </Select>
          <Select
            mode="multiple"
            placeholder="已读"
            style={{ width: 90 }}
            value={filters.isRead}
            onChange={(value) => setFilters({ ...filters, isRead: value })}
            size="small"
          >
            <Option value={false}>未读</Option>
            <Option value={true}>已读</Option>
          </Select>
          <Select
            placeholder="排序"
            style={{ width: 100 }}
            value={filters.sortBy}
            onChange={(value) => setFilters({ ...filters, sortBy: value })}
            size="small"
          >
            <Option value="publish_time">时间</Option>
            <Option value="pre_value_score">pre_value</Option>
            <Option value="socre">score</Option>
          </Select>
          <Button type="primary" size="small" onClick={fetchArticles}>
            刷新
          </Button>
        </Space>
      </div>
      
      <div style={{ 
        flex: 1,
        display: 'flex'
      }}>
        <div style={{ 
          flex: 1,
          overflowY: 'auto',
          background: '#f5f7fa',
          padding: '16px 20px'
        }}>
          <Spin spinning={loading} tip="加载中...">
            {articles.length > 0 ? (
              <div>
                {articles.map(renderArticleItem)}
              </div>
            ) : (
              <Empty 
                description="暂无文章" 
                style={{ padding: '80px 0' }}
              />
            )}
          </Spin>
          
          <div style={{ 
            padding: '16px 0',
            background: '#fafafa',
            borderRadius: 8,
            marginTop: 12,
            flexShrink: 0
          }}>
            <div style={{ textAlign: 'center' }}>
              <Space>
                <Button 
                  disabled={currentPage <= 1}
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                >
                  上一页
                </Button>
                <span style={{ color: '#666' }}>
                  第 {currentPage} / {Math.ceil(total / pageSize)} 页，共 {total} 条
                </span>
                <Button 
                  disabled={currentPage >= Math.ceil(total / pageSize)}
                  onClick={() => setCurrentPage(currentPage + 1)}
                >
                  下一页
                </Button>
                <Select
                  value={pageSize}
                  onChange={(value) => {
                    setPageSize(value);
                    setCurrentPage(1);
                  }}
                  style={{ width: 100 }}
                  size="small"
                >
                  <Option value={10}>10条/页</Option>
                  <Option value={20}>20条/页</Option>
                  <Option value={30}>30条/页</Option>
                  <Option value={50}>50条/页</Option>
                  <Option value={100}>100条/页</Option>
                </Select>
              </Space>
            </div>
          </div>
        </div>
        
        {selectedArticle && (
          <div 
            style={{ 
              width: '58%', 
              background: '#fff',
              overflow: 'hidden',
              boxShadow: '-2px 0 10px rgba(0,0,0,0.05)'
            }}
          >
            {renderArticleDetail()}
          </div>
        )}
      </div>
    </div>
  );
};

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [activeMenu, setActiveMenu] = useState('monitor');
  const [monitorActiveTab, setMonitorActiveTab] = useState('1');
  const [selectedDate, setSelectedDate] = useState(dayjs().subtract(1, 'day'));

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f7fa' }}>
      <Layout.Sider
        collapsible
        collapsed={collapsed}
        onCollapse={(value) => setCollapsed(value)}
        width={240}
        collapsedWidth={80}
        style={{
          background: '#fff',
          boxShadow: '0 0 10px rgba(0,0,0,0.05)',
          zIndex: 100
        }}
      >
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between', 
          padding: '0 24px',
          borderBottom: '1px solid #f0f0f0'
        }}>
          <h1 style={{ 
            color: '#262626', 
            margin: 0, 
            fontSize: collapsed ? '16px' : '18px', 
            fontWeight: 600,
            letterSpacing: 0.5
          }}>
            📊 数据管理
          </h1>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
        </div>
        <Menu
          mode="inline"
          selectedKeys={[activeMenu]}
          onSelect={(info) => setActiveMenu(info.key)}
          style={{ height: 'calc(100vh - 64px)', borderRight: 0 }}
          items={[
            {
              key: 'monitor',
              icon: <HomeOutlined />,
              label: '数据监控'
            },
            {
              key: 'article',
              icon: <FileSearchOutlined />,
              label: '文章管理'
            }
          ]}
        />
      </Layout.Sider>
      <Layout style={{ flex: 1 }}>
        <Header style={{ 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
          padding: '0 32px', 
          display: 'flex', 
          alignItems: 'center',
          boxShadow: '0 4px 12px rgba(102,126,234,0.3)'
        }}>
          <h1 style={{ 
            color: '#fff', 
            margin: 0, 
            fontSize: '22px',
            fontWeight: 600,
            letterSpacing: '0.5px'
          }}>
            {activeMenu === 'monitor' ? '📊 数据监控系统' : '📝 文章管理系统'}
          </h1>
        </Header>
        <Layout.Content style={{ 
          flex: 1, 
          overflow: 'auto'
        }}>
          {activeMenu === 'article' ? (
            <ArticleManagement />
          ) : (
            <MonitorProgress 
              activeTab={monitorActiveTab} 
              setActiveTab={setMonitorActiveTab}
              selectedDate={selectedDate}
              setSelectedDate={setSelectedDate}
            />
          )}
        </Layout.Content>
      </Layout>
    </Layout>
  );
}

export default App;
