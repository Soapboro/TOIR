import api from './api';

const unpack = (r) => (Array.isArray(r.data) ? r.data : (r.data.results ?? r.data));

export const requestsApi = {
  list:      (params)              => api.get('/requests/', { params }).then(unpack),
  detail:    (id)                  => api.get(`/requests/${id}/`).then((r) => r.data),
  create:    (data)                => api.post('/requests/', data).then((r) => r.data),
  assign:    (id, user_id)         => api.put(`/requests/${id}/assign/`, { user_id }).then((r) => r.data),
  take:      (id)                  => api.put(`/requests/${id}/take/`).then((r) => r.data),
  setStatus: (id, status, notes)   =>
    api.put(`/requests/${id}/status/`, { status, ...(notes ? { resolution_notes: notes } : {}) }).then((r) => r.data),
};

export const usersApi = {
  list: (params) => api.get('/users/', { params }).then(unpack),
  detail: (id) => api.get(`/users/${id}/`).then((r) => r.data),
  create: (data) => api.post('/users/', data).then((r) => r.data),
  update: (id, data) => api.patch(`/users/${id}/`, data).then((r) => r.data),
  delete: (id) => api.delete(`/users/${id}/`).then((r) => r.data),
};

export const equipmentApi = {
  list: (params) => api.get('/equipment/', { params }).then(unpack),
  create: (data) => api.post('/equipment/', data).then((r) => r.data),
  update: (id, data) => api.patch(`/equipment/${id}/`, data).then((r) => r.data),
  delete: (id) => api.delete(`/equipment/${id}/`).then((r) => r.data),
};
