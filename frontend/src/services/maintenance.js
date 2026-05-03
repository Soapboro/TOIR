import api from './api';

const unpack = (r) => (Array.isArray(r.data) ? r.data : (r.data.results ?? r.data));

export const maintenanceApi = {
  list:   (params) => api.get('/maintenance/plans/', { params }).then(unpack),
  create: (data)   => api.post('/maintenance/plans/', data).then((r) => r.data),
  update: (id, data) => api.patch(`/maintenance/plans/${id}/`, data).then((r) => r.data),
};

export const maintenanceRecordsApi = {
  create: (data) => api.post('/maintenance-records/', data).then((r) => r.data),
};

export const equipmentApi = {
  list: (params) => api.get('/equipment/', { params }).then(unpack),
};
