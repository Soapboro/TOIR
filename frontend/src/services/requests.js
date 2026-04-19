import api from './api';

const unpack = (r) => (Array.isArray(r.data) ? r.data : (r.data.results ?? r.data));

export const requestsApi = {
  list:      (params)              => api.get('/requests/', { params }).then(unpack),
  detail:    (id)                  => api.get(`/requests/${id}/`).then((r) => r.data),
  create:    (data)                => api.post('/requests/', data).then((r) => r.data),
  assign:    (id, user_id)         => api.put(`/requests/${id}/assign/`, { user_id }).then((r) => r.data),
  setStatus: (id, status, notes)   =>
    api.put(`/requests/${id}/status/`, { status, ...(notes ? { resolution_notes: notes } : {}) }).then((r) => r.data),
};

export const usersApi = {
  list: (params) => api.get('/users/', { params }).then(unpack),
};

export const equipmentApi = {
  list: (params) => api.get('/equipment/', { params }).then(unpack),
};
