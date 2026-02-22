import React from 'react';
import ReactECharts from 'echarts-for-react';

/**
 * 文章评分分布热力图组件
 * @param {Object} data - { xAxis:[], yAxis:[], data:[[xIndex,yIndex,count],...] }
 * @param {string} scoreType - 当前评分类型，用于切换提示
 */
const HeatmapChart = ({ data, scoreType }) => {
  if (!data) return null;

  const option = {
    tooltip: {
      position: 'top',
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      textStyle: { color: '#fff', fontSize: 14 },
      formatter: function (params) {
        return `<div style="padding: 8px;">
                  <div style="font-weight: bold; margin-bottom: 4px;">文章类型: ${data.yAxis[params.value[1]]}</div>
                  <div>评分: <span style="color: #1890ff; font-weight: bold;">${data.xAxis[params.value[0]]}</span></div>
                  <div>数量: <span style="color: #52c41a; font-weight: bold;">${params.value[2]}</span></div>
                </div>`;
      }
    },
    grid: { height: '70%', top: '8%', left: '5%', right: '5%' },
    xAxis: {
      type: 'category',
      data: data.xAxis,
      name: '评分',
      nameLocation: 'middle',
      nameGap: 30,
      nameTextStyle: { fontSize: 14, fontWeight: 'bold' },
      axisLabel: { fontSize: 13, fontWeight: 'bold' },
      splitArea: { show: true, areaStyle: { color: ['rgba(250,250,250,0.3)', 'rgba(240,240,240,0.3)'] } }
    },
    yAxis: {
      type: 'category',
      data: data.yAxis,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { fontSize: 13, fontWeight: 'bold', interval: 0, color: '#333' },
      splitArea: { show: true, areaStyle: { color: ['rgba(250,250,250,0.3)', 'rgba(240,240,240,0.3)'] } }
    },
    visualMap: {
      show: false,
      min: 0,
      max: Math.max(...data.data.map(d => d[2]), 1),
      inRange: { color: ['#f0f9ff', '#bae7ff', '#91d5ff', '#69c0ff', '#40a9ff', '#1890ff', '#096dd9', '#0050b3'] }
    },
    series: [{
      name: '文章数量',
      type: 'heatmap',
      data: data.data,
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

  return <ReactECharts option={option} style={{ height: '1500px' }} />;
};

export default HeatmapChart;