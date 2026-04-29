import api from './api';

const unpack = (r) => (Array.isArray(r.data) ? r.data : (r.data.results ?? r.data));

export const analyticsApi = {
  summary:       ()     => api.get('/analytics/summary/').then((r) => r.data),
  requestsTrend: (year) => api.get('/analytics/requests-trend/', { params: { year } }).then(unpack),
  predictions:   ()     => api.get('/analytics/predictions/').then(unpack),
  equipmentStats: ()    => api.get('/analytics/equipment-stats/').then(unpack),
};
