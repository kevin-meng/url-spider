import React from 'react';
import { Card, List, Tag, Space, Typography, Spin, Pagination } from 'antd';
import dayjs from 'dayjs';
import { StarFilled, ReadFilled, CloseCircleOutlined } from '@ant-design/icons';

const { Text } = Typography;

/**
 * 文章列表组件
 * @param {Array} articles - 文章数组
 * @param {Object} selectedArticle - 当前选中的文章
 * @param {Function} onSelect - 点击文章项的回调
 * @param {boolean} loading - 加载状态
 * @param {number} currentPage - 当前页码
 * @param {number} total - 总条数
 * @param {number} pageSize - 每页条数
 * @param {Function} onPageChange - 页码变化回调
 */
const ArticleList = ({ 
  articles, 
  selectedArticle, 
  onSelect, 
  loading, 
  currentPage, 
  total, 
  pageSize, 
  onPageChange 
}) => {
  const parseTags = (value) => {
    if (!value || typeof value !== 'string') return [];
    return value.split(',').map(t => t.trim()).filter(Boolean);
  };



  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
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
            renderItem={(article) => {
              let tagsList = [];
              if (Array.isArray(article.tags)) {
                tagsList = article.tags.filter(Boolean).map(t => String(t).trim()).filter(Boolean);
              } else if (typeof article.tags === 'string') {
                tagsList = parseTags(article.tags);
              } else if (Array.isArray(article.article_type)) {
                tagsList = article.article_type.filter(Boolean);
              } else if (typeof article.article_type === 'string' && article.article_type.trim()) {
                tagsList = [article.article_type.trim()];
              }

              return (
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
                  onClick={() => onSelect(article._id)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1, marginRight: 12 }}>
                      <div style={{ fontWeight: 500, marginBottom: 4, lineHeight: '1.4' }}>
                        {article.title}
                      </div>
                      <div style={{ fontSize: '12px', color: '#8c8c8c', marginBottom: 4 }}>
                        {article.mp_name} · {dayjs(article.publish_time).format('MM-DD HH:mm')}
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
                      {tagsList.length > 0 && (
                        <div style={{ marginBottom: 4 }}>
                          <Space wrap size={4}>
                            {tagsList.slice(0, 3).map((tag, idx) => (
                              <Tag key={idx} style={{ fontSize: '10px' }}>{tag}</Tag>
                            ))}
                            {tagsList.length > 3 && (
                              <Tag style={{ fontSize: '10px' }}>+{tagsList.length - 3}</Tag>
                            )}
                          </Space>
                        </div>
                      )}
                      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                        <Space size={8}>
                          <span style={{ fontSize: '11px', color: '#1890ff' }}>评分: {article.socre}</span>
                          <span style={{ fontSize: '11px', color: '#52c41a' }}>pre: {article.pre_value_score}</span>
                        </Space>
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      {article.is_collected && <StarFilled style={{ color: '#faad14', fontSize: '14px' }} />}
                      {article.is_read && <ReadFilled style={{ color: '#52c41a', fontSize: '14px' }} />}
                      {article.is_discarded && <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: '14px' }} />}
                    </div>
                  </div>
                </Card>
              );
            }}
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
          onChange={onPageChange}
          showSizeChanger={false}
          showQuickJumper
          showTotal={(total) => `共 ${total} 条`}
          size="small"
          style={{ textAlign: 'center' }}
        />
      </div>
    </div>
  );
};

export default ArticleList;