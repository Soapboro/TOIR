import React from 'react';
import {
  Alert, Badge, Button, Card, Col, Empty, List, Progress, Row, Skeleton, Space,
  Statistic, Table, Tag, Typography,
} from 'antd';
import {
  CalendarOutlined, CheckCircleOutlined, ClockCircleOutlined, FileTextOutlined,
  ToolOutlined, UserSwitchOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import dayjs from 'dayjs';
import useAuthStore from '../store/authStore';
import { analyticsApi } from '../services/analytics';
import { requestsApi } from '../services/requests';
import { maintenanceApi } from '../services/maintenance';
import PriorityTag from '../components/requests/PriorityTag';
import StatusBadge from '../components/requests/StatusBadge';
import PlanStatusTag from '../components/maintenance/PlanStatusTag';
import { MAINTENANCE_TYPE, resolveStatus } from '../components/maintenance/constants';

const { Title, Text } = Typography;

const EQUIPMENT_STATUS_LABELS = {
  active: 'В эксплуатации',
  maintenance: 'На обслуживании',
  repair: 'В ремонте',
  storage: 'На складе',
  decommissioned: 'Списано',
};

const EQUIPMENT_STATUS_COLORS = {
  active: 'green',
  maintenance: 'gold',
  repair: 'red',
  storage: 'blue',
  decommissioned: 'default',
};

const ROLE_COPY = {
  admin: {
    title: 'Административный дашборд',
    subtitle: 'Контроль заявок, назначения работ и состояния парка оборудования.',
  },
  manager: {
    title: 'Дашборд менеджера',
    subtitle: 'Здесь собраны работы, которым нужен ответственный, и текущая нагрузка.',
  },
  mechanic: {
    title: 'Дашборд исполнителя',
    subtitle: 'Ваши активные заявки и назначенные работы ТО.',
  },
  operator: {
    title: 'Дашборд оператора',
    subtitle: 'Ваши открытые заявки и состояние оборудования.',
  },
};

const isOpenRequest = (request) => !['completed', 'closed', 'cancelled'].includes(request.status);
const isActiveMaintenance = (plan) => !['completed', 'cancelled'].includes(plan.status);

function formatDate(date) {
  return date ? dayjs(date).format('DD.MM.YYYY') : 'Не указано';
}

function getEquipmentLabel(plan) {
  if (plan.equipment_detail?.name) return plan.equipment_detail.name;
  if (plan.equipment_name) return plan.equipment_name;
  return `#${plan.equipment}`;
}

function TaskCard({ title, icon, count, children, actionTo, actionText, loading }) {
  return (
    <Card
      title={(
        <Space>
          {icon}
          <span>{title}</span>
          <Badge count={count} showZero style={{ backgroundColor: count ? '#1677ff' : '#bfbfbf' }} />
        </Space>
      )}
      extra={actionTo && <Link to={actionTo}>{actionText}</Link>}
      styles={{ body: { padding: 0 } }}
    >
      {loading ? (
        <div style={{ padding: 16 }}>
          <Skeleton active paragraph={{ rows: 4 }} />
        </div>
      ) : children}
    </Card>
  );
}

function RequestList({ requests, emptyText }) {
  if (!requests.length) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={emptyText} style={{ padding: 24 }} />;
  }

  return (
    <List
      dataSource={requests.slice(0, 6)}
      renderItem={(request) => (
        <List.Item style={{ padding: '12px 16px' }}>
          <List.Item.Meta
            title={(
              <Space wrap size={8}>
                <Link to="/requests">#{request.id} {request.title}</Link>
                <PriorityTag priority={request.priority} />
                <StatusBadge status={request.status} />
              </Space>
            )}
            description={(
              <Space wrap size={12}>
                <Text type="secondary">{request.equipment_name || 'Оборудование не указано'}</Text>
                <Text type="secondary">{formatDate(request.created_at)}</Text>
                {request.assigned_to_name && <Text type="secondary">{request.assigned_to_name}</Text>}
              </Space>
            )}
          />
        </List.Item>
      )}
    />
  );
}

function MaintenanceList({ plans, emptyText }) {
  if (!plans.length) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={emptyText} style={{ padding: 24 }} />;
  }

  return (
    <List
      dataSource={plans.slice(0, 6)}
      renderItem={(plan) => (
        <List.Item style={{ padding: '12px 16px' }}>
          <List.Item.Meta
            title={(
              <Space wrap size={8}>
                <Link to="/maintenance">{getEquipmentLabel(plan)}</Link>
                <PlanStatusTag plan={plan} />
              </Space>
            )}
            description={(
              <Space wrap size={12}>
                <Text type="secondary">{MAINTENANCE_TYPE[plan.maintenance_type] || plan.maintenance_type}</Text>
                <Text type={resolveStatus(plan) === 'overdue' ? 'danger' : 'secondary'}>
                  {formatDate(plan.scheduled_date)}
                </Text>
                {plan.assigned_to_detail && (
                  <Text type="secondary">
                    {plan.assigned_to_detail.full_name || plan.assigned_to_detail.email}
                  </Text>
                )}
              </Space>
            )}
          />
        </List.Item>
      )}
    />
  );
}

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const role = user?.role || 'operator';
  const canAssignRequests = role === 'manager' || role === 'admin';
  const canPlanMaintenance = role === 'manager';
  const isExecutor = role === 'mechanic' || role === 'admin';
  const roleCopy = ROLE_COPY[role] || ROLE_COPY.operator;

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: analyticsApi.summary,
  });

  const { data: planFact, isLoading: planFactLoading } = useQuery({
    queryKey: ['dashboard-plan-fact'],
    queryFn: analyticsApi.planFact,
  });

  const { data: requests = [], isLoading: requestsLoading } = useQuery({
    queryKey: ['dashboard-requests'],
    queryFn: () => requestsApi.list(),
  });

  const { data: plans = [], isLoading: plansLoading } = useQuery({
    queryKey: ['dashboard-maintenance-plans'],
    queryFn: () => maintenanceApi.list(),
  });

  const openRequests = requests.filter(isOpenRequest);
  const assignedRequests = openRequests.filter((request) => request.assigned_to === user?.id);
  const ownRequests = openRequests.filter((request) => request.created_by === user?.id);
  const requestsToAssign = openRequests.filter((request) => !request.assigned_to && request.status === 'new');
  const availableRequests = role === 'mechanic' ? requestsToAssign : [];

  const activePlans = plans.filter(isActiveMaintenance);
  const assignedPlans = activePlans
    .filter((plan) => plan.assigned_to === user?.id)
    .sort((a, b) => dayjs(a.scheduled_date).unix() - dayjs(b.scheduled_date).unix());
  const plansToAssign = activePlans
    .filter((plan) => !plan.assigned_to && ['planned', 'overdue'].includes(resolveStatus(plan)))
    .sort((a, b) => dayjs(a.scheduled_date).unix() - dayjs(b.scheduled_date).unix());
  const overduePlans = activePlans.filter((plan) => resolveStatus(plan) === 'overdue');

  const equipmentTotal = summary?.equipment?.total ?? 0;
  const equipmentStatuses = Object.entries(summary?.equipment?.by_status || {});
  const maintenanceTotals = planFact?.totals || {};
  const completionPercent = maintenanceTotals.completion_percent ?? 0;
  const onTimePercent = maintenanceTotals.on_time_percent ?? 0;

  const equipmentColumns = [
    {
      title: 'Статус',
      dataIndex: 'status',
      render: (status) => (
        <Tag color={EQUIPMENT_STATUS_COLORS[status] || 'default'}>
          {EQUIPMENT_STATUS_LABELS[status] || status}
        </Tag>
      ),
    },
    {
      title: 'Количество',
      dataIndex: 'count',
      width: 120,
      align: 'right',
    },
  ];

  const equipmentRows = equipmentStatuses.map(([status, count]) => ({ status, count }));

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Title level={4} style={{ margin: 0 }}>{roleCopy.title}</Title>
          <Text type="secondary">{roleCopy.subtitle}</Text>
        </Col>
        <Col>
          <Space>
            <Button icon={<FileTextOutlined />} href="/requests">Заявки</Button>
            <Button icon={<CalendarOutlined />} href="/maintenance">ТО</Button>
          </Space>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              loading={summaryLoading}
              title="Оборудование"
              value={equipmentTotal}
              prefix={<ToolOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              loading={summaryLoading}
              title="Открытые заявки"
              value={summary?.open_requests ?? 0}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              loading={summaryLoading}
              title="ТО на неделе"
              value={summary?.maintenance?.this_week ?? 0}
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              loading={summaryLoading}
              title="Просрочено ТО"
              value={summary?.maintenance?.overdue ?? 0}
              valueStyle={{ color: (summary?.maintenance?.overdue ?? 0) ? '#cf1322' : undefined }}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        {isExecutor && (
          <>
            <Col xs={24} lg={12}>
              <TaskCard
                title="Мои заявки в работе"
                icon={<CheckCircleOutlined />}
                count={assignedRequests.length}
                actionTo="/requests"
                actionText="Открыть заявки"
                loading={requestsLoading}
              >
                <RequestList requests={assignedRequests} emptyText="Назначенных заявок нет" />
              </TaskCard>
            </Col>
            {role === 'mechanic' && (
              <Col xs={24} lg={12}>
                <TaskCard
                  title="Можно взять в работу"
                  icon={<FileTextOutlined />}
                  count={availableRequests.length}
                  actionTo="/requests"
                  actionText="Открыть заявки"
                  loading={requestsLoading}
                >
                  <RequestList requests={availableRequests} emptyText="Нет свободных заявок" />
                </TaskCard>
              </Col>
            )}
            <Col xs={24} lg={12}>
              <TaskCard
                title="Мои работы ТО"
                icon={<CalendarOutlined />}
                count={assignedPlans.length}
                actionTo="/maintenance"
                actionText="Открыть ТО"
                loading={plansLoading}
              >
                <MaintenanceList plans={assignedPlans} emptyText="Назначенных работ ТО нет" />
              </TaskCard>
            </Col>
          </>
        )}

        {canAssignRequests && (
          <>
            <Col xs={24} lg={12}>
              <TaskCard
                title="Заявки нужно назначить"
                icon={<UserSwitchOutlined />}
                count={requestsToAssign.length}
                actionTo="/requests"
                actionText="Назначить"
                loading={requestsLoading}
              >
                <RequestList requests={requestsToAssign} emptyText="Нет заявок без исполнителя" />
              </TaskCard>
            </Col>
          </>
        )}

        {canPlanMaintenance && (
          <>
            <Col xs={24} lg={12}>
              <TaskCard
                title="ТО нужно назначить"
                icon={<UserSwitchOutlined />}
                count={plansToAssign.length}
                actionTo="/maintenance"
                actionText="Назначить"
                loading={plansLoading}
              >
                <MaintenanceList plans={plansToAssign} emptyText="Нет работ ТО без ответственного" />
              </TaskCard>
            </Col>
          </>
        )}

        {!isExecutor && !canAssignRequests && (
          <Col xs={24}>
            <TaskCard
              title="Мои открытые заявки"
              icon={<FileTextOutlined />}
              count={ownRequests.length}
              actionTo="/requests"
              actionText="Открыть заявки"
              loading={requestsLoading}
            >
              <RequestList requests={ownRequests} emptyText="У вас нет открытых заявок" />
            </TaskCard>
          </Col>
        )}
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <Card title="Статусы оборудования">
            <Table
              dataSource={equipmentRows}
              columns={equipmentColumns}
              rowKey="status"
              pagination={false}
              loading={summaryLoading}
              locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Нет данных" /> }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Выполнение ТО">
            {planFactLoading ? (
              <Skeleton active paragraph={{ rows: 4 }} />
            ) : (
              <Space direction="vertical" style={{ width: '100%' }} size={16}>
                <div>
                  <Text type="secondary">План-факт</Text>
                  <Progress percent={Math.round(completionPercent)} status="active" />
                </div>
                <div>
                  <Text type="secondary">В срок</Text>
                  <Progress percent={Math.round(onTimePercent)} strokeColor="#52c41a" />
                </div>
                <Row gutter={12}>
                  <Col span={12}>
                    <Statistic title="Выполнено" value={maintenanceTotals.completed ?? 0} />
                  </Col>
                  <Col span={12}>
                    <Statistic title="В работе" value={maintenanceTotals.in_progress ?? 0} />
                  </Col>
                </Row>
              </Space>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Риски ТО">
            {plansLoading ? (
              <Skeleton active paragraph={{ rows: 4 }} />
            ) : overduePlans.length ? (
              <MaintenanceList plans={overduePlans} emptyText="" />
            ) : (
              <Alert type="success" showIcon message="Просроченных работ ТО нет" />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
}
