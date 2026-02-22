import React from 'react';
import { Form, List, Typography, Button, Space, Divider, InputNumber, Input } from 'antd';
import { StarFilled, StarOutlined, CheckCircleOutlined, CloseCircleOutlined, ReadOutlined, ReadFilled, EditOutlined, SaveOutlined, CloseOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { Text } = Typography;
const { TextArea } = Input;

/**
 * 文章详情组件
 * @param {Object} article - 文章详情数据
 * @param {boolean} editing - 是否处于编辑状态
 * @param {Function} onToggleFlag - 切换文章标志位回调 (field, value)
 * @param {Function} onToggleEdit - 切换编辑状态回调
 * @param {Function} onSave - 保存编辑回调
 * @param {Object} form - Ant Design 表单实例
 * @param {Array} fields - 字段配置数组
 */
const ArticleDetail = ({ 
  article, 
  editing, 
  onToggleFlag, 
  onToggleEdit, 
  onSave, 
  form, 
  fields 
}) => {
  if (!article) return null;

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
              <span key={idx} style={{ background: '#f0f5ff', color: '#1890ff', padding: '2px 8px', borderRadius: 4, fontSize: 12 }}>{tag}</span>
            ))}
          </Space>
        );
      case 'tags_hash':
        return (
          <Space wrap>
            {parseTags(value, '#').map((tag, idx) => (
              <span key={idx} style={{ background: '#f6ffed', color: '#52c41a', padding: '2px 8px', borderRadius: 4, fontSize: 12 }}>{tag}</span>
            ))}
          </Space>
        );
      case 'lines_semicolon':
        return (
          <List
            size="small"
            dataSource={parseLines(value, ';')}
            renderItem={(item) => <List.Item style={{ padding: '4px 0' }}>• {item}</List.Item>}
          />
        );
      case 'lines_period':
        return (
          <List
            size="small"
            dataSource={parseLines(value, '.')}
            renderItem={(item) => <List.Item style={{ padding: '4px 0' }}>• {item}</List.Item>}
          />
        );
      default:
        return <Text>{value}</Text>;
    }
  };

  return (
    <div style={{ height: '100%', overflow: 'auto', padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div />
          <div style={{ display: 'flex', gap: 8 }}>
            <Button
              size="small"
              icon={editing ? <CloseOutlined /> : <EditOutlined />}
              onClick={onToggleEdit}
            >
              {editing ? '取消编辑' : '编辑'}
            </Button>
            {editing && (
              <Button size="small" icon={<SaveOutlined />} onClick={onSave}>
                保存
              </Button>
            )}
          </div>
        </div>
        <div style={{ marginBottom: 16 }}>
          <Text strong style={{ fontSize: '16px' }}>{article.title}</Text>
        </div>
        <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
          <Space>
            <Text type="secondary">公众号:</Text>
            <Text>{article.mp_name}</Text>
          </Space>
          <Space>
            <Text type="secondary">发布时间:</Text>
            <Text>{dayjs(article.publish_time).format('YYYY-MM-DD HH:mm')}</Text>
          </Space>
          <Space>
            <Text type="secondary">评分:</Text>
            <Text style={{ color: '#1890ff', fontWeight: 'bold' }}>{article.socre}</Text>
          </Space>
          <Space>
            <Text type="secondary">pre_value:</Text>
            <Text style={{ color: '#52c41a', fontWeight: 'bold' }}>{article.pre_value_score}</Text>
          </Space>
        </div>
        <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
          <Button
            size="small"
            icon={article.is_collected ? <StarFilled /> : <StarOutlined />}
            type={article.is_collected ? 'primary' : 'default'}
            onClick={() => onToggleFlag('is_collected', !article.is_collected)}
          >
            {article.is_collected ? '已收藏' : '收藏'}
          </Button>
          <Button
            size="small"
            icon={article.is_followed ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
            type={article.is_followed ? 'primary' : 'default'}
            onClick={() => onToggleFlag('is_followed', !article.is_followed)}
          >
            {article.is_followed ? '已关注' : '关注'}
          </Button>
          <Button
            size="small"
            icon={article.is_discarded ? <CloseCircleOutlined /> : <CheckCircleOutlined />}
            type={article.is_discarded ? 'danger' : 'default'}
            onClick={() => onToggleFlag('is_discarded', !article.is_discarded)}
          >
            {article.is_discarded ? '已弃用' : '弃用'}
          </Button>
          <Button
            size="small"
            icon={article.is_read ? <ReadFilled /> : <ReadOutlined />}
            type={article.is_read ? 'primary' : 'default'}
            onClick={() => onToggleFlag('is_read', !article.is_read)}
          >
            {article.is_read ? '已读' : '未读'}
          </Button>
        </div>
      </div>
      <Divider />
      <Form form={form} layout="vertical">
        {fields.map(field => (
          <Form.Item
            key={field.key}
            label={
              <span style={{ fontWeight: 500 }}>
                {field.label}
                {field.key === 'socre' && (
                  <span style={{ marginLeft: 8, color: '#1890ff', fontSize: '12px' }}>当前评分</span>
                )}
              </span>
            }
            name={field.key}
          >
            {editing ? (
              field.type === 'number' ? (
                <InputNumber min={0} max={10} style={{ width: '100%' }} />
              ) : field.type === 'text' ? (
                <TextArea rows={field.key === '概要' ? 4 : 3} />
              ) : (
                <TextArea />
              )
            ) : (
              <div style={{ padding: '8px 12px', background: '#f5f5f5', borderRadius: '6px' }}>
                {renderFieldValue(field, article[field.key])}
              </div>
            )}
          </Form.Item>
        ))}
      </Form>
    </div>
  );
};

export default ArticleDetail;