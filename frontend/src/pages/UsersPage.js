import React, { useEffect, useState } from 'react';
import {
  Button, Col, Empty, Form, Input, message, Modal, Popconfirm, Row, Select,
  Space, Switch, Table, Tag, Typography,
} from 'antd';
import {
  DeleteOutlined, EditOutlined, PlusOutlined, ReloadOutlined, SearchOutlined,
} from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import useAuthStore from '../store/authStore';
import { usersApi } from '../services/requests';

const { Title, Text } = Typography;

const ROLE_OPTIONS = [
  { value: 'admin', label: 'Администратор', color: 'red' },
  { value: 'manager', label: 'Менеджер', color: 'blue' },
  { value: 'mechanic', label: 'Механик', color: 'gold' },
  { value: 'operator', label: 'Оператор', color: 'green' },
];

const roleMeta = Object.fromEntries(ROLE_OPTIONS.map((item) => [item.value, item]));

function UserModal({ open, user, onClose }) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const isEdit = Boolean(user);

  const { data: userDetail } = useQuery({
    queryKey: ['user-detail', user?.id],
    queryFn: () => usersApi.detail(user.id),
    enabled: open && isEdit,
  });

  useEffect(() => {
    if (!open) return;
    if (isEdit) {
      const source = userDetail || user;
      form.setFieldsValue({
        full_name: source.full_name,
        first_name: source.first_name,
        last_name: source.last_name,
        role: source.role,
        phone: source.phone,
        department: source.department,
        is_active: source.is_active,
      });
    } else {
      form.setFieldsValue({ role: 'operator', is_active: true });
    }
  }, [form, isEdit, open, user, userDetail]);

  const createMutation = useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['users-active'] });
      message.success('Пользователь создан');
      form.resetFields();
      onClose();
    },
  });

  const updateMutation = useMutation({
    mutationFn: (values) => usersApi.update(user.id, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['users-active'] });
      queryClient.invalidateQueries({ queryKey: ['user-detail', user?.id] });
      message.success('Пользователь обновлён');
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
      title={isEdit ? 'Редактирование пользователя' : 'Новый пользователь'}
      open={open}
      onCancel={() => { form.resetFields(); onClose(); }}
      onOk={() => form.submit()}
      okText={isEdit ? 'Сохранить' : 'Создать'}
      cancelText="Отмена"
      confirmLoading={pending}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ role: 'operator', is_active: true }}
        onFinish={handleFinish}
        style={{ marginTop: 16 }}
      >
        {!isEdit && (
          <>
            <Form.Item
              name="email"
              label="Email"
              rules={[{ required: true, type: 'email', message: 'Введите email' }]}
            >
              <Input />
            </Form.Item>
            <Form.Item
              name="username"
              label="Логин"
              rules={[{ required: true, message: 'Введите логин' }]}
            >
              <Input />
            </Form.Item>
            <Form.Item
              name="password"
              label="Пароль"
              rules={[{ required: true, min: 8, message: 'Минимум 8 символов' }]}
            >
              <Input.Password />
            </Form.Item>
          </>
        )}

        {isEdit && (
          <Space direction="vertical" size={0} style={{ marginBottom: 16 }}>
            <Text strong>{userDetail?.email || user.email}</Text>
            <Text type="secondary">Email и логин не изменяются в этой форме</Text>
          </Space>
        )}

        <Row gutter={12}>
          <Col span={12}>
            <Form.Item name="full_name" label="ФИО">
              <Input />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="role" label="Роль">
              <Select options={ROLE_OPTIONS.map(({ value, label }) => ({ value, label }))} />
            </Form.Item>
          </Col>
        </Row>
        {isEdit && (
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="first_name" label="Имя">
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="last_name" label="Фамилия">
                <Input />
              </Form.Item>
            </Col>
          </Row>
        )}
        <Row gutter={12}>
          <Col span={12}>
            <Form.Item name="department" label="Подразделение">
              <Input />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="phone" label="Телефон">
              <Input />
            </Form.Item>
          </Col>
        </Row>
        {isEdit && (
          <Form.Item name="is_active" label="Активен" valuePropName="checked">
            <Switch />
          </Form.Item>
        )}
      </Form>
    </Modal>
  );
}

export default function UsersPage() {
  const currentUser = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();

  const [filters, setFilters] = useState({ search: '', role: null });
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);

  const params = Object.fromEntries(
    Object.entries({ ...filters, search: filters.search || undefined }).filter(([, value]) => value != null),
  );

  const { data: users = [], isLoading, refetch } = useQuery({
    queryKey: ['users', params],
    queryFn: () => usersApi.list(params),
  });

  const deleteMutation = useMutation({
    mutationFn: usersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['users-active'] });
      message.success('Пользователь удалён');
    },
    onError: () => {
      message.error('Не удалось удалить пользователя');
    },
  });

  const openCreate = () => {
    setEditingUser(null);
    setModalOpen(true);
  };

  const openEdit = (record) => {
    setEditingUser(record);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingUser(null);
  };

  const columns = [
    {
      title: 'Пользователь',
      dataIndex: 'full_name',
      ellipsis: true,
      render: (name, row) => (
        <Space direction="vertical" size={0}>
          <Text strong>{name || row.email}</Text>
          <Text type="secondary">{row.email}</Text>
        </Space>
      ),
    },
    {
      title: 'Роль',
      dataIndex: 'role',
      width: 160,
      render: (role) => <Tag color={roleMeta[role]?.color}>{roleMeta[role]?.label || role}</Tag>,
    },
    {
      title: 'Подразделение',
      dataIndex: 'department',
      ellipsis: true,
      render: (value) => value || <Text type="secondary">Не указано</Text>,
    },
    {
      title: 'Активен',
      dataIndex: 'is_active',
      width: 100,
      render: (active) => <Switch size="small" checked={active} disabled />,
    },
    {
      title: 'Создан',
      dataIndex: 'date_joined',
      width: 130,
      render: (date) => dayjs(date).format('DD.MM.YYYY'),
    },
    {
      title: '',
      key: 'actions',
      width: 120,
      render: (_, record) => {
        const isSelf = record.id === currentUser?.id;
        return (
          <Space size={4}>
            <Button
              type="text"
              icon={<EditOutlined />}
              aria-label="Редактировать пользователя"
              onClick={() => openEdit(record)}
            />
            <Popconfirm
              title="Удалить пользователя?"
              description={isSelf ? 'Нельзя удалить собственный аккаунт.' : 'Это действие нельзя отменить.'}
              okText="Удалить"
              cancelText="Отмена"
              okButtonProps={{ danger: true, loading: deleteMutation.isPending, disabled: isSelf }}
              onConfirm={() => !isSelf && deleteMutation.mutate(record.id)}
            >
              <Button
                type="text"
                danger
                disabled={isSelf}
                icon={<DeleteOutlined />}
                aria-label="Удалить пользователя"
              />
            </Popconfirm>
          </Space>
        );
      },
    },
  ];

  return (
    <div>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Title level={4} style={{ margin: 0 }}>Пользователи</Title>
        </Col>
        <Col>
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            Добавить пользователя
          </Button>
        </Col>
      </Row>

      <Row gutter={12} style={{ marginBottom: 16 }}>
        <Col flex="1">
          <Input
            placeholder="Поиск по имени, email или подразделению"
            prefix={<SearchOutlined />}
            value={filters.search}
            onChange={(event) => setFilters((prev) => ({ ...prev, search: event.target.value }))}
            allowClear
          />
        </Col>
        <Col>
          <Select
            placeholder="Роль"
            allowClear
            style={{ width: 180 }}
            options={ROLE_OPTIONS.map(({ value, label }) => ({ value, label }))}
            value={filters.role}
            onChange={(role) => setFilters((prev) => ({ ...prev, role: role ?? null }))}
          />
        </Col>
        <Col>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()} />
        </Col>
      </Row>

      <Table
        dataSource={users}
        columns={columns}
        rowKey="id"
        loading={isLoading}
        locale={{ emptyText: <Empty description="Пользователи не найдены" /> }}
        pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (total) => `Всего: ${total}` }}
      />

      <UserModal open={modalOpen} user={editingUser} onClose={closeModal} />
    </div>
  );
}
