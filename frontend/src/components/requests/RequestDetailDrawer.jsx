import React, { useState } from 'react';
import {
  Drawer, Descriptions, Typography, Space, Button, Select, Input,
  Timeline, Divider, Modal, Alert, Spin, Tag,
} from 'antd';
import {
  UserOutlined, ClockCircleOutlined, CheckCircleOutlined,
  ExclamationCircleOutlined, CloseCircleOutlined, SyncOutlined,
} from '@ant-design/icons';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { requestsApi, usersApi } from '../../services/requests';
import { PRIORITY, STATUS, VALID_TRANSITIONS } from './constants';
import PriorityTag from './PriorityTag';
import StatusBadge from './StatusBadge';
import useAuthStore from '../../store/authStore';

const { Text, Paragraph } = Typography;

const STATUS_TRANSITION_LABELS = {
  in_progress: 'Взять в работу',
  completed:   'Завершить',
  on_hold:     'Приостановить',
  cancelled:   'Отменить',
  closed:      'Закрыть',
};

const TIMELINE_ICONS = {
  new:         <ExclamationCircleOutlined style={{ color: '#1677ff' }} />,
  assigned:    <UserOutlined             style={{ color: '#4096ff' }} />,
  in_progress: <SyncOutlined             style={{ color: '#fa8c16' }} />,
  on_hold:     <ClockCircleOutlined      style={{ color: '#faad14' }} />,
  completed:   <CheckCircleOutlined      style={{ color: '#52c41a' }} />,
  closed:      <CheckCircleOutlined      style={{ color: '#8c8c8c' }} />,
  cancelled:   <CloseCircleOutlined      style={{ color: '#ff4d4f' }} />,
};

function buildTimeline(req) {
  const items = [];
  items.push({
    dot: TIMELINE_ICONS.new,
    children: (
      <>
        <Text strong>Создана</Text>
        <br />
        <Text type="secondary">{dayjs(req.created_at).format('DD.MM.YYYY HH:mm')}</Text>
        {req.created_by_detail && (
          <Text type="secondary"> · {req.created_by_detail.full_name || req.created_by_detail.email}</Text>
        )}
      </>
    ),
  });

  if (req.assigned_to_detail) {
    items.push({
      dot: TIMELINE_ICONS.assigned,
      children: (
        <>
          <Text strong>Назначена</Text>
          <br />
          <Text type="secondary">
            Исполнитель: {req.assigned_to_detail.full_name || req.assigned_to_detail.email}
          </Text>
        </>
      ),
    });
  }

  if (!['new', 'assigned'].includes(req.status)) {
    items.push({
      dot: TIMELINE_ICONS[req.status],
      children: (
        <>
          <Text strong>{STATUS[req.status]?.label ?? req.status}</Text>
          <br />
          {req.completed_at && (
            <Text type="secondary">{dayjs(req.completed_at).format('DD.MM.YYYY HH:mm')}</Text>
          )}
          {req.resolution_notes && (
            <Paragraph type="secondary" style={{ marginTop: 4, marginBottom: 0 }}>
              {req.resolution_notes}
            </Paragraph>
          )}
        </>
      ),
    });
  }

  return items;
}

export default function RequestDetailDrawer({ requestId, onClose }) {
  const user = useAuthStore((s) => s.user);
  const canManage = user?.role === 'admin' || user?.role === 'manager';
  const queryClient = useQueryClient();

  const [assignModalOpen, setAssignModalOpen]         = useState(false);
  const [selectedUser, setSelectedUser]               = useState(null);
  const [pendingStatus, setPendingStatus]             = useState(null);
  const [resolutionNotes, setResolutionNotes]         = useState('');
  const [statusConfirmOpen, setStatusConfirmOpen]     = useState(false);

  const { data: req, isLoading } = useQuery({
    queryKey: ['request', requestId],
    queryFn: () => requestsApi.detail(requestId),
    enabled: !!requestId,
  });

  const { data: users = [] } = useQuery({
    queryKey: ['users-active'],
    queryFn: () => usersApi.list({ is_active: true }),
    enabled: canManage && assignModalOpen,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['requests'] });
    queryClient.invalidateQueries({ queryKey: ['request', requestId] });
  };

  const assignMutation = useMutation({
    mutationFn: ({ user_id }) => requestsApi.assign(requestId, user_id),
    onSuccess: () => { invalidate(); setAssignModalOpen(false); setSelectedUser(null); },
  });

  const statusMutation = useMutation({
    mutationFn: ({ status, notes }) => requestsApi.setStatus(requestId, status, notes),
    onSuccess: () => { invalidate(); setStatusConfirmOpen(false); setPendingStatus(null); setResolutionNotes(''); },
  });

  const handleStatusClick = (status) => {
    setPendingStatus(status);
    setStatusConfirmOpen(true);
  };

  const nextStatuses = req ? (VALID_TRANSITIONS[req.status] ?? []) : [];

  return (
    <>
      <Drawer
        title={
          req ? (
            <Space wrap>
              <Text>#{req.id}</Text>
              <PriorityTag priority={req.priority} />
              <StatusBadge status={req.status} />
            </Space>
          ) : 'Заявка'
        }
        open={!!requestId}
        onClose={onClose}
        width={600}
        styles={{ body: { paddingBottom: 80 } }}
      >
        {isLoading && <Spin style={{ display: 'block', margin: '40px auto' }} />}

        {req && (
          <>
            <Typography.Title level={4} style={{ marginTop: 0 }}>{req.title}</Typography.Title>

            <Descriptions column={2} size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="Оборудование" span={2}>
                {req.equipment_detail?.name ?? '—'}
                {req.equipment_detail?.inventory_number && (
                  <Text type="secondary"> [{req.equipment_detail.inventory_number}]</Text>
                )}
              </Descriptions.Item>
              <Descriptions.Item label="Автор">
                {req.created_by_detail?.full_name || req.created_by_detail?.email || '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Создана">
                {dayjs(req.created_at).format('DD.MM.YYYY HH:mm')}
              </Descriptions.Item>
              <Descriptions.Item label="Исполнитель" span={2}>
                {req.assigned_to_detail
                  ? req.assigned_to_detail.full_name || req.assigned_to_detail.email
                  : <Text type="secondary">Не назначен</Text>}
              </Descriptions.Item>
            </Descriptions>

            <Divider orientation="left" plain>Описание</Divider>
            <Paragraph>{req.description}</Paragraph>

            {req.resolution_notes && (
              <>
                <Divider orientation="left" plain>Выполненные работы</Divider>
                <Paragraph>{req.resolution_notes}</Paragraph>
              </>
            )}

            <Divider orientation="left" plain>История</Divider>
            <Timeline items={buildTimeline(req)} style={{ marginTop: 8 }} />

            {canManage && (
              <>
                <Divider orientation="left" plain>Действия</Divider>
                <Space wrap>
                  <Button
                    icon={<UserOutlined />}
                    onClick={() => setAssignModalOpen(true)}
                    disabled={['closed', 'cancelled', 'completed'].includes(req.status)}
                  >
                    Назначить исполнителя
                  </Button>
                  {nextStatuses.map((s) => {
                    const isDestructive = s === 'cancelled';
                    const isPositive    = ['completed', 'closed', 'in_progress'].includes(s);
                    return (
                      <Button
                        key={s}
                        danger={isDestructive}
                        type={isPositive ? 'primary' : 'default'}
                        loading={statusMutation.isPending && pendingStatus === s}
                        onClick={() => handleStatusClick(s)}
                      >
                        {STATUS_TRANSITION_LABELS[s] ?? STATUS[s]?.label ?? s}
                      </Button>
                    );
                  })}
                </Space>
                {statusMutation.isError && (
                  <Alert
                    message="Ошибка при изменении статуса"
                    type="error"
                    showIcon
                    style={{ marginTop: 12 }}
                  />
                )}
              </>
            )}
          </>
        )}
      </Drawer>

      {/* Assign modal */}
      <Modal
        title="Назначить исполнителя"
        open={assignModalOpen}
        onCancel={() => { setAssignModalOpen(false); setSelectedUser(null); }}
        onOk={() => selectedUser && assignMutation.mutate({ user_id: selectedUser })}
        okText="Назначить"
        confirmLoading={assignMutation.isPending}
        okButtonProps={{ disabled: !selectedUser }}
      >
        <Select
          style={{ width: '100%', marginTop: 16 }}
          placeholder="Выберите механика"
          value={selectedUser}
          onChange={setSelectedUser}
          showSearch
          filterOption={(input, opt) => opt.label.toLowerCase().includes(input.toLowerCase())}
          options={users
            .filter((u) => ['mechanic', 'admin'].includes(u.role))
            .map((u) => ({ value: u.id, label: u.full_name || u.email }))}
        />
      </Modal>

      {/* Status change confirm */}
      <Modal
        title={`Изменить статус → "${STATUS[pendingStatus]?.label ?? pendingStatus}"`}
        open={statusConfirmOpen}
        onCancel={() => { setStatusConfirmOpen(false); setPendingStatus(null); setResolutionNotes(''); }}
        onOk={() => statusMutation.mutate({ status: pendingStatus, notes: resolutionNotes })}
        okText="Подтвердить"
        okButtonProps={{ danger: pendingStatus === 'cancelled' }}
        confirmLoading={statusMutation.isPending}
      >
        {pendingStatus === 'completed' && (
          <Input.TextArea
            style={{ marginTop: 12 }}
            rows={3}
            placeholder="Описание выполненных работ (необязательно)"
            value={resolutionNotes}
            onChange={(e) => setResolutionNotes(e.target.value)}
          />
        )}
        {!['completed'].includes(pendingStatus) && (
          <Text>Подтвердите изменение статуса заявки.</Text>
        )}
      </Modal>
    </>
  );
}
