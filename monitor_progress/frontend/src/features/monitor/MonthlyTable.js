import React from 'react';
import { Table, Pagination } from 'antd';

/**
 * 账号文章发布时间统计表格（近24个月）
 * @param {Object} data - { data:[], months:[], total, page_size }
 * @param {number} currentPage - 当前页码
 * @param {Function} onPageChange - 页码变化回调
 */
const MonthlyTable = ({ data, currentPage, onPageChange }) => {
  if (!data) return null;

  const columns = [
    {
      title: '序号',
      key: 'index',
      fixed: 'left',
      width: 70,
      align: 'center',
      render: (_, __, index) => (
        <span style={{ fontWeight: 'bold', color: '#8c8c8c' }}>
          {index + 1 + (currentPage - 1) * data.page_size}
        </span>
      )
    },
    {
      title: '公众号名称',
      dataIndex: 'mp_name',
      key: 'mp_name',
      fixed: 'left',
      width: 220,
      render: (text) => <span style={{ fontWeight: 500 }}>{text}</span>
    }
  ];

  data.months.forEach(month => {
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

  return (
    <>
      <Table
        columns={columns}
        dataSource={data.data}
        rowKey="mp_id"
        pagination={false}
        scroll={{ x: data.months.length * 85 + 310 }}
        size="middle"
        style={{ marginTop: 16 }}
      />
      <div style={{ marginTop: 32, textAlign: 'center' }}>
        <Pagination
          current={currentPage}
          total={data.total}
          pageSize={data.page_size}
          onChange={onPageChange}
          showSizeChanger={false}
          showQuickJumper
          showTotal={(total) => `共 ${total} 个账号`}
          size="large"
        />
      </div>
    </>
  );
};

export default MonthlyTable;