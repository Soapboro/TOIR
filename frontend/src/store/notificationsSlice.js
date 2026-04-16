import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../services/api';

export const fetchUnreadCount = createAsyncThunk('notifications/unreadCount', async () => {
  const { data } = await api.get('/notifications/unread-count/');
  return data.count;
});

const notificationsSlice = createSlice({
  name: 'notifications',
  initialState: { unreadCount: 0 },
  reducers: {
    decrementUnread: (state) => { state.unreadCount = Math.max(0, state.unreadCount - 1); },
    clearUnread: (state) => { state.unreadCount = 0; },
  },
  extraReducers: (builder) => {
    builder.addCase(fetchUnreadCount.fulfilled, (state, action) => {
      state.unreadCount = action.payload;
    });
  },
});

export const { decrementUnread, clearUnread } = notificationsSlice.actions;
export default notificationsSlice.reducer;
