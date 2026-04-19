import React from 'react';
import { Layout, Menu, Avatar, Dropdown, Typography, Space, Badge } from 'antd';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  DashboardOutlined,
  ToolOutlined,
  FileTextOutlined,
  CalendarOutlined,
  BarChartOutlined,
  BellOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import useAuthStore from '../store/authStore';
import api from '../services/api';

const { Header, Content } = Layout;
const { Text } = Typography;

const NAV_ITEMS = [
  { key: '/',             icon: <DashboardOutlined />, label: <Link to="/">Дашборд</Link> },
  { key: '/equipment',    icon: <ToolOutlined />,      label: <Link to="/equipment">Оборудование</Link> },
  { key: '/requests',     icon: <FileTextOutlined />,  label: <Link to="/requests">Заявки</Link> },
  { key: '/maintenance',  icon: <CalendarOutlined />,  label: <Link to="/maintenance">ТО</Link> },
  { key: '/analytics',    icon: <BarChartOutlined />,  label: <Link to="/analytics">Аналитика</Link> },
  { key: '/notifications',icon: <BellOutlined />,      label: <Link to="/notifications">Уведомления</Link> },
];

export default function AppLayout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = async () => {
    const { refreshToken } = useAuthStore.getState();
    if (refreshToken) {
      await api.post('/auth/logout/', { refresh: refreshToken }).catch(() => {});
    }
    logout();
    navigate('/login');
  };

  const userMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Выйти',
      onClick: handleLogout,
    },
  ];

  const selectedKey = NAV_ITEMS.find(
    (item) => item.key !== '/' && location.pathname.startsWith(item.key)
  )?.key ?? '/';

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 32,
          padding: '0 24px',
          background: '#001529',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        <Text strong style={{ color: '#fff', fontSize: 18, whiteSpace: 'nowrap', letterSpacing: 1 }}>
          ТОИР
        </Text>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[selectedKey]}
          items={NAV_ITEMS}
          style={{ flex: 1, minWidth: 0 }}
        />
        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" trigger={['click']}>
          <Space style={{ cursor: 'pointer' }}>
            <Badge dot status="success">
              <Avatar icon={<UserOutlined />} style={{ background: '#1677ff' }} />
            </Badge>
            <Text style={{ color: '#fff', whiteSpace: 'nowrap' }}>
              {user?.full_name || user?.email || 'Пользователь'}
            </Text>
          </Space>
        </Dropdown>
      </Header>
      <Content style={{ padding: 24, background: '#f5f5f5' }}>
        {children}
      </Content>
    </Layout>
  );
}
