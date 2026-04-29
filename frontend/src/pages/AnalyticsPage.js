import React, { useState } from 'react';
import {
  Row, Col, Card, Statistic, Table, Tag, Tooltip,
  Select, Typography, Space, Spin, Empty, Badge, Progress,
} from 'antd';
import {
  ToolOutlined, AlertOutlined, ClockCircleOutlined,
  ExclamationCircleOutlined, BarChartOutlined,
} from '@ant-design/icons';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip as RechartTooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { analyticsApi } from '../services/analytics';
import { MAINTENANCE_TYPE } from '../components/maintenance/constants';

const { Title, Text } = Typography;

/* ── urgency helpers ─────────────────────────────────────────────────────── */

function urgencyConfig(days) {
  if (days === null || days === undefined) return { color: '#d9d9d9', label: 'Нет данных',  bg: '#fafafa' };
  if (days <= 7)  return { color: '#ff4d4f', label: 'Критично',   bg: '#fff2f0' };
  if (days <= 30) return { color: '#fa8c16', label: 'Высокая',    bg: '#fff7e6' };
  if (days <= 90) return { color: '#fadb14', label: 'Средняя',    bg: '#feffe6' };
  return           { color: '#52c41a', label: 'Низкая',     bg: '#f6ffed' };
}

function UrgencyTag({ days }) {
  const cfg = urgencyConfig(days);
  return (
    <Tag style={{ background: cfg.color, color: days === null ? '#595959' : '#fff', border: 'none', fontWeight: 600, minWidth: 82, textAlign: 'center' }}>
      {cfg.label}
    </Tag>
  );
}

/* ── stat widget ─────────────────────────────────────────────────────────── */

function StatCard({ title, value, icon, color, suffix, loading }) {
  return (
    <Card
      bordered={false}
      style={{ borderLeft: `4px solid ${color}`, height: '100%' }}
      styles={{ body: { padding: '16px 20px' } }}
    >
      <Spin spinning={!!loading}>
        <Space>
          <div style={{ fontSize: 28, color, lineHeight: 1 }}>{icon}</div>
          <Statistic
            title={<Text type="secondary" style={{ fontSize: 13 }}>{title}</Text>}
            value={value ?? '—'}
            suffix={suffix}
            valueStyle={{ fontSize: 28, fontWeight: 700, color }}
          />
        </Space>
      </Spin>
    </Card>
  );
}

/* ── custom recharts tooltip ─────────────────────────────────────────────── */

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#fff', border: '1px solid #f0f0f0', borderRadius: 8, padding: '8px 14px', boxShadow: '0 2px 8px rgba(0,0,0,.1)' }}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} style={{ color: p.color, fontSize: 13 }}>
          {p.name}: <b>{p.value}</b>
        </div>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════ */

export default function AnalyticsPage() {
  const [trendYear, setTrendYear] = useState(dayjs().year());

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: analyticsApi.summary,
    staleTime: 60_000,
  });

  const { data: trend = [], isLoading: trendLoading } = useQuery({
    queryKey: ['analytics-trend', trendYear],
    queryFn: () => analyticsApi.requestsTrend(trendYear),
    staleTime: 60_000,
  });

  const { data: predictions = [], isLoading: predLoading } = useQuery({
    queryKey: ['analytics-predictions'],
    queryFn: analyticsApi.predictions,
    staleTime: 60_000,
  });

  const { data: equipStats = [], isLoading: statsLoading } = useQuery({
    queryKey: ['analytics-equipment-stats'],
    queryFn: analyticsApi.equipmentStats,
    staleTime: 60_000,
  });

  const { data: planFact, isLoading: planFactLoading } = useQuery({
    queryKey: ['analytics-plan-fact'],
    queryFn: analyticsApi.planFact,
    staleTime: 60_000,
  });

  const yearOptions = [-2, -1, 0, 1].map((d) => {
    const y = dayjs().year() + d;
    return { value: y, label: String(y) };
  });

  /* ── predictions table columns ──────────────────────────────────────────── */
  const predColumns = [
    {
      title: 'Оборудование',
      dataIndex: 'equipment_name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: 'Срочность',
      key: 'urgency',
      width: 110,
      sorter: (a, b) => {
        const da = a.days_until_failure ?? 999999;
        const db = b.days_until_failure ?? 999999;
        return da - db;
      },
      defaultSortOrder: 'ascend',
      render: (_, r) => <UrgencyTag days={r.days_until_failure} />,
    },
    {
      title: 'Дней до отказа',
      dataIndex: 'days_until_failure',
      key: 'days',
      width: 130,
      align: 'right',
      render: (v) => (v != null ? <b style={{ color: urgencyConfig(v).color }}>{v}</b> : <Text type="secondary">—</Text>),
    },
    {
      title: 'Прогноз отказа',
      dataIndex: 'predicted_failure_date',
      key: 'pred_date',
      width: 135,
      render: (v) => (v ? dayjs(v).format('DD.MM.YYYY') : <Text type="secondary">—</Text>),
    },
    {
      title: 'MTBF, ч',
      dataIndex: 'mtbf_hours',
      key: 'mtbf',
      width: 100,
      align: 'right',
      render: (v) => (v != null ? Number(v).toFixed(0) : <Text type="secondary">—</Text>),
    },
    {
      title: 'Отказов',
      dataIndex: 'failure_count',
      key: 'failures',
      width: 85,
      align: 'right',
    },
    {
      title: 'Основание',
      dataIndex: 'reason',
      key: 'reason',
      ellipsis: true,
      render: (v) => v ? <Text type="secondary" style={{ fontSize: 12 }}>{v}</Text> : null,
    },
  ];

  /* ── equipment stats table columns ─────────────────────────────────────── */
  const statsColumns = [
    {
      title: 'Оборудование',
      dataIndex: 'equipment_name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: 'Инв. №',
      dataIndex: 'inventory_number',
      key: 'inv',
      width: 120,
    },
    {
      title: 'Ремонтов',
      dataIndex: 'repair_count',
      key: 'repairs',
      width: 90,
      align: 'right',
      sorter: (a, b) => a.repair_count - b.repair_count,
      defaultSortOrder: 'descend',
      render: (v) => (
        <Badge
          count={v}
          showZero
          style={{
            backgroundColor: v === 0 ? '#d9d9d9' : v >= 5 ? '#ff4d4f' : v >= 3 ? '#fa8c16' : '#1677ff',
          }}
        />
      ),
    },
    {
      title: 'MTBF, ч',
      dataIndex: 'mtbf_hours',
      key: 'mtbf',
      width: 100,
      align: 'right',
      sorter: (a, b) => (a.mtbf_hours ?? -1) - (b.mtbf_hours ?? -1),
      render: (v) => (v != null
        ? <span style={{ color: v < 168 ? '#ff4d4f' : v < 720 ? '#fa8c16' : '#52c41a', fontWeight: 600 }}>{v.toFixed(0)}</span>
        : <Text type="secondary">—</Text>
      ),
    },
    {
      title: 'Последнее ТО',
      dataIndex: 'last_maintenance_at',
      key: 'last_maint',
      width: 135,
      render: (v, r) => {
        if (!v) return <Text type="secondary">—</Text>;
        const label = MAINTENANCE_TYPE[r.last_maintenance_type] ?? r.last_maintenance_type ?? '';
        return (
          <Tooltip title={label}>
            <span>{dayjs(v).format('DD.MM.YYYY')}</span>
          </Tooltip>
        );
      },
    },
  ];

  const planFactTypeColumns = [
    {
      title: 'Вид ТО',
      dataIndex: 'maintenance_type',
      key: 'type',
      render: (v) => MAINTENANCE_TYPE[v] ?? v,
    },
    {
      title: 'План',
      dataIndex: 'planned',
      key: 'planned',
      width: 80,
      align: 'right',
    },
    {
      title: 'Факт',
      dataIndex: 'completed',
      key: 'completed',
      width: 80,
      align: 'right',
    },
    {
      title: 'Просрочено',
      dataIndex: 'overdue',
      key: 'overdue',
      width: 110,
      align: 'right',
      render: (v) => <Badge count={v} showZero style={{ backgroundColor: v ? '#ff4d4f' : '#d9d9d9' }} />,
    },
    {
      title: 'Выполнение',
      dataIndex: 'completion_percent',
      key: 'completion',
      width: 150,
      render: (v) => <Progress percent={Math.round(v)} size="small" />,
    },
  ];

  /* ── render ─────────────────────────────────────────────────────────────── */

  return (
    <div style={{ padding: 24 }}>
      {/* header */}
      <Space align="center" style={{ marginBottom: 20 }}>
        <BarChartOutlined style={{ fontSize: 22, color: '#1677ff' }} />
        <Title level={4} style={{ margin: 0 }}>Аналитика</Title>
      </Space>

      {/* ── STAT WIDGETS ── */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="Всего оборудования"
            value={summary?.equipment?.total}
            icon={<ToolOutlined />}
            color="#1677ff"
            loading={summaryLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="Открытых заявок"
            value={summary?.open_requests}
            icon={<AlertOutlined />}
            color="#fa8c16"
            loading={summaryLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="ТО на этой неделе"
            value={summary?.maintenance?.this_week}
            icon={<ClockCircleOutlined />}
            color="#13c2c2"
            loading={summaryLoading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="Просроченных ТО"
            value={summary?.maintenance?.overdue}
            icon={<ExclamationCircleOutlined />}
            color="#ff4d4f"
            loading={summaryLoading}
          />
        </Col>
      </Row>

      {/* ── LINE CHART ── */}
      <Card
        title={
          <Space>
            <span>Динамика заявок по месяцам</span>
            <Select
              value={trendYear}
              onChange={setTrendYear}
              options={yearOptions}
              size="small"
              style={{ width: 90 }}
            />
          </Space>
        }
        bordered={false}
        style={{ marginBottom: 24, boxShadow: '0 1px 4px rgba(0,0,0,.08)' }}
      >
        <Spin spinning={trendLoading}>
          {trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={trend} margin={{ top: 8, right: 24, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="month_label"
                  tick={{ fontSize: 13 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fontSize: 12 }}
                  axisLine={false}
                  tickLine={false}
                  width={30}
                />
                <RechartTooltip content={<ChartTooltip />} />
                <Legend wrapperStyle={{ paddingTop: 12, fontSize: 13 }} />
                <Line
                  type="monotone"
                  dataKey="new"
                  name="Новые заявки"
                  stroke="#1677ff"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#1677ff' }}
                  activeDot={{ r: 5 }}
                />
                <Line
                  type="monotone"
                  dataKey="completed"
                  name="Закрытые заявки"
                  stroke="#52c41a"
                  strokeWidth={2.5}
                  strokeDasharray="5 3"
                  dot={{ r: 3, fill: '#52c41a' }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <Empty description="Нет данных за выбранный год" style={{ padding: 40 }} />
          )}
        </Spin>
      </Card>

      {/* ── PREDICTIONS + EQUIPMENT STATS ── */}
      <Card
        title="План/факт выполнения ТО"
        bordered={false}
        style={{ marginBottom: 24, boxShadow: '0 1px 4px rgba(0,0,0,.08)' }}
      >
        <Spin spinning={planFactLoading}>
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={24} md={6}>
              <Statistic
                title="План"
                value={planFact?.totals?.planned_for_execution ?? 0}
                suffix={`из ${planFact?.totals?.planned_total ?? 0}`}
              />
            </Col>
            <Col xs={24} md={6}>
              <Statistic
                title="Факт"
                value={planFact?.totals?.completed ?? 0}
                suffix={`${planFact?.totals?.completion_percent ?? 0}%`}
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col xs={24} md={6}>
              <Statistic
                title="Вовремя"
                value={planFact?.totals?.completed_on_time ?? 0}
                suffix={`${planFact?.totals?.on_time_percent ?? 0}%`}
                valueStyle={{ color: '#1677ff' }}
              />
            </Col>
            <Col xs={24} md={6}>
              <Statistic
                title="Просрочено"
                value={planFact?.totals?.overdue ?? 0}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Col>
          </Row>
          <Progress
            percent={Math.round(planFact?.totals?.completion_percent ?? 0)}
            style={{ marginBottom: 16 }}
          />
          <Table
            rowKey="maintenance_type"
            columns={planFactTypeColumns}
            dataSource={planFact?.by_type ?? []}
            size="small"
            pagination={false}
            locale={{ emptyText: <Empty description="Нет данных за текущий период" /> }}
          />
        </Spin>
      </Card>

      <Row gutter={[16, 16]}>
        {/* Predictions table */}
        <Col xs={24} xl={14}>
          <Card
            title={
              <Space>
                <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
                <span>Прогнозы неисправностей</span>
              </Space>
            }
            bordered={false}
            style={{ boxShadow: '0 1px 4px rgba(0,0,0,.08)', height: '100%' }}
            styles={{ body: { padding: 0 } }}
          >
            <Spin spinning={predLoading}>
              <Table
                rowKey="equipment_id"
                columns={predColumns}
                dataSource={predictions}
                size="small"
                pagination={{ pageSize: 8, size: 'small', showTotal: (t) => `${t} единиц` }}
                locale={{ emptyText: <Empty description="Нет данных" /> }}
                rowClassName={(r) => {
                  const d = r.days_until_failure;
                  if (d === null || d === undefined) return '';
                  if (d <= 7)  return 'row-critical';
                  if (d <= 30) return 'row-high';
                  if (d <= 90) return 'row-medium';
                  return '';
                }}
              />
            </Spin>
          </Card>
        </Col>

        {/* Equipment stats table */}
        <Col xs={24} xl={10}>
          <Card
            title={
              <Space>
                <ToolOutlined style={{ color: '#1677ff' }} />
                <span>Статистика по оборудованию</span>
              </Space>
            }
            bordered={false}
            style={{ boxShadow: '0 1px 4px rgba(0,0,0,.08)', height: '100%' }}
            styles={{ body: { padding: 0 } }}
          >
            <Spin spinning={statsLoading}>
              <Table
                rowKey="equipment_id"
                columns={statsColumns}
                dataSource={equipStats}
                size="small"
                pagination={{ pageSize: 8, size: 'small', showTotal: (t) => `${t} единиц` }}
                locale={{ emptyText: <Empty description="Нет данных" /> }}
              />
            </Spin>
          </Card>
        </Col>
      </Row>

      {/* row styles for predictions */}
      <style>{`
        .row-critical td { background: #fff2f0 !important; }
        .row-critical:hover td { background: #ffe7e4 !important; }
        .row-high td { background: #fff7e6 !important; }
        .row-high:hover td { background: #ffefd1 !important; }
        .row-medium td { background: #feffe6 !important; }
        .row-medium:hover td { background: #f5ffd0 !important; }
      `}</style>
    </div>
  );
}
