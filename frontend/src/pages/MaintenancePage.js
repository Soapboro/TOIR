import React, { useState, useMemo } from 'react';
import {
  Table, Calendar, Badge, Button, Space, Select, Segmented,
  Typography, Row, Col, Card, DatePicker, Tooltip, ConfigProvider,
} from 'antd';
import {
  PlusOutlined, TableOutlined, CalendarOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import 'dayjs/locale/ru';
import locale from 'antd/locale/ru_RU';
import { maintenanceApi, equipmentApi } from '../services/maintenance';
import {
  PLAN_STATUS, MAINTENANCE_TYPE, STATUS_OPTIONS, resolveStatus,
} from '../components/maintenance/constants';
import CreatePlanModal from '../components/maintenance/CreatePlanModal';
import PlanStatusTag from '../components/maintenance/PlanStatusTag';

dayjs.locale('ru');

const { Title, Text } = Typography;

const STATUS_ROW_BG = {
  planned:     'rgba(22,119,255,0.06)',
  in_progress: 'rgba(250,140,22,0.08)',
  completed:   'rgba(82,196,26,0.06)',
  overdue:     'rgba(255,77,79,0.08)',
  cancelled:   'transparent',
};

function getEquipmentLabel(plan) {
  if (plan.equipment_detail?.name) return plan.equipment_detail.name;
  if (plan.equipment_name) return plan.equipment_name;
  return `#${plan.equipment}`;
}

export default function MaintenancePage() {
  const [view, setView] = useState('table');
  const [createOpen, setCreateOpen] = useState(false);
  const [createDefaultDate, setCreateDefaultDate] = useState(null);
  const [filterMonth, setFilterMonth] = useState(null);
  const [filterEquipment, setFilterEquipment] = useState(null);
  const [filterStatus, setFilterStatus] = useState(null);
  const [calendarValue, setCalendarValue] = useState(dayjs());

  const { data: plans = [], isLoading } = useQuery({
    queryKey: ['maintenance-plans'],
    queryFn: () => maintenanceApi.list(),
  });

  const { data: equipment = [] } = useQuery({
    queryKey: ['equipment-list'],
    queryFn: () => equipmentApi.list(),
  });

  const filtered = useMemo(() => {
    const activeMonth = view === 'calendar' ? calendarValue : filterMonth;
    return plans.filter((plan) => {
      const status = resolveStatus(plan);
      if (filterStatus && status !== filterStatus) return false;
      if (filterEquipment && plan.equipment !== filterEquipment) return false;
      if (activeMonth) {
        const d = dayjs(plan.scheduled_date);
        if (d.month() !== activeMonth.month() || d.year() !== activeMonth.year()) return false;
      }
      return true;
    });
  }, [plans, filterStatus, filterEquipment, filterMonth, calendarValue, view]);

  const columns = [
    {
      title: 'Дата',
      dataIndex: 'scheduled_date',
      width: 110,
      sorter: (a, b) => dayjs(a.scheduled_date).unix() - dayjs(b.scheduled_date).unix(),
      defaultSortOrder: 'ascend',
      render: (v) => dayjs(v).format('DD.MM.YYYY'),
    },
    {
      title: 'Оборудование',
      key: 'equipment',
      render: (_, r) => getEquipmentLabel(r),
      ellipsis: true,
    },
    {
      title: 'Вид ТО',
      dataIndex: 'maintenance_type',
      render: (v) => MAINTENANCE_TYPE[v] ?? v,
    },
    {
      title: 'Трудоёмкость, ч',
      dataIndex: 'estimated_duration_hours',
      width: 140,
      align: 'center',
      render: (v) => v ?? '—',
    },
    {
      title: 'Статус',
      key: 'status',
      width: 150,
      render: (_, r) => <PlanStatusTag plan={r} />,
      filters: STATUS_OPTIONS.map(({ value, label }) => ({ text: label, value })),
      onFilter: (value, r) => resolveStatus(r) === value,
    },
    {
      title: 'Примечания',
      dataIndex: 'notes',
      ellipsis: true,
      render: (v) => v || '—',
    },
  ];

  const cellRender = (date, info) => {
    if (info.type !== 'date') return info.originNode;
    const dayPlans = plans.filter(
      (p) =>
        (!filterEquipment || p.equipment === filterEquipment) &&
        (!filterStatus || resolveStatus(p) === filterStatus) &&
        dayjs(p.scheduled_date).isSame(date, 'day'),
    );
    if (!dayPlans.length) return null;
    return (
      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {dayPlans.slice(0, 3).map((p) => {
          const status = resolveStatus(p);
          const cfg = PLAN_STATUS[status] ?? { color: '#d9d9d9' };
          return (
            <li key={p.id} style={{ marginBottom: 2 }}>
              <Tooltip
                title={`${getEquipmentLabel(p)} — ${MAINTENANCE_TYPE[p.maintenance_type] ?? p.maintenance_type}`}
              >
                <Badge
                  color={cfg.color}
                  text={
                    <Text style={{ fontSize: 11, color: cfg.color, fontWeight: 500 }}>
                      {getEquipmentLabel(p)}
                    </Text>
                  }
                />
              </Tooltip>
            </li>
          );
        })}
        {dayPlans.length > 3 && (
          <li>
            <Text type="secondary" style={{ fontSize: 11 }}>
              ещё {dayPlans.length - 3}...
            </Text>
          </li>
        )}
      </ul>
    );
  };

  const handleCalendarSelect = (date) => {
    setCreateDefaultDate(date);
    setCreateOpen(true);
  };

  const handleCalendarPanelChange = (date) => {
    setCalendarValue(date);
  };

  return (
    <ConfigProvider locale={locale}>
      <div style={{ padding: 24 }}>
        {/* Header */}
        <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
          <Col>
            <Title level={4} style={{ margin: 0 }}>Планирование ТО</Title>
          </Col>
          <Col>
            <Space>
              <Segmented
                value={view}
                onChange={setView}
                options={[
                  { value: 'table', icon: <TableOutlined />, label: 'Таблица' },
                  { value: 'calendar', icon: <CalendarOutlined />, label: 'Календарь' },
                ]}
              />
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => {
                  setCreateDefaultDate(null);
                  setCreateOpen(true);
                }}
              >
                Создать запись
              </Button>
            </Space>
          </Col>
        </Row>

        {/* Filters */}
        <Card style={{ marginBottom: 16 }} styles={{ body: { padding: '12px 16px' } }}>
          <Row gutter={[12, 8]} align="middle">
            <Col>
              {view === 'table' ? (
                <DatePicker
                  picker="month"
                  format="MMMM YYYY"
                  placeholder="Все месяцы"
                  value={filterMonth}
                  onChange={setFilterMonth}
                  allowClear
                  style={{ width: 180 }}
                />
              ) : (
                <DatePicker
                  picker="month"
                  format="MMMM YYYY"
                  placeholder="Месяц"
                  value={calendarValue}
                  onChange={(d) => d && setCalendarValue(d)}
                  allowClear={false}
                  style={{ width: 180 }}
                />
              )}
            </Col>
            <Col>
              <Select
                style={{ width: 250 }}
                placeholder="Все оборудование"
                allowClear
                showSearch
                value={filterEquipment}
                onChange={setFilterEquipment}
                options={equipment.map((e) => ({
                  value: e.id,
                  label: `${e.name} [${e.inventory_number}]`,
                }))}
                filterOption={(input, opt) =>
                  opt.label.toLowerCase().includes(input.toLowerCase())
                }
              />
            </Col>
            <Col>
              <Select
                style={{ width: 180 }}
                placeholder="Все статусы"
                allowClear
                value={filterStatus}
                onChange={setFilterStatus}
                options={STATUS_OPTIONS}
              />
            </Col>
            <Col flex="auto" />
            {/* Legend */}
            <Col>
              <Space size={16}>
                {[
                  { key: 'planned', label: 'Запланировано', color: '#1677ff' },
                  { key: 'completed', label: 'Выполнено', color: '#52c41a' },
                  { key: 'overdue', label: 'Просрочено', color: '#ff4d4f' },
                ].map(({ key, label, color }) => (
                  <Badge key={key} color={color} text={<Text style={{ fontSize: 13 }}>{label}</Text>} />
                ))}
              </Space>
            </Col>
          </Row>
        </Card>

        {/* Content */}
        {view === 'table' ? (
          <Table
            rowKey="id"
            dataSource={filtered}
            columns={columns}
            loading={isLoading}
            onRow={(record) => {
              const status = resolveStatus(record);
              return {
                style: {
                  background: STATUS_ROW_BG[status] ?? 'transparent',
                },
              };
            }}
            pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (t) => `Всего: ${t}` }}
            scroll={{ x: 800 }}
          />
        ) : (
          <Card>
            <Calendar
              value={calendarValue}
              onPanelChange={handleCalendarPanelChange}
              onSelect={handleCalendarSelect}
              cellRender={cellRender}
            />
          </Card>
        )}

        <CreatePlanModal
          open={createOpen}
          onClose={() => {
            setCreateOpen(false);
            setCreateDefaultDate(null);
          }}
          defaultDate={createDefaultDate}
        />
      </div>
    </ConfigProvider>
  );
}
