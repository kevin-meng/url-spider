import axios from 'axios';

// 使用相对路径，这样在Docker环境中也能正确连接到后端服务
const API_BASE = '';

const articleAPI = {
  getProgress: async () => {
    const response = await axios.get(`${API_BASE}/api/progress`);
    return response;
  },
  getArticles: async (params) => {
    const response = await axios.get(`${API_BASE}/api/articles`, { params });
    return response;
  },
  getArticle: async (id) => {
    const response = await axios.get(`${API_BASE}/api/articles/${id}`);
    return response;
  },
  updateArticle: async (id, data) => {
    const response = await axios.put(`${API_BASE}/api/articles/${id}`, data);
    return response;
  },
  getStats: async (params) => {
    const response = await axios.get(`${API_BASE}/api/stats`, { params });
    return response;
  },
  getHeatmap: async (params) => {
    const response = await axios.get(`${API_BASE}/api/heatmap`, { params });
    return response;
  },
  getMonthlyStats: async (params) => {
    const response = await axios.get(`${API_BASE}/api/monthly-stats`, { params });
    return response;
  }
};

export { articleAPI };