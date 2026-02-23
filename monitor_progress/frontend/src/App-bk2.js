import React, { useState, useEffect, useRef, useCallback } from 'react';
import MonitorProgressNew from './features/monitor/MonitorProgress';
import ArticleManagementNew from './features/article/ArticleManagement';
import { Layout, DatePicker, Tabs, Card, Row, Col, Statistic, Progress, Pagination, Table, Tag, Divider, List, Button, Select, Input, Spin, message, Form, InputNumber, Space, Typography, Menu, Segmented, Slider } from 'antd';
import ReactECharts from 'echarts-for-react';
import ReactMarkdown from 'react-markdown';
import { StarOutlined, StarFilled, CheckCircleOutlined, CloseCircleOutlined, EditOutlined, SaveOutlined, CloseOutlined, ReadOutlined, ReadFilled, FileTextOutlined, MenuFoldOutlined, MenuUnfoldOutlined, FileSearchOutlined, RobotOutlined, FilterOutlined, SettingOutlined, CalendarOutlined, BarChartOutlined } from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import relativeTime from 'dayjs/plugin/relativeTime';

dayjs.locale('zh-cn');
dayjs.extend(relativeTime);

const { Header } = Layout;
const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

// 使用相对路径，这样在Docker环境中也能正确连接到后端服务
const API_BASE = '';

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
  { key: '问题库', label: '问题库', type: 'lines_dash' },
  { key: '原则库', label: '原则库', type: 'lines_period' },
  { key: '四精练', label: '四精练', type: 'lines_semicolon' },
  { key: '量化的结论', label: '量化的结论', type: 'lines_semicolon' },
  { key: '点子库', label: '点子库', type: 'markdown' },
  { key: '梳理点子想法', label: '梳理点子想法', type: 'text' },
  { key: '备注', label: '备注', type: 'text' }
];

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
                  // prefix={<ArrowUpOutlined />}
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
      <Tabs activeKey={activeTab} onChange={setActiveTab} size="large" type="card" tabBarStyle={{ marginBottom: '24px', fontSize: '15px' }} items={tabItems} />
    </div>
  );
};

const ArticleManagement = ({ filters, dateRange }) => {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10); // 每页10篇
  const [total, setTotal] = useState(0);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [editing, setEditing] = useState(false);
  const [form] = Form.useForm();
  const [collapsedGroups, setCollapsedGroups] = useState({
    basicInfo: true, // 包含socre和tags
    tagsGroup: true  // 包含书籍、事件、产品服务、人物、地点、概念实体、组织公司
  });

  const queryKey = JSON.stringify({
    filters,
    start_date: dateRange && dateRange[0] ? dateRange[0].format('YYYY-MM-DD') : null,
    end_date: dateRange && dateRange[1] ? dateRange[1].format('YYYY-MM-DD') : null,
    pageSize
  });

  const lastQueryKeyRef = useRef(queryKey);

  const fetchArticlesInternal = useCallback(async () => {
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
      if (dateRange && dateRange[0]) params.start_date = dateRange[0].format('YYYY-MM-DD');
      if (dateRange && dateRange[1]) params.end_date = dateRange[1].format('YYYY-MM-DD');

      const response = await axios.get(`${API_BASE}/api/articles`, { params });
      const nextArticles = Array.isArray(response.data?.articles)
        ? response.data.articles
        : (Array.isArray(response.data?.data) ? response.data.data : []);
      setArticles(nextArticles);
      setTotal(response.data.total);
    } catch (error) {
      console.error('获取文章失败:', error);
      message.error('获取文章失败');
    } finally {
      setLoading(false);
    }
  }, [currentPage, dateRange, filters, pageSize]);

  useEffect(() => {
    if (lastQueryKeyRef.current !== queryKey && currentPage !== 1) {
      lastQueryKeyRef.current = queryKey;
      setCurrentPage(1);
      return;
    }

    lastQueryKeyRef.current = queryKey;
    fetchArticlesInternal();
  }, [currentPage, fetchArticlesInternal, queryKey]);

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
      fetchArticlesInternal();
    } catch (error) {
      message.error('保存失败');
      console.error(error);
    }
  };

  const handleToggleFlag = (articleId, field, value) => {
    // 先更新本地状态，让UI立即变化
    setArticles(prevArticles => {
      return prevArticles.map(article => {
        if (article._id === articleId) {
          return {
            ...article,
            [field]: value
          };
        }
        return article;
      });
    });
    
    // 如果当前选中的文章就是被修改的文章，也更新selectedArticle
    if (selectedArticle && selectedArticle._id === articleId) {
      setSelectedArticle(prev => ({
        ...prev,
        [field]: value
      }));
    }
    
    // 异步发送请求到服务器
    axios.put(`${API_BASE}/api/articles/${articleId}`, { [field]: value })
      .then(() => {
        message.success('更新成功');
        // 这里可以选择是否重新获取文章列表，因为本地状态已经更新了
        // fetchArticlesInternal();
        // if (selectedArticle && selectedArticle._id === articleId) {
        //   fetchArticleDetail(articleId);
        // }
      })
      .catch(error => {
        message.error('更新失败');
        console.error(error);
        // 如果请求失败，回滚本地状态
        fetchArticlesInternal();
        if (selectedArticle && selectedArticle._id === articleId) {
          fetchArticleDetail(articleId);
        }
      });
  };

  const parseTags = (value, separator) => {
    if (!value || typeof value !== 'string') return [];
    return value.split(separator).filter(t => t.trim()).map(t => t.trim());
  };

  const parseLines = (value, separators) => {
    if (!value || typeof value !== 'string') return [];
    
    let result = [value];
    separators.forEach(separator => {
      result = result.flatMap(item => item.split(separator));
    });
    
    return result.filter(item => item.trim()).map(item => item.trim());
  };

  const renderFieldValue = (field, value) => {
    if (!value) return <Text type="secondary">暂无内容</Text>;

    switch (field.key) {
      case 'tags':
        // 直接显示原字段内容，不做切分
        return <Text>{value}</Text>;
      case '书籍':
      case '事件':
      case '产品服务':
      case '人物':
      case '地点':
      case '概念实体':
      case '组织公司':
        return (
          <Space wrap>
            {parseTags(value, '#').map((tag, idx) => (
              <Tag key={idx} color="green">{tag}</Tag>
            ))}
          </Space>
        );
      case '四精练':
        return (
          <List
            size="small"
            dataSource={parseLines(value, ['；', ';', '\n'])}
            renderItem={(item) => <List.Item style={{ padding: '4px 0' }}>• {item}</List.Item>}
          />
        );
      case '问题库':
        return (
          <List
            size="small"
            dataSource={parseLines(value, ['- ', '\n'])}
            renderItem={(item) => <List.Item style={{ padding: '4px 0' }}>• {item}</List.Item>}
          />
        );
      case '原则库':
        return (
          <List
            size="small"
            dataSource={parseLines(value, ['。', '\n'])}
            renderItem={(item) => <List.Item style={{ padding: '4px 0' }}>• {item}</List.Item>}
          />
        );
      case '相关问题':
        return (
          <List
            size="small"
            dataSource={parseLines(value, ['；', ';', '\n'])}
            renderItem={(item) => <List.Item style={{ padding: '4px 0' }}>• {item}</List.Item>}
          />
        );
      case '点子库':
        // 将##替换为####，并保持markdown格式
        const formattedValue = value.replace(/##/g, '####');
        return (
          <div style={{ whiteSpace: 'pre-wrap' }}>
            {formattedValue}
          </div>
        );
      case '生命之花':
        return (
          <List
            size="small"
            dataSource={parseLines(value, ['；', ';', '\n'])}
            renderItem={(item) => <List.Item style={{ padding: '4px 0' }}>• {item}</List.Item>}
          />
        );
      default:
        return <Text>{value}</Text>;
    }
  };

  const renderArticleDetail = () => {
    if (!selectedArticle) return null;

    return (
      <div style={{ height: '100%', overflow: 'auto', padding: '24px' }}>
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>

          </div>
          
          <div style={{ marginBottom: 16 }}>
            {selectedArticle.url ? (
              <a href={selectedArticle.url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none' }}>
                <Text strong style={{ fontSize: '18px', color: '#1890ff' }}>{selectedArticle.title}</Text>
              </a>
            ) : (
              <Text strong style={{ fontSize: '18px' }}>{selectedArticle.title}</Text>
            )}
          </div>
          
          <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
            <Space>
              <Text type="secondary">公众号:</Text>
              <Text>{selectedArticle.mp_name || '未知公众号'}</Text>
            </Space>
            <Space>
              <Text type="secondary">发布时间:</Text>
              <Text>
                {selectedArticle.publish_time 
                  ? typeof selectedArticle.publish_time === 'number' 
                    ? dayjs.unix(selectedArticle.publish_time).format('YYYY-MM-DD HH:mm') 
                    : dayjs(selectedArticle.publish_time).format('YYYY-MM-DD HH:mm') 
                  : '未知时间'
                }
              </Text>
            </Space>
            <Space>
              <Text type="secondary">评分:</Text>
              <Text style={{ color: '#1890ff', fontWeight: 'bold' }}>{selectedArticle.socre}</Text>
            </Space>
            <Space>
              <Text type="secondary">pre_value:</Text>
              <Text style={{ color: '#52c41a', fontWeight: 'bold' }}>{selectedArticle.pre_value_score}</Text>
            </Space>
          </div>
          
          <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
            <Button
              size="small"
              icon={selectedArticle.is_collected ? <StarFilled /> : <StarOutlined />}
              type={selectedArticle.is_collected ? 'primary' : 'default'}
              onClick={() => handleToggleFlag(selectedArticle._id, 'is_collected', !selectedArticle.is_collected)}
            >
              {selectedArticle.is_collected ? '已收藏' : '收藏'}
            </Button>
            <Button
              size="small"
              icon={selectedArticle.is_followed ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
              type={selectedArticle.is_followed ? 'primary' : 'default'}
              onClick={() => handleToggleFlag(selectedArticle._id, 'is_followed', !selectedArticle.is_followed)}
            >
              {selectedArticle.is_followed ? '已关注' : '关注'}
            </Button>
            <Button
              size="small"
              icon={selectedArticle.is_discarded ? <CloseCircleOutlined /> : <CheckCircleOutlined />}
              type={selectedArticle.is_discarded ? 'danger' : 'default'}
              onClick={() => handleToggleFlag(selectedArticle._id, 'is_discarded', !selectedArticle.is_discarded)}
            >
              {selectedArticle.is_discarded ? '已弃用' : '弃用'}
            </Button>
            <Button
              size="small"
              icon={selectedArticle.is_read ? <ReadFilled /> : <ReadOutlined />}
              type={selectedArticle.is_read ? 'primary' : 'default'}
              onClick={() => handleToggleFlag(selectedArticle._id, 'is_read', !selectedArticle.is_read)}
            >
              {selectedArticle.is_read ? '已读' : '未读'}
            </Button>
            <div style={{ display: 'flex', gap: 8 }}>
              <Button
                size="small"
                style={{background: '#168ae9ff',color: '#f8f7f7ff', fontWeight: 'bold' }} 
                icon={editing ? <CloseOutlined /> : <EditOutlined />}
                onClick={() => setEditing(!editing)}
              >
                {editing ? '取消编辑' : '编辑'}
              </Button>
              {editing && (
                // 填充淡蓝色
                <Button size="small" style={{background: '#032c7dff',  color: '#f1ededff', fontWeight: 'bold' }} icon={<SaveOutlined />} onClick={handleSave}>
                  保存
                </Button>
              )}
            </div>
          </div>
        </div>

        <Divider />

        <Form form={form} layout="vertical">
          {/* 基本信息组：包含socre和tags */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 'bold' }}>基本信息</h4>
              <button 
                style={{ fontSize: '12px', color: '#1890ff', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                onClick={(e) => {
                  e.preventDefault();
                  setCollapsedGroups(prev => ({
                    ...prev,
                    basicInfo: !prev.basicInfo
                  }));
                }}
              >
                {collapsedGroups.basicInfo ? '展开' : '折叠'}
              </button>
            </div>
            
            {!collapsedGroups.basicInfo && (
              <div style={{ marginBottom: 16, padding: 12, border: '1px dashed #d9d9d9', borderRadius: 8, background: '#fafafa' }}>
                {ARTICLE_FIELDS.filter(field => ['socre', 'tags'].includes(field.key)).map(field => {
                  return (
                    <Form.Item
                      key={field.key}
                      label={
                        <span style={{ fontWeight: 500 }}>
                          <span style={{ 
                            display: 'inline-block', 
                            width: '8px', 
                            height: '8px', 
                            borderRadius: '50%', 
                            backgroundColor: '#1890ff', 
                            marginRight: '6px',
                            verticalAlign: 'middle'
                          }} />
                          {field.label}
                          {field.key === 'socre' && (
                            <span style={{ marginLeft: 8, color: '#1890ff', fontSize: '12px' }}>当前评分</span>
                          )}
                        </span>
                      }
                      name={field.key}
                    >
                      {editing ? (
                        <TextArea rows={field.key === '概要' ? 4 : 3} />
                      ) : (
                        <div style={{ padding: '4px 8px', background: '#f5f5f5', borderRadius: '4px' }}>
                          {renderFieldValue(field, selectedArticle[field.key])}
                        </div>
                      )}
                    </Form.Item>
                  );
                })}
              </div>
            )}
          </div>
          
          {/* 标签组：包含书籍、事件、产品服务、人物、地点、概念实体、组织公司 */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 'bold' }}>标签信息</h4>
              <button 
                style={{ fontSize: '12px', color: '#1890ff', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                onClick={(e) => {
                  e.preventDefault();
                  setCollapsedGroups(prev => ({
                    ...prev,
                    tagsGroup: !prev.tagsGroup
                  }));
                }}
              >
                {collapsedGroups.tagsGroup ? '展开' : '折叠'}
              </button>
            </div>
            
            {!collapsedGroups.tagsGroup && (
              <div style={{ marginBottom: 16, padding: 12, border: '1px dashed #d9d9d9', borderRadius: 8, background: '#fafafa' }}>
                {ARTICLE_FIELDS.filter(field => ['书籍', '事件', '产品服务', '人物', '地点', '概念实体', '组织公司'].includes(field.key)).map(field => {
                  return (
                    <Form.Item
                      key={field.key}
                      label={
                        <span style={{ fontWeight: 500 }}>
                          <span style={{ 
                            display: 'inline-block', 
                            width: '8px', 
                            height: '8px', 
                            borderRadius: '50%', 
                            backgroundColor: '#1890ff', 
                            marginRight: '6px',
                            verticalAlign: 'middle'
                          }} />
                          {field.label}
                        </span>
                      }
                      name={field.key}
                    >
                      {editing ? (
                        <TextArea rows={field.key === '概要' ? 4 : 3} />
                      ) : (
                        <div style={{ padding: '4px 8px', background: '#f5f5f5', borderRadius: '4px' }}>
                          {renderFieldValue(field, selectedArticle[field.key])}
                        </div>
                      )}
                    </Form.Item>
                  );
                })}
              </div>
            )}
          </div>
          
          {/* 其他字段：不折叠 */}
          {ARTICLE_FIELDS.filter(field => !['socre', 'tags', '书籍', '事件', '产品服务', '人物', '地点', '概念实体', '组织公司'].includes(field.key)).map(field => {
            return (
              <Form.Item
                key={field.key}
                label={
                  <span style={{ fontWeight: 500 }}>
                    <span style={{ 
                      display: 'inline-block', 
                      width: '8px', 
                      height: '8px', 
                      borderRadius: '50%', 
                      backgroundColor: '#1890ff', 
                      marginRight: '6px',
                      verticalAlign: 'middle'
                    }} />
                    {field.label}
                  </span>
                }
                name={field.key}
              >
                {editing ? (
                  <TextArea rows={field.key === '概要' ? 4 : 3} />
                ) : (
                  <div style={{ padding: '4px 8px', background: '#f5f5f5', borderRadius: '4px' }}>
                    {renderFieldValue(field, selectedArticle[field.key])}
                  </div>
                )}
              </Form.Item>
            );
          })}
        </Form>
      </div>
    );
  };

  return (
    <div style={{ height: 'calc(100vh - 64px)', display: 'flex', overflow: 'hidden' }}>
      {/* 左侧文章列表 */}
      <div style={{ 
        width: '42%', 
        background: '#fff',
        borderRight: '1px solid #f0f0f0',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* 文章列表头部 */}
        <div style={{ 
          padding: '16px 24px',
          borderBottom: '1px solid #f0f0f0',
          background: '#fafafa',
          flexShrink: 0
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text strong>文章列表</Text>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              共 {total} 篇
            </Text>
          </div>
        </div>
        
        {/* 文章列表内容 */}
        <div style={{ flex: 1, overflow: 'auto', padding: 12 }}>
          <Spin spinning={loading}>
            <List
              dataSource={articles}
              renderItem={(article) => (
                <Card
                  hoverable
                  size="small"
                  bodyStyle={{ padding: 8 }}
                  style={{ 
                    marginBottom: 8,
                    borderRadius: 6,
                    border: selectedArticle && selectedArticle._id === article._id ? '2px solid #1890ff' : '1px solid #f0f0f0',
                    background: selectedArticle && selectedArticle._id === article._id ? '#f0f9ff' : '#fff'
                  }}
                  onClick={() => fetchArticleDetail(article._id)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1, marginRight: 12 }}>
                      <div style={{ fontWeight: 500, marginBottom: 4, lineHeight: '1.4' }}>
                        {article.url ? (
                          <a href={article.url} target="_blank" rel="noopener noreferrer" style={{ color: '#1890ff', textDecoration: 'none' }}>
                            {article.title}
                          </a>
                        ) : (
                          article.title
                        )}
                      </div>

                      {typeof article.description === 'string' && article.description.trim() && (
                        <div
                          style={{
                            fontSize: 12,
                            color: '#595959',
                            marginBottom: 6,
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden'
                          }}
                        >
                          {article.description}
                        </div>
                      )}
                      {(() => {
                        let tagsList = [];
                        if (Array.isArray(article.tags)) {
                          tagsList = article.tags.filter(Boolean).map(t => String(t).trim()).filter(Boolean);
                        } else if (typeof article.tags === 'string') {
                          tagsList = article.tags.split(',').map(t => t.trim()).filter(Boolean);
                        } else if (Array.isArray(article.article_type)) {
                          tagsList = article.article_type.filter(Boolean);
                        } else if (typeof article.article_type === 'string' && article.article_type.trim()) {
                          tagsList = [article.article_type.trim()];
                        }
                        if (tagsList.length === 0) return null;
                        const display = tagsList.slice(0, 3);
                        const rest = tagsList.length - display.length;
                        return (
                          <div style={{ marginBottom: 4 }}>
                            <Space wrap size={4}>
                              {display.map((tag, idx) => (
                                <Tag key={idx} style={{ fontSize: '10px' }}>{tag}</Tag>
                              ))}
                              {rest > 0 && (
                                <Tag style={{ fontSize: '10px' }}>+{rest}</Tag>
                              )}
                            </Space>
                          </div>
                        );
                      })()}
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                        <Space size={8}>
                          <span style={{ fontSize: '11px', color: '#1890ff' }}>评分: {article.socre}</span>
                          <span style={{ fontSize: '11px', color: '#52c41a' }}>pre: {article.pre_value_score}</span>
                        </Space>
                        <span style={{ fontSize: '11px', color: '#8c8c8c' }}>
                          {article.publish_time 
                            ? typeof article.publish_time === 'number' 
                              ? dayjs.unix(article.publish_time).fromNow() 
                              : dayjs(article.publish_time).fromNow() 
                            : '未知时间'
                          }
                        </span>
                        <span style={{ fontSize: '11px', color: '#8c8c8c' }}>{article.mp_name}</span>
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <StarFilled style={{ color: article.is_collected ? '#faad14' : '#d9d9d9', fontSize: '14px' }} />
                      <ReadFilled style={{ color: article.is_read ? '#52c41a' : '#d9d9d9', fontSize: '14px' }} />
                      <CloseCircleOutlined style={{ color: article.is_discarded ? '#ff4d4f' : '#d9d9d9', fontSize: '14px' }} />
                    </div>
                  </div>
                </Card>
              )}
            />
          </Spin>
        </div>
        
        {/* 固定底部翻页条 */}
        <div style={{ 
          padding: '16px 24px',
          borderTop: '1px solid #f0f0f0',
          background: '#fff',
          flexShrink: 0
        }}>
          <Pagination
            current={currentPage}
            total={total}
            pageSize={pageSize}
            onChange={(page) => setCurrentPage(page)}
            showSizeChanger={false}
            showQuickJumper
            showTotal={(total) => `共 ${total} 条`}
            size="small"
            style={{ textAlign: 'center' }}
          />
        </div>
      </div>
      
      {/* 右侧详情区域 */}
      {selectedArticle && (
        <div 
          style={{ 
            width: '58%', 
            background: '#fff',
            overflow: 'hidden',
            boxShadow: '-2px 0 10px rgba(0,0,0,0.05)',
            borderLeft: '1px solid #f0f0f0'
          }}
        >
          {renderArticleDetail()}
        </div>
      )}
    </div>
  );
};

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [activeMenu, setActiveMenu] = useState('monitor');
  const [monitorScoreType, setMonitorScoreType] = useState('pre_value_score');
  const [selectedDate, setSelectedDate] = useState(dayjs());
  const [articleDateRange, setArticleDateRange] = useState([dayjs().startOf('day'), dayjs().endOf('day')]);
  const [articleFilters, setArticleFilters] = useState({
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
  const [allTags, setAllTags] = useState([]);

  useEffect(() => {
    fetchTags();
  }, [articleDateRange]);

  // 临时筛选与日期，仅在点击“确认筛选”后生效到正式筛选
  const [articleTempFilters, setArticleTempFilters] = useState(articleFilters);
  const [articleTempDateRange, setArticleTempDateRange] = useState(articleDateRange);

  useEffect(() => {
    setArticleTempFilters(articleFilters);
  }, [articleFilters]);

  useEffect(() => {
    setArticleTempDateRange(articleDateRange);
  }, [articleDateRange]);

  const fetchTags = async () => {
    try {
      const params = {};
      if (articleDateRange && articleDateRange[0]) {
        params.start_date = articleDateRange[0].format('YYYY-MM-DD');
      }
      if (articleDateRange && articleDateRange[1]) {
        params.end_date = articleDateRange[1].format('YYYY-MM-DD');
      }
      const response = await axios.get(`${API_BASE}/api/tags`, { params });
      setAllTags(response.data.tags);
    } catch (error) {
      console.error('获取标签失败:', error);
    }
  };

  const handleTempFilterChange = (key, value) => {
    setArticleTempFilters(prev => ({ ...prev, [key]: value }));
  };

  const getFilterSummary = () => {
    const parts = [];
    
    if (articleFilters.scores && articleFilters.scores.length > 0 && articleFilters.scores.length < 11) {
      parts.push(`评分: ${articleFilters.scores.join(',')}`);
    }
    
    if (articleFilters.isCollected && articleFilters.isCollected.length === 1) {
      parts.push(articleFilters.isCollected[0] ? '已收藏' : '未收藏');
    }
    
    if (articleFilters.isFollowed && articleFilters.isFollowed.length === 1) {
      parts.push(articleFilters.isFollowed[0] ? '已关注' : '未关注');
    }
    
    if (articleFilters.isDiscarded && articleFilters.isDiscarded.length === 1) {
      parts.push(articleFilters.isDiscarded[0] ? '已弃用' : '未弃用');
    }
    
    if (articleFilters.isRead && articleFilters.isRead.length === 1) {
      parts.push(articleFilters.isRead[0] ? '已读' : '未读');
    }
    
    if (articleFilters.tags) {
      const tagList = articleFilters.tags.split(',');
      if (tagList.length > 0) {
        parts.push(`标签: ${tagList.length > 2 ? `${tagList.slice(0, 2).join(',')}...` : tagList.join(',')}`);
      }
    }
    
    return parts;
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f5f7fa' }}>
      <Layout.Sider
        collapsible
        collapsed={collapsed}
        onCollapse={(value) => setCollapsed(value)}
        width={260}
        collapsedWidth={64}
        style={{
          background: '#fff',
          boxShadow: '2px 0 8px rgba(0,0,0,0.06)',
          zIndex: 100,
          overflow: 'hidden'
        }}
        trigger={null}
      >
        <div style={{ 
          height: 64, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: collapsed ? 'center' : 'space-between', 
          padding: collapsed ? '0' : '0 20px',
          borderBottom: '1px solid #f0f0f0',
          background: 'linear-gradient(135deg, #3c5be8ff 0%, #2428e1ff 100%)'
        }}>
          {!collapsed && (
            <h1 style={{ 
              color: '#fff', 
              margin: 0, 
              fontSize: '16px', 
              fontWeight: 600,
              letterSpacing: 0.5
            }}>
              📊 数据管理平台
            </h1>
          )}
          {collapsed && <span style={{ color: '#fff', fontSize: '20px' }}>📊</span>}
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined style={{ color: '#fff', fontSize: '18px' }} /> : <MenuFoldOutlined style={{ color: '#fff', fontSize: '18px' }} />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ 
              color: '#fff',
              marginLeft: collapsed ? 0 : 'auto'
            }}
          />
        </div>
        
        <div style={{ overflowY: 'auto', height: 'calc(100vh - 64px)' }}>
          <Menu
            mode="inline"
            selectedKeys={[activeMenu]}
            onSelect={(info) => setActiveMenu(info.key)}
            style={{ height: 'auto', borderRight: 0, paddingTop: 8, fontSize: 15, fontWeight: 600 }}
            items={[
              {
                key: 'monitor',
                icon: <BarChartOutlined style={{ fontSize: 16 }} />,
                label: <span style={{ fontSize: 15, fontWeight: 600 }}>数据监控</span>
              },
              {
                key: 'article',
                icon: <FileSearchOutlined style={{ fontSize: 16 }} />,
                label: <span style={{ fontSize: 15, fontWeight: 600 }}>文章管理</span>
              }
            ]}
          />

          {!collapsed && (
            <div style={{ padding: '16px 16px 0' }}>
              <Divider style={{ margin: '8px 0' }} />
              
              {activeMenu === 'monitor' && (
                <div>
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                      <CalendarOutlined style={{ color: '#8c8c8c' }} />
                      <Text type="secondary" style={{ fontSize: '13px' }}>选择日期</Text>
                    </div>
                    <DatePicker
                      value={selectedDate}
                      onChange={(date) => setSelectedDate(date)}
                      style={{ width: '100%' }}
                      size="middle"
                    />
                  </div>
                  
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                      <SettingOutlined style={{ color: '#8c8c8c' }} />
                      <Text type="secondary" style={{ fontSize: '13px' }}>评分类型</Text>
                    </div>
                    <Select
                      value={monitorScoreType}
                      onChange={(value) => setMonitorScoreType(value)}
                      style={{ width: '100%' }}
                      size="middle"
                    >
                      <Option value="pre_value_score">pre_value_score</Option>
                      <Option value="score">score</Option>
                    </Select>
                  </div>
                </div>
              )}

              {activeMenu === 'article' && (
                <div>
                  <div
                    style={{
                      padding: 14,
                      background: 'linear-gradient(180deg,#ffffff 0%,#fafcff 100%)',
                      border: '1px solid #f0f3f8',
                      borderRadius: 12,
                      boxShadow: '0 6px 18px rgba(0,0,0,0.06)',
                      marginBottom: 16
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                      <FilterOutlined style={{ color: '#8c8c8c' }} />
                      <Text type="secondary" style={{ fontSize: 13, fontWeight: 600 }}>筛选条件</Text>
                    </div>

                    <div style={{ marginBottom: 14 }}>
                      <Text style={{ fontSize: 12, color: '#8c8c8c', display: 'block', marginBottom: 6 }}>日期范围</Text>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        <DatePicker
                          allowClear
                          value={articleTempDateRange?.[0] ?? null}
                          onChange={(date) => {
                            setArticleTempDateRange((prev) => {
                              const next = [date, prev?.[1] ?? null];
                              if (!next[0] && !next[1]) return null;
                              return next;
                            });
                          }}
                          size="middle"
                          style={{ width: '100%' }}
                          placeholder="开始日期"
                        />
                        <DatePicker
                          allowClear
                          value={articleTempDateRange?.[1] ?? null}
                          onChange={(date) => {
                            setArticleTempDateRange((prev) => {
                              const next = [prev?.[0] ?? null, date];
                              if (!next[0] && !next[1]) return null;
                              return next;
                            });
                          }}
                          size="middle"
                          style={{ width: '100%' }}
                          placeholder="结束日期"
                        />
                      </div>
                    </div>

                    <div style={{ marginBottom: 14 }}>
                      <Text style={{ fontSize: 12, color: '#8c8c8c', display: 'block', marginBottom: 6 }}>评分类型</Text>
                      <Segmented
                        block
                        value={articleTempFilters.scoreType}
                        onChange={(val) => handleTempFilterChange('scoreType', val)}
                        options={[
                          { label: 'pre_value', value: 'pre_value_score' },
                          { label: 'score', value: 'socre' }
                        ]}
                      />
                    </div>

                    <div style={{ marginBottom: 14 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                        <Text style={{ fontSize: 12, color: '#8c8c8c' }}>评分范围</Text>
                        <Text style={{ fontSize: 12, color: '#262626', fontWeight: 600 }}>
                          {Array.isArray(articleTempFilters.scores) && articleTempFilters.scores.length > 0
                            ? `${Math.min(...articleTempFilters.scores)} - ${Math.max(...articleTempFilters.scores)}`
                            : '0 - 10'}
                        </Text>
                      </div>
                      <Slider
                        range
                        min={0}
                        max={10}
                        value={[
                          Array.isArray(articleTempFilters.scores) && articleTempFilters.scores.length > 0 ? Math.min(...articleTempFilters.scores) : 0,
                          Array.isArray(articleTempFilters.scores) && articleTempFilters.scores.length > 0 ? Math.max(...articleTempFilters.scores) : 10
                        ]}
                        onChange={(val) => {
                          const [minV, maxV] = val;
                          const list = [];
                          for (let i = minV; i <= maxV; i += 1) list.push(i);
                          handleTempFilterChange('scores', list);
                        }}
                      />
                    </div>

                    <div style={{ marginBottom: 14 }}>
                      <Text style={{ fontSize: 12, color: '#8c8c8c', display: 'block', marginBottom: 6 }}>标签</Text>
                      <Select
                        mode="tags"
                        style={{ width: '100%' }}
                        placeholder="选择或输入标签"
                        value={articleTempFilters.tags ? articleTempFilters.tags.split(',') : []}
                        onChange={(value) => handleTempFilterChange('tags', value.join(','))}
                        size="middle"
                        maxTagCount={3}
                      >
                        {allTags.map((tag) => (
                          <Option key={tag.name} value={tag.name}>{tag.name} ({tag.count})</Option>
                        ))}
                      </Select>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 14 }}>
                      <div>
                        <Text style={{ fontSize: 12, color: '#8c8c8c', display: 'block', marginBottom: 6 }}>收藏</Text>
                        <Segmented
                          block
                          value={
                            articleTempFilters.isCollected?.length === 1
                              ? (articleTempFilters.isCollected[0] ? 'yes' : 'no')
                              : 'all'
                          }
                          onChange={(val) => {
                            if (val === 'all') handleTempFilterChange('isCollected', [true, false]);
                            else handleTempFilterChange('isCollected', [val === 'yes']);
                          }}
                          options={[
                            { label: '全部', value: 'all' },
                            { label: '是', value: 'yes' },
                            { label: '否', value: 'no' }
                          ]}
                        />
                      </div>
                      <div>
                        <Text style={{ fontSize: 12, color: '#8c8c8c', display: 'block', marginBottom: 6 }}>关注</Text>
                        <Segmented
                          block
                          value={
                            articleTempFilters.isFollowed?.length === 1
                              ? (articleTempFilters.isFollowed[0] ? 'yes' : 'no')
                              : 'all'
                          }
                          onChange={(val) => {
                            if (val === 'all') handleTempFilterChange('isFollowed', [true, false]);
                            else handleTempFilterChange('isFollowed', [val === 'yes']);
                          }}
                          options={[
                            { label: '全部', value: 'all' },
                            { label: '是', value: 'yes' },
                            { label: '否', value: 'no' }
                          ]}
                        />
                      </div>
                      <div>
                        <Text style={{ fontSize: 12, color: '#8c8c8c', display: 'block', marginBottom: 6 }}>弃用</Text>
                        <Segmented
                          block
                          value={
                            articleTempFilters.isDiscarded?.length === 1
                              ? (articleTempFilters.isDiscarded[0] ? 'yes' : 'no')
                              : 'all'
                          }
                          onChange={(val) => {
                            if (val === 'all') handleTempFilterChange('isDiscarded', [true, false]);
                            else handleTempFilterChange('isDiscarded', [val === 'yes']);
                          }}
                          options={[
                            { label: '全部', value: 'all' },
                            { label: '是', value: 'yes' },
                            { label: '否', value: 'no' }
                          ]}
                        />
                      </div>
                      <div>
                        <Text style={{ fontSize: 12, color: '#8c8c8c', display: 'block', marginBottom: 6 }}>已读</Text>
                        <Segmented
                          block
                          value={
                            articleTempFilters.isRead?.length === 1
                              ? (articleTempFilters.isRead[0] ? 'yes' : 'no')
                              : 'all'
                          }
                          onChange={(val) => {
                            if (val === 'all') handleTempFilterChange('isRead', [true, false]);
                            else handleTempFilterChange('isRead', [val === 'yes']);
                          }}
                          options={[
                            { label: '全部', value: 'all' },
                            { label: '是', value: 'yes' },
                            { label: '否', value: 'no' }
                          ]}
                        />
                      </div>
                    </div>

                    <div style={{ marginBottom: 6 }}>
                      <Text style={{ fontSize: 12, color: '#8c8c8c', display: 'block', marginBottom: 6 }}>排序</Text>
                      <Segmented
                        block
                        value={articleTempFilters.sortBy}
                        onChange={(val) => handleTempFilterChange('sortBy', val)}
                        options={[
                          { label: '时间', value: 'publish_time' },
                          { label: 'pre_value', value: 'pre_value_score' },
                          { label: 'score', value: 'socre' }
                        ]}
                      />
                    </div>

                    {/* 确认和重置按钮 */}
                    <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
                      <Button 
                        block 
                        onClick={() => {
                          setArticleTempFilters({
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
                          setArticleTempDateRange([dayjs().startOf('day'), dayjs().endOf('day')]);
                        }}
                      >
                        重置筛选
                      </Button>
                      <Button 
                        type="primary" 
                        block 
                        style={{ background: '#1a78c4ff', borderColor: '#1a6cc4ff' }}
                        onClick={() => {
                          setArticleFilters(articleTempFilters);
                          setArticleDateRange(articleTempDateRange);
                          message.success('筛选条件已应用');
                        }}
                      >
                        确认筛选
                      </Button>
                    </div>
                  </div>

                  {getFilterSummary().length > 0 && (
                    <div style={{
                      padding: 12,
                      background: '#f6ffed',
                      borderRadius: 10,
                      border: '1px solid #d9f7be',
                      marginBottom: 16
                    }}>
                      <Text style={{ fontSize: 12, color: '#0d6b9eff', fontWeight: 600, display: 'block', marginBottom: 6 }}>
                        已应用筛选
                      </Text>
                      <Space wrap size={6}>
                        {getFilterSummary().map((item, idx) => (
                          <Tag key={idx} color="green" style={{ fontSize: 11, margin: 0 }}>
                            {item}
                          </Tag>
                        ))}
                      </Space>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </Layout.Sider>
      
      <Layout style={{ flex: 1, overflow: 'hidden' }}>
        <Header style={{ 
          background: '#fff', 
          padding: '0 24px', 
          display: 'flex', 
          alignItems: 'center',
          boxShadow: '0 1px 4px rgba(0,0,0,0.05)',
          borderBottom: '1px solid #f0f0f0',
          height: 64,
          flexShrink: 0
        }}>
          {activeMenu === 'monitor' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <h2 style={{ 
                margin: 0, 
                fontSize: '18px',
                fontWeight: 600,
                color: '#262626'
              }}>
                📊 数据监控
              </h2>
            </div>
          )}
        </Header>
        
        <Layout.Content style={{ 
          flex: 1, 
          overflow: 'hidden',
          background: '#f5f7fa'
        }}>
          {activeMenu === 'article' ? (
            <ArticleManagementNew 
              filters={articleFilters}
              dateRange={articleDateRange}
            />
          ) : (
            <MonitorProgressNew 
              selectedDate={selectedDate}
              setSelectedDate={setSelectedDate}
              scoreType={monitorScoreType}
              setScoreType={setMonitorScoreType}
            />
          )}
        </Layout.Content>
      </Layout>
    </Layout>
  );
}

export default App;
