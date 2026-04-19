import React, { useState } from 'react';
import {
  Button, Space, Table, Select, Typography, Row, Col, Input, Tooltip, Empty,
} from 'antd';
import { PlusOutlined, SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import useAuthStore from '../store/authStore';
import { requestsApi, usersApi } from '../services/requests';
import { PRIORITY_OPTIONS, STATUS_OPTIONS, PRIORITY } from '../components/requests/constants';
import PriorityTag from '../components/requests/PriorityTag';
import StatusBadge from '../components/requests/StatusBadge';
import CreateRequestModal from '../components/requests/CreateRequestModal';
import RequestDetailDrawer from '../components/requests/RequestDetailDrawer';

const { Title } = Typography;

export default function RequestsPage() {
  const user = useAuthStore((s) => s.user);

  const [filters, setFilters]   = useState({ status: null, priority: null, assigned_to: null, search: '' });
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedId, setSelectedId] = useState(null);

  const params = Object.fromEntries(
    Object.entries({ ...filters, search: filters.search || undefined }).filter(([, v]) => v != null)
  );

  const { data: requests = [], isLoading, refetch } = useQuery({
    queryKey: ['requests', params],
    queryFn: () => requestsApi.list(params),
  });

  const { data: users = [] } = useQuery({
    queryKey: ['users-active'],
    queryFn: () => usersApi.list({ is_active: true }),
  });

  const setFilter = (key) => (value) => setFilters((prev) => ({ ...prev, [key]: value ?? null }));

  const prioritySummary = ['critical', 'high', 'medium', 'low'].map((p) => ({
    priority: p,
    count: requests.filter((r) => r.priority === p && !['closed', 'cancelled'].includes(r.status)).length,
  })).filter((s) => s.count > 0);

  const columns = [
    {
      title: '#',
      dataIndex: 'id',
      width: 60,
      sorter: (a, b) => a.id - b.id,
    },
    {
      title: 'Оборудование',
      dataIndex: 'equipment_name',
      ellipsis: true,
      render: (name, row) => (
        <Tooltip title={`Инв. № ${row.equipment_inventory ?? '—'}`}>{name ?? '—'}</Tooltip>
      ),
    },
    {
      title: 'Тема',
      dataIndex: 'title',
      ellipsis: true,
    },
    {
      title: 'Приоритет',
      dataIndex: 'priority',
      width: 130,
      sorter: (a, b) => {
        const order = ['critical', 'high', 'medium', 'low'];
        return order.indexOf(a.priority) - order.indexOf(b.priority);
      },
      render: (p) => <PriorityTag priority={p} />,
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      width: 160,
      render: (s) => <StatusBadge status={s} />,
    },
    {
      title: 'Исполнитель',
      dataIndex: 'assigned_to_name',
      ellipsis: true,
      render: (name) => name ?? <span style={{ color: '#bfbfbf' }}>Не назначен</span>,
    },
    {
      title: 'Создана',
      dataIndex: 'created_at',
      width: 130,
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
      render: (d) => dayjs(d).format('DD.MM.YYYY'),
    },
  ];

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Space align="center" wrap>
            <Title level={4} style={{ margin: 0 }}>Заявки на ремонт</Title>
            {prioritySummary.map(({ priority, count }) => (
              <span
                key={priority}
                style={{
                  background: PRIORITY[priority].color,
                  color: '#fff',
                  borderRadius: 12,
                  padding: '2px 10px',
                  fontSize: 12,
                  fontWeight: 600,
                }}
              >
                {PRIORITY[priority].label}: {count}
              </span>
            ))}
          </Space>
        </Col>
        <Col>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
            Новая заявка
          </Button>
        </Col>
      </Row>

      <Row gutter={12} style={{ marginBottom: 16 }}>
        <Col flex="1">
          <Input
            placeholder="Поиск по теме или описанию"
            prefix={<SearchOutlined />}
            value={filters.search}
            onChange={(e) => setFilter('search')(e.target.value || null)}
            allowClear
          />
        </Col>
        <Col>
          <Select
            placeholder="Статус"
            allowClear
            style={{ width: 180 }}
            options={STATUS_OPTIONS}
            value={filters.status}
            onChange={setFilter('status')}
          />
        </Col>
        <Col>
          <Select
            placeholder="Приоритет"
            allowClear
            style={{ width: 160 }}
            options={PRIORITY_OPTIONS}
            value={filters.priority}
            onChange={setFilter('priority')}
          />
        </Col>
        <Col>
          <Select
            placeholder="Исполнитель"
            allowClear
            showSearch
            style={{ width: 200 }}
            options={users.map((u) => ({ value: u.id, label: u.full_name || u.email }))}
            value={filters.assigned_to}
            onChange={setFilter('assigned_to')}
            filterOption={(input, opt) => opt.label.toLowerCase().includes(input.toLowerCase())}
          />
        </Col>
        <Col>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()} />
        </Col>
      </Row>

      <Table
        dataSource={requests}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        locale={{ emptyText: <Empty description="Заявок не найдено" /> }}
        pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (t) => `Всего: ${t}` }}
        onRow={(row) => ({ onClick: () => setSelectedId(row.id), style: { cursor: 'pointer' } })}
        rowClassName={(row) =>
          row.priority === 'critical' && !['closed', 'cancelled', 'completed'].includes(row.status)
            ? 'row-critical'
            : ''
        }
      />

      <style>{`
        .row-critical td { background: #fff2f0 !important; }
        .row-critical:hover td { background: #ffe7e0 !important; }
      `}</style>

      <CreateRequestModal open={createOpen} onClose={() => setCreateOpen(false)} />

      <RequestDetailDrawer requestId={selectedId} onClose={() => setSelectedId(null)} />
    </div>
  );
}
