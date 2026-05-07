import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert, Badge, Button, Calendar, Card, Col, ConfigProvider, DatePicker, Descriptions,
  Divider, Drawer, Form, Input, InputNumber, Modal, Popconfirm, Row, Select, Segmented,
  Space, Table, Tabs, Tag, Tooltip, Typography, message,
} from 'antd';
import {
  CalendarOutlined, CheckCircleOutlined, DeleteOutlined, EditOutlined, PlusOutlined, TableOutlined,
} from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import 'dayjs/locale/ru';
import locale from 'antd/locale/ru_RU';
import {
  equipmentApi,
  maintenanceApi,
  maintenanceRecordsApi,
  maintenanceSchedulesApi,
  regulationsApi,
} from '../services/maintenance';
import {
  MAINTENANCE_TYPE, PLAN_STATUS, STATUS_OPTIONS, TYPE_OPTIONS, resolveStatus,
} from '../components/maintenance/constants';
import CreatePlanModal from '../components/maintenance/CreatePlanModal';
import PlanStatusTag from '../components/maintenance/PlanStatusTag';
import useAuthStore from '../store/authStore';

dayjs.locale('ru');

const { Title, Text } = Typography;

const STATUS_ROW_BG = {
  planned: 'rgba(22,119,255,0.06)',
  in_progress: 'rgba(250,140,22,0.08)',
  completed: 'rgba(82,196,26,0.06)',
  overdue: 'rgba(255,77,79,0.08)',
  cancelled: 'transparent',
};

function getEquipmentLabel(plan) {
  if (plan.equipment_detail?.name) return plan.equipment_detail.name;
  if (plan.equipment_name) return plan.equipment_name;
  return `#${plan.equipment}`;
}

function getEquipmentInventory(plan) {
  return plan.equipment_detail?.inventory_number || plan.equipment_inventory || null;
}

function RegulationModal({ open, regulation, equipment, onClose }) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const isEdit = Boolean(regulation);

  useEffect(() => {
    if (!open) return;
    form.setFieldsValue({
      equipment: regulation?.equipment ?? null,
      maintenance_type: regulation?.maintenance_type ?? 'scheduled',
      interval_days: regulation?.interval_days ?? 30,
      description: regulation?.description ?? '',
    });
  }, [form, open, regulation]);

  const createMutation = useMutation({
    mutationFn: ({ equipment: equipmentId, ...values }) => regulationsApi.create(equipmentId, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance-regulations'] });
      form.resetFields();
      onClose();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (values) => regulationsApi.update(regulation.id, {
      maintenance_type: values.maintenance_type,
      interval_days: values.interval_days,
      description: values.description,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance-regulations'] });
      form.resetFields();
      onClose();
    },
  });

  const pending = createMutation.isPending || updateMutation.isPending;

  return (
    <Modal
      title={isEdit ? 'Редактирование регламента ТО' : 'Новый регламент ТО'}
      open={open}
      onCancel={() => { form.resetFields(); onClose(); }}
      onOk={() => form.submit()}
      okText={isEdit ? 'Сохранить' : 'Создать'}
      cancelText="Отмена"
      confirmLoading={pending}
      width={560}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={(values) => (isEdit ? updateMutation.mutate(values) : createMutation.mutate(values))}
      >
        <Form.Item
          name="equipment"
          label="Оборудование"
          rules={[{ required: true, message: 'Выберите оборудование' }]}
        >
          <Select
            showSearch
            disabled={isEdit}
            options={equipment.map((item) => ({
              value: item.id,
              label: `${item.name} [${item.inventory_number}]`,
            }))}
            filterOption={(input, option) => option.label.toLowerCase().includes(input.toLowerCase())}
          />
        </Form.Item>
        <Form.Item
          name="maintenance_type"
          label="Вид ТО"
          rules={[{ required: true, message: 'Выберите вид ТО' }]}
        >
          <Select options={TYPE_OPTIONS} />
        </Form.Item>
        <Form.Item
          name="interval_days"
          label="Периодичность, дней"
          rules={[{ required: true, message: 'Укажите периодичность' }]}
        >
          <InputNumber min={1} step={1} precision={0} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="description" label="Описание работ">
          <Input.TextArea rows={4} />
        </Form.Item>
      </Form>
    </Modal>
  );
}

export default function MaintenancePage() {
  const user = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const [form] = Form.useForm();
  const [messageApi, contextHolder] = message.useMessage();

  const [view, setView] = useState('table');
  const [createOpen, setCreateOpen] = useState(false);
  const [createDefaultDate, setCreateDefaultDate] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [completeOpen, setCompleteOpen] = useState(false);
  const [filterMonth, setFilterMonth] = useState(null);
  const [filterEquipment, setFilterEquipment] = useState(null);
  const [filterStatus, setFilterStatus] = useState(null);
  const [calendarValue, setCalendarValue] = useState(dayjs());
  const [activeTab, setActiveTab] = useState('plans');
  const [regulationOpen, setRegulationOpen] = useState(false);
  const [editingRegulation, setEditingRegulation] = useState(null);

  const canPlan = user?.role === 'manager';
  const canComplete = user?.role === 'admin' || user?.role === 'mechanic';
  const canManageRegulations = user?.role === 'admin' || user?.role === 'mechanic';
  const canUpdateSchedules = user?.role === 'manager';

  const { data: plans = [], isLoading } = useQuery({
    queryKey: ['maintenance-plans'],
    queryFn: () => maintenanceApi.list(),
  });

  const { data: equipment = [] } = useQuery({
    queryKey: ['equipment-list'],
    queryFn: () => equipmentApi.list(),
  });

  const { data: regulations = [], isLoading: regulationsLoading } = useQuery({
    queryKey: ['maintenance-regulations'],
    queryFn: () => regulationsApi.list(),
  });

  const { data: schedules = [], isLoading: schedulesLoading } = useQuery({
    queryKey: ['maintenance-schedules'],
    queryFn: () => maintenanceSchedulesApi.list(),
  });

  const { data: records = [], isLoading: recordsLoading } = useQuery({
    queryKey: ['maintenance-records'],
    queryFn: () => maintenanceRecordsApi.list(),
  });

  const completeMutation = useMutation({
    mutationFn: (values) => maintenanceRecordsApi.create({
      equipment: selectedPlan.equipment,
      plan: selectedPlan.id,
      maintenance_type: selectedPlan.maintenance_type,
      performed_at: values.performed_at.toISOString(),
      duration_hours: values.duration_hours,
      work_performed: values.work_performed,
      parts_replaced: values.parts_replaced || '',
      next_due_date: values.next_due_date ? values.next_due_date.format('YYYY-MM-DD') : null,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance-plans'] });
      form.resetFields();
      setCompleteOpen(false);
      setSelectedPlan(null);
      messageApi.success('ТО отмечено как выполненное');
    },
  });

  const deleteRegulationMutation = useMutation({
    mutationFn: regulationsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance-regulations'] });
      messageApi.success('Регламент удалён');
    },
  });

  const scheduleStatusMutation = useMutation({
    mutationFn: ({ id, status }) => maintenanceSchedulesApi.update(id, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance-schedules'] });
    },
  });

  const filtered = useMemo(() => {
    const activeMonth = view === 'calendar' ? calendarValue : filterMonth;
    return plans.filter((plan) => {
      const status = resolveStatus(plan);
      if (filterStatus && status !== filterStatus) return false;
      if (filterEquipment && plan.equipment !== filterEquipment) return false;
      if (activeMonth) {
        const scheduled = dayjs(plan.scheduled_date);
        if (scheduled.month() !== activeMonth.month() || scheduled.year() !== activeMonth.year()) {
          return false;
        }
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
      render: (value) => dayjs(value).format('DD.MM.YYYY'),
    },
    {
      title: 'Оборудование',
      key: 'equipment',
      render: (_, record) => getEquipmentLabel(record),
      ellipsis: true,
    },
    {
      title: 'Вид ТО',
      dataIndex: 'maintenance_type',
      render: (value) => MAINTENANCE_TYPE[value] ?? value,
    },
    {
      title: 'Трудоёмкость, ч',
      dataIndex: 'estimated_duration_hours',
      width: 140,
      align: 'center',
      render: (value) => value ?? '—',
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
      ellipsis: true,
      render: (value) => value || '—',
    },
    {
      title: '',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Button
          type="link"
          onClick={(event) => {
            event.stopPropagation();
            setSelectedPlan(record);
          }}
        >
          Открыть
        </Button>
      ),
    },
  ];

  const cellRender = (date, info) => {
    if (info.type !== 'date') return info.originNode;
    const dayPlans = plans.filter(
      (plan) =>
        (!filterEquipment || plan.equipment === filterEquipment)
        && (!filterStatus || resolveStatus(plan) === filterStatus)
        && dayjs(plan.scheduled_date).isSame(date, 'day'),
    );

    if (!dayPlans.length) return null;

    return (
      <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {dayPlans.slice(0, 3).map((plan) => {
          const status = resolveStatus(plan);
          const cfg = PLAN_STATUS[status] ?? { color: '#d9d9d9' };
          return (
            <li key={plan.id} style={{ marginBottom: 2 }}>
              <Tooltip title={`${getEquipmentLabel(plan)} — ${MAINTENANCE_TYPE[plan.maintenance_type] ?? plan.maintenance_type}`}>
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    setSelectedPlan(plan);
                  }}
                  style={{
                    border: 0,
                    padding: 0,
                    margin: 0,
                    background: 'transparent',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  <Badge
                    color={cfg.color}
                    text={<Text style={{ fontSize: 11, color: cfg.color, fontWeight: 500 }}>{getEquipmentLabel(plan)}</Text>}
                  />
                </button>
              </Tooltip>
            </li>
          );
        })}
        {dayPlans.length > 3 && (
          <li><Text type="secondary" style={{ fontSize: 11 }}>ещё {dayPlans.length - 3}...</Text></li>
        )}
      </ul>
    );
  };

  const openCreateModal = (date = null) => {
    if (!canPlan) return;
    setCreateDefaultDate(date);
    setCreateOpen(true);
  };

  const openCompleteForm = () => {
    form.setFieldsValue({
      performed_at: dayjs(),
      duration_hours: selectedPlan?.estimated_duration_hours
        ? Number(selectedPlan.estimated_duration_hours)
        : null,
      work_performed: selectedPlan?.notes || '',
      parts_replaced: '',
      next_due_date: null,
    });
    setCompleteOpen(true);
  };

  const closeSelectedPlan = () => {
    setSelectedPlan(null);
    setCompleteOpen(false);
    form.resetFields();
  };

  const openRegulationModal = (regulation = null) => {
    if (!canManageRegulations) return;
    setEditingRegulation(regulation);
    setRegulationOpen(true);
  };

  const closeRegulationModal = () => {
    setEditingRegulation(null);
    setRegulationOpen(false);
  };

  const regulationColumns = [
    {
      title: 'Оборудование',
      dataIndex: 'equipment_name',
      ellipsis: true,
      render: (value, row) => (
        <Space direction="vertical" size={0}>
          <Text strong>{value || `#${row.equipment}`}</Text>
          {row.equipment_inventory && <Text type="secondary">Инв. N {row.equipment_inventory}</Text>}
        </Space>
      ),
    },
    {
      title: 'Вид ТО',
      dataIndex: 'maintenance_type',
      width: 170,
      render: (value, row) => row.maintenance_type_display || MAINTENANCE_TYPE[value] || value,
    },
    {
      title: 'Периодичность',
      dataIndex: 'interval_days',
      width: 140,
      align: 'right',
      render: (value) => `${value} дн.`,
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      ellipsis: true,
      render: (value) => value || <Text type="secondary">Не указано</Text>,
    },
    ...(canManageRegulations ? [{
      title: '',
      key: 'actions',
      width: 110,
      render: (_, record) => (
        <Space size={4}>
          <Button
            type="text"
            icon={<EditOutlined />}
            aria-label="Редактировать регламент"
            onClick={() => openRegulationModal(record)}
          />
          <Popconfirm
            title="Удалить регламент?"
            okText="Удалить"
            cancelText="Отмена"
            okButtonProps={{ danger: true, loading: deleteRegulationMutation.isPending }}
            onConfirm={() => deleteRegulationMutation.mutate(record.id)}
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              aria-label="Удалить регламент"
            />
          </Popconfirm>
        </Space>
      ),
    }] : []),
  ];

  const scheduleColumns = [
    {
      title: 'Дата',
      dataIndex: 'scheduled_date',
      width: 120,
      sorter: (a, b) => dayjs(a.scheduled_date).unix() - dayjs(b.scheduled_date).unix(),
      render: (value) => dayjs(value).format('DD.MM.YYYY'),
    },
    {
      title: 'Оборудование',
      dataIndex: 'equipment_name',
      ellipsis: true,
      render: (value, row) => (
        <Space direction="vertical" size={0}>
          <Text strong>{value || `#${row.equipment}`}</Text>
          {row.equipment_inventory && <Text type="secondary">Инв. N {row.equipment_inventory}</Text>}
        </Space>
      ),
    },
    {
      title: 'Регламент',
      dataIndex: 'regulation_description',
      ellipsis: true,
      render: (value, row) => value || MAINTENANCE_TYPE[row.maintenance_type] || row.maintenance_type,
    },
    {
      title: 'Периодичность',
      dataIndex: 'interval_days',
      width: 130,
      align: 'right',
      render: (value) => (value ? `${value} дн.` : <Text type="secondary">-</Text>),
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      width: 180,
      render: (value, row) => canUpdateSchedules ? (
        <Select
          size="small"
          value={value}
          options={STATUS_OPTIONS}
          style={{ width: 150 }}
          onClick={(event) => event.stopPropagation()}
          onChange={(status) => scheduleStatusMutation.mutate({ id: row.id, status })}
        />
      ) : (
        <Tag color={PLAN_STATUS[value]?.color}>{row.status_display || PLAN_STATUS[value]?.label || value}</Tag>
      ),
    },
    {
      title: 'Примечания',
      dataIndex: 'notes',
      ellipsis: true,
      render: (value) => value || <Text type="secondary">Нет</Text>,
    },
  ];

  const recordColumns = [
    {
      title: 'Дата выполнения',
      dataIndex: 'performed_at',
      width: 170,
      sorter: (a, b) => dayjs(a.performed_at).unix() - dayjs(b.performed_at).unix(),
      defaultSortOrder: 'descend',
      render: (value) => dayjs(value).format('DD.MM.YYYY HH:mm'),
    },
    {
      title: 'Оборудование',
      dataIndex: 'equipment_name',
      ellipsis: true,
      render: (value, row) => (
        <Space direction="vertical" size={0}>
          <Text strong>{value || `#${row.equipment}`}</Text>
          {row.equipment_inventory && <Text type="secondary">Инв. N {row.equipment_inventory}</Text>}
        </Space>
      ),
    },
    {
      title: 'Вид ТО',
      dataIndex: 'maintenance_type',
      width: 160,
      render: (value, row) => row.maintenance_type_display || MAINTENANCE_TYPE[value] || value,
    },
    {
      title: 'Исполнитель',
      dataIndex: 'performed_by_name',
      width: 180,
      render: (value) => value || <Text type="secondary">Не указан</Text>,
    },
    {
      title: 'Трудоёмкость, ч',
      dataIndex: 'duration_hours',
      width: 140,
      align: 'right',
      render: (value) => value ?? <Text type="secondary">-</Text>,
    },
    {
      title: 'Следующее ТО',
      dataIndex: 'next_due_date',
      width: 130,
      render: (value) => (value ? dayjs(value).format('DD.MM.YYYY') : <Text type="secondary">-</Text>),
    },
  ];

  const selectedStatus = selectedPlan ? resolveStatus(selectedPlan) : null;
  const selectedInventory = selectedPlan ? getEquipmentInventory(selectedPlan) : null;
  const isAssignedToCurrentUser = selectedPlan?.assigned_to === user?.id;
  const selectedCanComplete = (
    selectedPlan
    && canComplete
    && isAssignedToCurrentUser
    && !['completed', 'cancelled'].includes(selectedPlan.status)
  );

  return (
    <ConfigProvider locale={locale}>
      <div style={{ padding: 24 }}>
        {contextHolder}

        <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
          <Col>
            <Title level={4} style={{ margin: 0 }}>Планирование ТО</Title>
          </Col>
          <Col>
            <Space>
              {activeTab === 'plans' && (
              <Segmented
                value={view}
                onChange={setView}
                options={[
                  { value: 'table', icon: <TableOutlined />, label: 'Таблица' },
                  { value: 'calendar', icon: <CalendarOutlined />, label: 'Календарь' },
                ]}
              />
              )}
              {activeTab === 'plans' && canPlan && (
                <Button type="primary" icon={<PlusOutlined />} onClick={() => openCreateModal()}>
                  Создать запись
                </Button>
              )}
              {activeTab === 'regulations' && canManageRegulations && (
                <Button type="primary" icon={<PlusOutlined />} onClick={() => openRegulationModal()}>
                  Новый регламент
                </Button>
              )}
            </Space>
          </Col>
        </Row>

        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            { key: 'plans', label: 'Планы ТО' },
            { key: 'regulations', label: 'Регламенты' },
            { key: 'schedules', label: 'Графики' },
            { key: 'history', label: 'История работ' },
          ]}
        />

        {activeTab === 'plans' && (
          <>
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
                  onChange={(date) => date && setCalendarValue(date)}
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
                options={equipment.map((item) => ({
                  value: item.id,
                  label: `${item.name} [${item.inventory_number}]`,
                }))}
                filterOption={(input, option) => option.label.toLowerCase().includes(input.toLowerCase())}
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

        {view === 'table' ? (
          <Table
            rowKey="id"
            dataSource={filtered}
            columns={columns}
            loading={isLoading}
            onRow={(record) => {
              const status = resolveStatus(record);
              return {
                onClick: () => setSelectedPlan(record),
                style: {
                  background: STATUS_ROW_BG[status] ?? 'transparent',
                  cursor: 'pointer',
                },
              };
            }}
            pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (total) => `Всего: ${total}` }}
            scroll={{ x: 800 }}
          />
        ) : (
          <Card>
            <Calendar
              value={calendarValue}
              onPanelChange={setCalendarValue}
              onSelect={(date) => canPlan && openCreateModal(date)}
              cellRender={cellRender}
            />
          </Card>
        )}
          </>
        )}

        {activeTab === 'regulations' && (
          <Table
            rowKey="id"
            dataSource={regulations}
            columns={regulationColumns}
            loading={regulationsLoading}
            pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (total) => `Всего: ${total}` }}
            scroll={{ x: 900 }}
          />
        )}

        {activeTab === 'schedules' && (
          <Table
            rowKey="id"
            dataSource={schedules}
            columns={scheduleColumns}
            loading={schedulesLoading}
            pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (total) => `Всего: ${total}` }}
            scroll={{ x: 900 }}
          />
        )}

        {activeTab === 'history' && (
          <Table
            rowKey="id"
            dataSource={records}
            columns={recordColumns}
            loading={recordsLoading}
            pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (total) => `Всего: ${total}` }}
            scroll={{ x: 900 }}
          />
        )}

        {canPlan && (
          <CreatePlanModal
            open={createOpen}
            onClose={() => {
              setCreateOpen(false);
              setCreateDefaultDate(null);
            }}
            defaultDate={createDefaultDate}
          />
        )}

        {canManageRegulations && (
          <RegulationModal
            open={regulationOpen}
            regulation={editingRegulation}
            equipment={equipment}
            onClose={closeRegulationModal}
          />
        )}

        <Drawer
          title={(
            selectedPlan ? (
              <Space wrap>
                <Text>{getEquipmentLabel(selectedPlan)}</Text>
                <PlanStatusTag plan={selectedPlan} />
              </Space>
            ) : 'План ТО'
          )}
          open={!!selectedPlan}
          onClose={closeSelectedPlan}
          width={620}
          styles={{ body: { paddingBottom: 80 } }}
          extra={selectedCanComplete && (
            <Button type="primary" icon={<CheckCircleOutlined />} onClick={openCompleteForm}>
              Выполнить
            </Button>
          )}
        >
          {selectedPlan && (
            <>
              <Descriptions column={2} size="small" style={{ marginBottom: 16 }}>
                <Descriptions.Item label="Дата">
                  {dayjs(selectedPlan.scheduled_date).format('DD.MM.YYYY')}
                </Descriptions.Item>
                <Descriptions.Item label="Вид ТО">
                  {MAINTENANCE_TYPE[selectedPlan.maintenance_type] ?? selectedPlan.maintenance_type}
                </Descriptions.Item>
                <Descriptions.Item label="Оборудование" span={2}>
                  {getEquipmentLabel(selectedPlan)}
                  {selectedInventory && <Text type="secondary"> [{selectedInventory}]</Text>}
                </Descriptions.Item>
                <Descriptions.Item label="Трудоёмкость">
                  {selectedPlan.estimated_duration_hours ?? '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Статус">
                  {PLAN_STATUS[selectedStatus]?.label ?? selectedStatus}
                </Descriptions.Item>
                <Descriptions.Item label="Ответственный" span={2}>
                  {selectedPlan.assigned_to_detail
                    ? selectedPlan.assigned_to_detail.full_name || selectedPlan.assigned_to_detail.email
                    : <Text type="secondary">Не назначен</Text>}
                </Descriptions.Item>
              </Descriptions>

              <Divider orientation="left" plain>Примечания</Divider>
              <Typography.Paragraph>
                {selectedPlan.notes || <Text type="secondary">Примечаний нет</Text>}
              </Typography.Paragraph>

              <Divider orientation="left" plain>Регламент</Divider>
              <Typography.Paragraph>
                {selectedPlan.regulation_description || <Text type="secondary">Регламент для этой работы не указан</Text>}
              </Typography.Paragraph>
              {selectedPlan.regulation_interval_days && (
                <Text type="secondary">Периодичность: {selectedPlan.regulation_interval_days} дн.</Text>
              )}

              {selectedPlan.status === 'completed' && (
                <Alert type="success" showIcon message="Этот план уже выполнен" />
              )}

              {!canComplete && !['completed', 'cancelled'].includes(selectedPlan.status) && (
                <Alert
                  type="info"
                  showIcon
                  message="Фиксировать выполнение может администратор или механик"
                />
              )}
              {canComplete && !isAssignedToCurrentUser && !['completed', 'cancelled'].includes(selectedPlan.status) && (
                <Alert
                  type="info"
                  showIcon
                  message="Отметить ТО выполненным может только назначенный исполнитель"
                />
              )}
            </>
          )}
        </Drawer>

        <Drawer
          title="Фиксация выполненного ТО"
          open={completeOpen}
          onClose={() => {
            setCompleteOpen(false);
            form.resetFields();
          }}
          width={520}
          destroyOnClose
        >
          <Form form={form} layout="vertical" onFinish={(values) => completeMutation.mutate(values)}>
            <Form.Item
              name="performed_at"
              label="Дата и время выполнения"
              rules={[{ required: true, message: 'Укажите дату и время' }]}
            >
              <DatePicker showTime format="DD.MM.YYYY HH:mm" style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="duration_hours" label="Фактическая трудоёмкость, ч">
              <InputNumber min={0} step={0.5} precision={1} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name="work_performed"
              label="Выполненные работы"
              rules={[{ required: true, message: 'Опишите выполненные работы' }]}
            >
              <Input.TextArea rows={4} />
            </Form.Item>
            <Form.Item name="parts_replaced" label="Заменённые детали и материалы">
              <Input.TextArea rows={3} />
            </Form.Item>
            <Form.Item name="next_due_date" label="Дата следующего ТО">
              <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
            </Form.Item>

            {completeMutation.isError && (
              <Alert
                type="error"
                showIcon
                message="Не удалось зафиксировать выполнение"
                style={{ marginBottom: 16 }}
              />
            )}

            <Space>
              <Button type="primary" htmlType="submit" loading={completeMutation.isPending}>
                Сохранить и завершить
              </Button>
              <Button onClick={() => setCompleteOpen(false)}>Отмена</Button>
            </Space>
          </Form>
        </Drawer>
      </div>
    </ConfigProvider>
  );
}
