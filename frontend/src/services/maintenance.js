import api from './api';

const unpack = (r) => (Array.isArray(r.data) ? r.data : (r.data.results ?? r.data));

export const maintenanceApi = {
  list:   (params) => api.get('/maintenance/plans/', { params }).then(unpack),
  create: (data)   => api.post('/maintenance/plans/', data).then((r) => r.data),
  update: (id, data) => api.patch(`/maintenance/plans/${id}/`, data).then((r) => r.data),
};

export const maintenanceRecordsApi = {
  list: (params) => api.get('/maintenance-records/', { params }).then(unpack),
  create: (data) => api.post('/maintenance-records/', data).then((r) => r.data),
};

export const maintenanceSchedulesApi = {
  list: (params) => api.get('/schedules/', { params }).then(unpack),
  update: (id, data) => api.patch(`/schedules/${id}/`, data).then((r) => r.data),
};

export const regulationsApi = {
  list: (params) => api.get('/regulations/', { params }).then(unpack),
  create: (equipmentId, data) => api.post(`/equipment/${equipmentId}/regulations/`, data).then((r) => r.data),
  update: (id, data) => api.patch(`/regulations/${id}/`, data).then((r) => r.data),
  delete: (id) => api.delete(`/regulations/${id}/`).then((r) => r.data),
};

export const equipmentApi = {
  list: (params) => api.get('/equipment/', { params }).then(unpack),
};
