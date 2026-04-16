import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../services/api';

export const login = createAsyncThunk('auth/login', async (credentials, { rejectWithValue }) => {
  try {
    const { data } = await api.post('/auth/login/', credentials);
    localStorage.setItem('access', data.access);
    localStorage.setItem('refresh', data.refresh);
    return data;
  } catch (err) {
    return rejectWithValue(err.response?.data || 'Ошибка входа');
  }
});

export const logout = createAsyncThunk('auth/logout', async (_, { getState }) => {
  const refresh = localStorage.getItem('refresh');
  if (refresh) {
    await api.post('/auth/logout/', { refresh }).catch(() => {});
  }
  localStorage.removeItem('access');
  localStorage.removeItem('refresh');
});

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    token: localStorage.getItem('access'),
    user: null,
    loading: false,
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(login.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.token = action.payload.access;
        state.user = action.payload.user;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(logout.fulfilled, (state) => {
        state.token = null;
        state.user = null;
      });
  },
});

export default authSlice.reducer;
