import axios from 'axios';

// 使用相对路径，这样在Docker环境中也能正确连接到后端服务
const API_BASE = '';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // 处理未授权情况
      console.error('未授权访问');
    }
    return Promise.reject(error);
  }
);

// 文章相关 API
export const articleAPI = {
  // 获取文章列表
  getArticles: (params) => api.get('/api/articles', { params }),
  
  // 获取文章详情
  getArticle: (id) => api.get(`/api/articles/${id}`),
  
  // 更新文章
  updateArticle: (id, data) => api.put(`/api/articles/${id}`, data),
  
  // 获取标签列表
  getTags: (params) => api.get('/api/tags', { params }),
  
  // 获取统计信息
  getStats: (params) => api.get('/api/stats', { params }),
  
  // 获取热力图数据
  getHeatmap: (params) => api.get('/api/heatmap', { params }),
  
  // 获取月度统计
  getMonthlyStats: (params) => api.get('/api/monthly-stats', { params }),
};

// 监控相关 API
export const monitorAPI = {
  // 获取监控数据
  getMonitorData: (params) => api.get('/api/monitor', { params }),
};

export default api;
