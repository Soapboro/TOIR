import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { login } from '../store/authSlice';

export default function LoginPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { loading, error } = useSelector((s) => s.auth);
  const [form, setForm] = useState({ email: '', password: '' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await dispatch(login(form));
    if (login.fulfilled.match(result)) navigate('/');
  };

  return (
    <div style={{ maxWidth: 400, margin: '100px auto', padding: 24 }}>
      <h1>ТОИР — Вход</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <input
            type="email" placeholder="Email" value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            style={{ display: 'block', width: '100%', marginBottom: 8, padding: 8 }}
          />
        </div>
        <div>
          <input
            type="password" placeholder="Пароль" value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            style={{ display: 'block', width: '100%', marginBottom: 8, padding: 8 }}
          />
        </div>
        {error && <p style={{ color: 'red' }}>Неверный email или пароль.</p>}
        <button type="submit" disabled={loading} style={{ padding: '8px 16px' }}>
          {loading ? 'Вход...' : 'Войти'}
        </button>
      </form>
    </div>
  );
}
