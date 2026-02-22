import React from 'react';
import { List, Space, Typography } from 'antd';

const { Text } = Typography;

/**
 * 通用字段值渲染组件
 * @param {string} type - 字段类型
 * @param {string|Array} value - 字段值
 * @param {string} separator - 分隔符（可选）
 */
const FieldValue = ({ type, value, separator = ',' }) => {
  if (!value) return <Text type="secondary">暂无内容</Text>;

  const parseTags = (str, sep) => {
    if (!str || typeof str !== 'string') return [];
    return str.split(sep).filter(t => t.trim()).map(t => t.trim());
  };

  const parseLines = (str, sep) => {
    if (!str || typeof str !== 'string') return [];
    return str.split(sep).filter(t => t.trim()).map(t => t.trim());
  };

  switch (type) {
    case 'tags_comma':
      const tagsComma = parseTags(value, separator);
      return (
        <Space wrap>
          {tagsComma.map((tag, idx) => (
            <span key={idx} style={{ background: '#f0f5ff', color: '#1890ff', padding: '2px 8px', borderRadius: 4, fontSize: 12 }}>{tag}</span>
          ))}
        </Space>
      );
    case 'tags_hash':
      const tagsHash = parseTags(value, '#');
      return (
        <Space wrap>
          {tagsHash.map((tag, idx) => (
            <span key={idx} style={{ background: '#f6ffed', color: '#52c41a', padding: '2px 8px', borderRadius: 4, fontSize: 12 }}>{tag}</span>
          ))}
        </Space>
      );
    case 'lines_semicolon':
      const linesSemi = parseLines(value, ';');
      return (
        <List
          size="small"
          dataSource={linesSemi}
          renderItem={(item) => <List.Item style={{ padding: '4px 0' }}>• {item}</List.Item>}
        />
      );
    case 'lines_period':
      const linesPeriod = parseLines(value, '.');
      return (
        <List
          size="small"
          dataSource={linesPeriod}
          renderItem={(item) => <List.Item style={{ padding: '4px 0' }}>• {item}</List.Item>}
        />
      );
    default:
      return <Text>{value}</Text>;
  }
};

export default FieldValue;