import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import useAuthStore from './store/authStore';
import AppLayout from './components/AppLayout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import EquipmentPage from './pages/EquipmentPage';
import RequestsPage from './pages/RequestsPage';
import MaintenancePage from './pages/MaintenancePage';
import AnalyticsPage from './pages/AnalyticsPage';
import NotificationsPage from './pages/NotificationsPage';
import UsersPage from './pages/UsersPage';

function PrivateRoute({ children }) {
  const token = useAuthStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return <AppLayout>{children}</AppLayout>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/"              element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
      <Route path="/equipment"     element={<PrivateRoute><EquipmentPage /></PrivateRoute>} />
      <Route path="/requests"      element={<PrivateRoute><RequestsPage /></PrivateRoute>} />
      <Route path="/maintenance"   element={<PrivateRoute><MaintenancePage /></PrivateRoute>} />
      <Route path="/analytics"     element={<PrivateRoute><AnalyticsPage /></PrivateRoute>} />
      <Route path="/notifications" element={<PrivateRoute><NotificationsPage /></PrivateRoute>} />
      <Route path="/users"         element={<PrivateRoute><UsersPage /></PrivateRoute>} />
      <Route path="*"              element={<Navigate to="/" replace />} />
    </Routes>
  );
}
