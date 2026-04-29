import React, { useState, useMemo } from 'react';
import {
  Button, Table, Calendar, Select, Badge, Tag, Space, Typography,
  Segmented, Tooltip, Empty, Spin, Row, Col, Card,
} from 'antd';
import {
  PlusOutlined, TableOutlined, CalendarOutlined,
  ToolOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import 'dayjs/locale/ru';
import { maintenanceApi, equipmentApi } from '../services/maintenance';
import {
  PLAN_STATUS, MAINTENANCE_TYPE, STATUS_OPTIONS, resolveStatus,
} from '../components/maintenance/constants';
import PlanStatusTag from '../components/maintenance/PlanStatusTag';
import CreatePlanModal from '../components/maintenance/CreatePlanModal';

dayjs.locale('ru');

const { Title } = Typography;

const MONTH_OPTIONS = Array.from({ length: 12 }, (_, i) => ({
  value: i + 1,
  label: dayjs().month(i).format('MMMM'),
}));

const YEAR_OPTIONS = [-1, 0, 1].map((offset) => {
  const y = dayjs().year() + offset;
  return { value: y, label: String(y) };
});

export default function MaintenancePage() {
  const [view, setView] = useState('table');
  const [filterMonth, setFilterMonth] = useState(dayjs().month() + 1);
  const [filterYear, setFilterYear] = useState(dayjs().year());
  const [filterEquipment, setFilterEquipment] = useState(null);
  const [filterStatus, setFilterStatus] = useState(null);
  const [calendarValue, setCalendarValue] = useState(dayjs());
  const [modalOpen, setModalOpen] = useState(false);
  const [modalDefaultDate, setModalDefaultDate] = useState(null);

  const { data: plans = [], isLoading } = useQuery({
    queryKey: ['maintenance-plans', filterMonth, filterYear, filterEquipment, filterStatus],
    queryFn: () => maintenanceApi.list({
      month: filterMonth,
      year: filterYear,
      ...(filterEquipment ? { equipment: filterEquipment } : {}),
      ...(filterStatus ? { status: filterStatus } : {}),
    }),
  });

  const { data: equipment = [] } = useQuery({
    queryKey: ['equipment-list'],
    queryFn: () => equipmentApi.list(),
  });

  const equipOptions = useMemo(
    () => equipment.map((e) => ({ value: e.id, label: `${e.name} [${e.inventory_number}]` })),
    [equipment],
  );

  // plans keyed by date string for calendar
  const plansByDate = useMemo(() => {
    const map = {};
    plans.forEach((p) => {
      const key = dayjs(p.scheduled_date).format('YYYY-MM-DD');
      if (!map[key]) map[key] = [];
      map[key].push(p);
    });
    return map;
  }, [plans]);

  const openCreate = (date = null) => {
    setModalDefaultDate(date);
    setModalOpen(true);
  };

  // sync calendar nav → month/year filters
  const handleCalendarChange = (date) => {
    setCalendarValue(date);
    setFilterMonth(date.month() + 1);
    setFilterYear(date.year());
  };

  const handleCalendarPanelChange = (date) => {
    setCalendarValue(date);
    setFilterMonth(date.month() + 1);
    setFilterYear(date.year());
  };

  /* ── TABLE COLUMNS ───────────────────────────────────────────── */
  const columns = [
    {
      title: 'Дата',
      dataIndex: 'scheduled_date',
      key: 'date',
      width: 120,
      sorter: (a, b) => dayjs(a.scheduled_date).unix() - dayjs(b.scheduled_date).unix(),
      render: (v) => dayjs(v).format('DD.MM.YYYY'),
    },
    {
      title: 'Оборудование',
      dataIndex: ['equipment_detail', 'name'],
      key: 'equipment',
      ellipsis: true,
      render: (name, record) => (
        <Tooltip title={record.equipment_detail?.inventory_number}>
          <span>{name ?? '—'}</span>
        </Tooltip>
      ),
    },
    {
      title: 'Вид ТО',
      dataIndex: 'maintenance_type',
      key: 'type',
      width: 160,
      render: (v) => MAINTENANCE_TYPE[v] ?? v,
    },
    {
      title: 'Трудоёмкость, ч',
      dataIndex: 'estimated_duration_hours',
      key: 'duration',
      width: 140,
      align: 'right',
      render: (v) => (v != null ? Number(v).toFixed(1) : '—'),
    },
    {
      title: 'Исполнитель',
      dataIndex: ['assigned_to_detail', 'full_name'],
      key: 'assigned',
      width: 160,
      render: (v) => v ?? '—',
    },
    {
      title: 'Статус',
      key: 'status',
      width: 150,
      render: (_, record) => <PlanStatusTag plan={record} />,
      filters: STATUS_OPTIONS.map(({ value, label }) => ({ text: label, value })),
      onFilter: (value, record) => resolveStatus(record) === value,
    },
    {
      title: 'Примечания',
      dataIndex: 'notes',
      key: 'notes',
      ellipsis: true,
      render: (v) => v || '—',
    },
  ];

  /* ── CALENDAR CELL RENDERER ──────────────────────────────────── */
  const dateCellRender = (date) => {
    const key = date.format('YYYY-MM-DD');
    const items = plansByDate[key];
    if (!items?.length) return null;
    return (
      <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
        {items.slice(0, 3).map((p) => {
          const status = resolveStatus(p);
          const cfg = PLAN_STATUS[status] ?? { color: '#d9d9d9', label: status };
          return (
            <li key={p.id} style={{ marginBottom: 2 }}>
              <Tooltip
                title={`${p.equipment_detail?.name ?? ''} — ${MAINTENANCE_TYPE[p.maintenance_type] ?? p.maintenance_type}`}
              >
                <Badge
                  color={cfg.color}
                  text={
                    <span style={{ fontSize: 11, lineHeight: '14px' }}>
                      {p.equipment_detail?.name ?? `#${p.id}`}
                    </span>
                  }
                />
              </Tooltip>
            </li>
          );
        })}
        {items.length > 3 && (
          <li>
            <span style={{ fontSize: 11, color: '#8c8c8c' }}>+{items.length - 3} ещё</span>
          </li>
        )}
      </ul>
    );
  };

  /* ── CALENDAR: click on date to create ──────────────────────── */
  const handleCalendarSelect = (date, { source }) => {
    if (source === 'date') {
      setCalendarValue(date);
    }
  };

  /* ── LEGEND ─────────────────────────────────────────────────── */
  const Legend = () => (
    <Space wrap size={8}>
      {Object.entries(PLAN_STATUS).map(([key, { label, color }]) => (
        <Tag key={key} style={{ background: color, color: '#fff', border: 'none', fontWeight: 500 }}>
          {label}
        </Tag>
      ))}
    </Space>
  );

  /* ── FILTER BAR ─────────────────────────────────────────────── */
  const FilterBar = () => (
    <Space wrap>
      <Select
        value={filterMonth}
        onChange={(v) => {
          setFilterMonth(v);
          setCalendarValue(calendarValue.month(v - 1));
        }}
        options={MONTH_OPTIONS}
        style={{ width: 130 }}
        placeholder="Месяц"
      />
      <Select
        value={filterYear}
        onChange={(v) => {
          setFilterYear(v);
          setCalendarValue(calendarValue.year(v));
        }}
        options={YEAR_OPTIONS}
        style={{ width: 90 }}
      />
      <Select
        allowClear
        value={filterEquipment}
        onChange={setFilterEquipment}
        options={equipOptions}
        style={{ minWidth: 220 }}
        placeholder="Оборудование"
        showSearch
        filterOption={(input, opt) => opt.label.toLowerCase().includes(input.toLowerCase())}
      />
      <Select
        allowClear
        value={filterStatus}
        onChange={setFilterStatus}
        options={STATUS_OPTIONS}
        style={{ width: 160 }}
        placeholder="Статус"
      />
    </Space>
  );

  return (
    <div style={{ padding: 24 }}>
      {/* ── HEADER ── */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Space align="center">
            <ToolOutlined style={{ fontSize: 22, color: '#1677ff' }} />
            <Title level={4} style={{ margin: 0 }}>Планирование ТО</Title>
          </Space>
        </Col>
        <Col>
          <Space>
            <Segmented
              value={view}
              onChange={setView}
              options={[
                { label: 'Таблица', value: 'table', icon: <TableOutlined /> },
                { label: 'Календарь', value: 'calendar', icon: <CalendarOutlined /> },
              ]}
            />
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => openCreate()}
            >
              Новая запись
            </Button>
          </Space>
        </Col>
      </Row>

      {/* ── FILTERS + LEGEND ── */}
      <Card
        size="small"
        style={{ marginBottom: 16 }}
        styles={{ body: { padding: '10px 16px' } }}
      >
        <Row justify="space-between" align="middle" wrap>
          <Col><FilterBar /></Col>
          <Col style={{ marginTop: 4 }}><Legend /></Col>
        </Row>
      </Card>

      {/* ── TABLE VIEW ── */}
      {view === 'table' && (
        <Spin spinning={isLoading}>
          <Table
            rowKey="id"
            columns={columns}
            dataSource={plans}
            pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (t) => `Всего: ${t}` }}
            size="small"
            locale={{ emptyText: <Empty description="Нет записей за выбранный период" /> }}
            rowClassName={(record) => {
              const s = resolveStatus(record);
              if (s === 'overdue') return 'row-overdue';
              if (s === 'completed') return 'row-completed';
              return '';
            }}
          />
        </Spin>
      )}

      {/* ── CALENDAR VIEW ── */}
      {view === 'calendar' && (
        <Spin spinning={isLoading}>
          <Card size="small">
            <Calendar
              value={calendarValue}
              onSelect={handleCalendarSelect}
              onPanelChange={handleCalendarPanelChange}
              onChange={handleCalendarChange}
              cellRender={(date, info) => {
                if (info.type === 'date') return dateCellRender(date);
                return null;
              }}
              headerRender={({ value, onChange }) => {
                const cur = value;
                return (
                  <Row justify="end" style={{ padding: '8px 16px 4px' }}>
                    <Space>
                      <Select
                        value={cur.month() + 1}
                        onChange={(m) => {
                          const next = cur.clone().month(m - 1);
                          onChange(next);
                          handleCalendarChange(next);
                        }}
                        options={MONTH_OPTIONS}
                        style={{ width: 130 }}
                      />
                      <Select
                        value={cur.year()}
                        onChange={(y) => {
                          const next = cur.clone().year(y);
                          onChange(next);
                          handleCalendarChange(next);
                        }}
                        options={YEAR_OPTIONS}
                        style={{ width: 90 }}
                      />
                    </Space>
                  </Row>
                );
              }}
            />
          </Card>
        </Spin>
      )}

      {/* ── ROW STYLES ── */}
      <style>{`
        .row-overdue  td { background: #fff2f0 !important; }
        .row-overdue:hover td { background: #ffe7e4 !important; }
        .row-completed td { background: #f6ffed !important; }
        .row-completed:hover td { background: #eaffd6 !important; }
        .ant-picker-calendar-date-content { overflow: visible !important; }
      `}</style>

      <CreatePlanModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        defaultDate={modalDefaultDate}
      />
    </div>
  );
}
