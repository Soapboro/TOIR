import React, { useEffect, useState } from 'react';
import {
  Button, Col, DatePicker, Empty, Form, Input, message, Modal, Popconfirm, Row,
  Select, Space, Table, Tag, Typography,
} from 'antd';
import {
  DeleteOutlined, EditOutlined, PlusOutlined, ReloadOutlined, SearchOutlined,
} from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import useAuthStore from '../store/authStore';
import { equipmentApi } from '../services/requests';

const { Title, Text } = Typography;

const STATUS_OPTIONS = [
  { value: 'active', label: 'В эксплуатации', color: 'green' },
  { value: 'maintenance', label: 'На обслуживании', color: 'gold' },
  { value: 'repair', label: 'В ремонте', color: 'red' },
  { value: 'storage', label: 'На складе', color: 'blue' },
  { value: 'decommissioned', label: 'Списано', color: 'default' },
];

const statusMeta = Object.fromEntries(STATUS_OPTIONS.map((item) => [item.value, item]));

function toFormValues(equipment) {
  if (!equipment) return { status: 'active' };
  return {
    name: equipment.name,
    inventory_number: equipment.inventory_number,
    serial_number: equipment.serial_number,
    status: equipment.status || 'active',
    category: equipment.category,
    location: equipment.location,
    manufacturer: equipment.manufacturer,
    model: equipment.model,
    installation_date: equipment.installation_date ? dayjs(equipment.installation_date) : null,
    warranty_expiry_date: equipment.warranty_expiry_date ? dayjs(equipment.warranty_expiry_date) : null,
    notes: equipment.notes,
  };
}

function normalizeFormValues(values) {
  return {
    ...values,
    installation_date: values.installation_date ? values.installation_date.format('YYYY-MM-DD') : null,
    warranty_expiry_date: values.warranty_expiry_date ? values.warranty_expiry_date.format('YYYY-MM-DD') : null,
  };
}

function EquipmentModal({ open, equipment, onClose }) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const isEdit = Boolean(equipment);

  useEffect(() => {
    if (open) {
      form.setFieldsValue(toFormValues(equipment));
    }
  }, [equipment, form, open]);

  const createMutation = useMutation({
    mutationFn: (values) => equipmentApi.create(normalizeFormValues(values)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipment'] });
      message.success('Оборудование создано');
      form.resetFields();
      onClose();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (values) => equipmentApi.update(equipment.id, normalizeFormValues(values)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipment'] });
      message.success('Оборудование обновлено');
      form.resetFields();
      onClose();
    },
  });

  const handleFinish = (values) => {
    if (isEdit) {
      updateMutation.mutate(values);
    } else {
      createMutation.mutate(values);
    }
  };

  const pending = createMutation.isPending || updateMutation.isPending;

  return (
    <Modal
      title={isEdit ? 'Редактирование оборудования' : 'Новое оборудование'}
      open={open}
      onCancel={() => { form.resetFields(); onClose(); }}
      onOk={() => form.submit()}
      okText={isEdit ? 'Сохранить' : 'Создать'}
      cancelText="Отмена"
      confirmLoading={pending}
      width={720}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ status: 'active' }}
        onFinish={handleFinish}
        style={{ marginTop: 16 }}
      >
        <Form.Item
          name="name"
          label="Наименование"
          rules={[{ required: true, message: 'Введите наименование' }]}
        >
          <Input />
        </Form.Item>
        <Row gutter={12}>
          <Col span={12}>
            <Form.Item
              name="inventory_number"
              label="Инвентарный номер"
              rules={[{ required: true, message: 'Введите инвентарный номер' }]}
            >
              <Input />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="serial_number" label="Серийный номер">
              <Input />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={12}>
          <Col span={12}>
            <Form.Item name="status" label="Статус">
              <Select options={STATUS_OPTIONS.map(({ value, label }) => ({ value, label }))} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="category" label="Категория">
              <Input />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={12}>
          <Col span={12}>
            <Form.Item name="location" label="Расположение">
              <Input />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="manufacturer" label="Производитель">
              <Input />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={12}>
          <Col span={12}>
            <Form.Item name="model" label="Модель">
              <Input />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="installation_date" label="Дата ввода в эксплуатацию">
              <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
            </Form.Item>
          </Col>
        </Row>
        <Row gutter={12}>
          <Col span={12}>
            <Form.Item name="warranty_expiry_date" label="Дата окончания гарантии">
              <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
            </Form.Item>
          </Col>
          <Col span={12} />
        </Row>
        <Form.Item name="notes" label="Примечания">
          <Input.TextArea rows={3} />
        </Form.Item>
      </Form>
    </Modal>
  );
}

export default function EquipmentPage() {
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === 'admin';
  const queryClient = useQueryClient();

  const [filters, setFilters] = useState({ search: '', status: null });
  const [modalOpen, setModalOpen] = useState(false);
  const [editingEquipment, setEditingEquipment] = useState(null);

  const params = Object.fromEntries(
    Object.entries({ ...filters, search: filters.search || undefined }).filter(([, value]) => value != null),
  );

  const { data: equipment = [], isLoading, refetch } = useQuery({
    queryKey: ['equipment', params],
    queryFn: () => equipmentApi.list(params),
  });

  const deleteMutation = useMutation({
    mutationFn: equipmentApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipment'] });
      message.success('Оборудование удалено');
    },
    onError: () => {
      message.error('Не удалось удалить оборудование');
    },
  });

  const openCreate = () => {
    setEditingEquipment(null);
    setModalOpen(true);
  };

  const openEdit = (record) => {
    setEditingEquipment(record);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingEquipment(null);
  };

  const columns = [
    {
      title: 'Наименование',
      dataIndex: 'name',
      ellipsis: true,
      render: (name, row) => (
        <Space direction="vertical" size={0}>
          <Text strong>{name}</Text>
          <Text type="secondary">Инв. N {row.inventory_number}</Text>
        </Space>
      ),
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      width: 180,
      render: (status, row) => (
        <Tag color={statusMeta[status]?.color ?? 'default'}>
          {row.status_display || statusMeta[status]?.label || status}
        </Tag>
      ),
    },
    {
      title: 'Категория',
      dataIndex: 'category',
      ellipsis: true,
      render: (value) => value || <Text type="secondary">Не указана</Text>,
    },
    {
      title: 'Расположение',
      dataIndex: 'location',
      ellipsis: true,
      render: (value) => value || <Text type="secondary">Не указано</Text>,
    },
    {
      title: 'Ввод в эксплуатацию',
      dataIndex: 'installation_date',
      width: 180,
      render: (date) => (date ? dayjs(date).format('DD.MM.YYYY') : <Text type="secondary">Не указано</Text>),
    },
    ...(isAdmin ? [{
      title: '',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size={4}>
          <Button
            type="text"
            icon={<EditOutlined />}
            aria-label="Редактировать оборудование"
            onClick={() => openEdit(record)}
          />
          <Popconfirm
            title="Удалить оборудование?"
            description="Это действие нельзя отменить."
            okText="Удалить"
            cancelText="Отмена"
            okButtonProps={{ danger: true, loading: deleteMutation.isPending }}
            onConfirm={() => deleteMutation.mutate(record.id)}
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              aria-label="Удалить оборудование"
            />
          </Popconfirm>
        </Space>
      ),
    }] : []),
  ];

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Title level={4} style={{ margin: 0 }}>Оборудование</Title>
        </Col>
        <Col>
          {isAdmin && (
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
              Добавить оборудование
            </Button>
          )}
        </Col>
      </Row>

      <Row gutter={12} style={{ marginBottom: 16 }}>
        <Col flex="1">
          <Input
            placeholder="Поиск по наименованию, номеру, модели или расположению"
            prefix={<SearchOutlined />}
            value={filters.search}
            onChange={(event) => setFilters((prev) => ({ ...prev, search: event.target.value }))}
            allowClear
          />
        </Col>
        <Col>
          <Select
            placeholder="Статус"
            allowClear
            style={{ width: 200 }}
            options={STATUS_OPTIONS.map(({ value, label }) => ({ value, label }))}
            value={filters.status}
            onChange={(status) => setFilters((prev) => ({ ...prev, status: status ?? null }))}
          />
        </Col>
        <Col>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()} />
        </Col>
      </Row>

      <Table
        dataSource={equipment}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        locale={{ emptyText: <Empty description="Оборудование не найдено" /> }}
        pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (total) => `Всего: ${total}` }}
      />

      {isAdmin && (
        <EquipmentModal
          open={modalOpen}
          equipment={editingEquipment}
          onClose={closeModal}
        />
      )}
    </div>
  );
}
