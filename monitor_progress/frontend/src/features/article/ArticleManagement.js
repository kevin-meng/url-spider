import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Form, List, Card, Tag, Space, Typography, Button, Spin, Pagination, Input, InputNumber, message, Divider } from 'antd';
import { StarOutlined, StarFilled, CheckCircleOutlined, CloseCircleOutlined, ReadOutlined, ReadFilled, EditOutlined, SaveOutlined, CloseOutlined } from '@ant-design/icons';
import axios from 'axios';
import dayjs from 'dayjs';

const { Text } = Typography;
const { TextArea } = Input;
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
  { key: '问题库', label: '问题库', type: 'lines_dash' },
  { key: '原则库', label: '原则库', type: 'lines_period' },
  { key: '四精练', label: '四精练', type: 'lines_semicolon' },
  { key: '量化的结论', label: '量化的结论', type: 'lines_semicolon' },
  { key: '点子库', label: '点子库', type: 'markdown' },
  { key: '梳理点子想法', label: '梳理点子想法', type: 'text' },
  { key: '备注', label: '备注', type: 'text' }
];

function ArticleManagement({ filters, dateRange }) {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
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
      console.error('错误详情:', error.response);
      message.error(`获取文章失败: ${error.message}`);
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
            {selectedArticle.link ? (
              <a href={selectedArticle.link} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none' }}>
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
                        <TextArea rows={3} />
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
          
          {/* 其他字段 */}
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
      <div style={{ 
        width: '42%', 
        background: '#fff',
        borderRight: '1px solid #f0f0f0',
        display: 'flex',
        flexDirection: 'column'
      }}>
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
        <div style={{ flex: 1, overflow: 'auto', padding: 12 }}>
          <Spin spinning={loading}>
            <List
              dataSource={articles}
              renderItem={(article) => (
                <Card
                  hoverable
                  size="small"
                  bodyStyle={{ padding: 12 }}
                  style={{ 
                    marginBottom: 10,
                    borderRadius: 8,
                    border: selectedArticle && selectedArticle._id === article._id ? '2px solid #1890ff' : '1px solid #f0f0f0',
                    background: selectedArticle && selectedArticle._id === article._id ? '#f0f9ff' : '#fff'
                  }}
                  onClick={() => fetchArticleDetail(article._id)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1, marginRight: 12 }}>
                      <div style={{ fontWeight: 500, marginBottom: 4, lineHeight: '1.4' }}>
                        {article.url ? (
                          <a href={article.url} target="_blank" rel="noopener noreferrer" style={{ textDecoration: 'none', color: '#1890ff' }}>
                            {article.title}
                          </a>
                        ) : (
                          article.title
                        )}
                      </div>
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 4 }}>
                        <span style={{ fontSize: '11px', color: '#8c8c8c' }}>{article.mp_name || '未知公众号'}</span>
                        <span style={{ fontSize: '11px', color: '#8c8c8c' }}>
                          {article.publish_time 
                            ? typeof article.publish_time === 'number' 
                              ? dayjs.unix(article.publish_time).fromNow() 
                              : dayjs(article.publish_time).fromNow() 
                            : '未知时间'
                          }
                        </span>
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
                        <span style={{ fontSize: '11px', color: '#8c8c8c' }}>{article.mp_name || '未知公众号'}</span>
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
}

export default ArticleManagement;
