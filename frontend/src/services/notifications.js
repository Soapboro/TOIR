import api from './api';

export const notificationsApi = {
  list:        (params) => api.get('/notifications/', { params }).then((r) => r.data),
  unreadCount: ()       => api.get('/notifications/unread-count/').then((r) => r.data.count),
  markRead:    (id)     => api.put(`/notifications/${id}/read/`).then((r) => r.data),
  markAllRead: ()       => api.put('/notifications/read-all/').then((r) => r.data),
};
