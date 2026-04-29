import React, { useState } from 'react';
import {
  List, Avatar, Typography, Button, Tag, Space,
  Segmented, Spin, Empty, Tooltip, Row, Col, Card,
} from 'antd';
import {
  BellOutlined, CheckOutlined, CheckCircleOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/ru';
import { notificationsApi } from '../services/notifications';
import { getCfg } from '../components/notifications/notifConfig';

dayjs.extend(relativeTime);
dayjs.locale('ru');

const { Title, Text, Paragraph } = Typography;

const PAGE_SIZE = 20;

function NotifTypeTag({ type }) {
  const cfg = getCfg(type);
  return (
    <Tag style={{ background: `${cfg.color}18`, color: cfg.color, border: `1px solid ${cfg.color}40`, fontSize: 11 }}>
      {cfg.label}
    </Tag>
  );
}

export default function NotificationsPage() {
  const [filter, setFilter] = useState('all');   // 'all' | 'unread'
  const [page, setPage] = useState(1);
  const qc = useQueryClient();

  const params = {
    ordering: '-created_at',
    page,
    page_size: PAGE_SIZE,
    ...(filter === 'unread' ? { is_read: false } : {}),
  };

  const { data, isLoading } = useQuery({
    queryKey: ['notifications', filter, page],
    queryFn: () => notificationsApi.list(params),
    keepPreviousData: true,
  });

  const { data: unreadCount = 0 } = useQuery({
    queryKey: ['notif-unread-count'],
    queryFn: notificationsApi.unreadCount,
    refetchInterval: 30_000,
    refetchIntervalInBackground: true,
  });

  const items = data?.results ?? [];
  const total = data?.count ?? 0;

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['notifications'] });
    qc.invalidateQueries({ queryKey: ['notif-unread-count'] });
    qc.invalidateQueries({ queryKey: ['notif-recent'] });
  };

  const { mutate: markRead } = useMutation({
    mutationFn: notificationsApi.markRead,
    onSuccess: invalidate,
  });

  const { mutate: markAll, isPending: markAllPending } = useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => { setPage(1); invalidate(); },
  });

  const handleFilterChange = (val) => {
    setFilter(val);
    setPage(1);
  };

  return (
    <div style={{ padding: 24, maxWidth: 860, margin: '0 auto' }}>
      {/* header */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 20 }}>
        <Col>
          <Space align="center">
            <BellOutlined style={{ fontSize: 22, color: '#1677ff' }} />
            <Title level={4} style={{ margin: 0 }}>Уведомления</Title>
            {unreadCount > 0 && (
              <Tag color="blue" style={{ fontWeight: 600 }}>{unreadCount} непрочитанных</Tag>
            )}
          </Space>
        </Col>
        <Col>
          <Button
            icon={<CheckOutlined />}
            onClick={() => markAll()}
            loading={markAllPending}
            disabled={unreadCount === 0}
          >
            Прочитать все
          </Button>
        </Col>
      </Row>

      {/* filter tabs */}
      <Segmented
        value={filter}
        onChange={handleFilterChange}
        options={[
          { label: 'Все', value: 'all' },
          { label: `Непрочитанные${unreadCount > 0 ? ` (${unreadCount})` : ''}`, value: 'unread' },
        ]}
        style={{ marginBottom: 16 }}
      />

      {/* list */}
      <Card bordered={false} styles={{ body: { padding: 0 } }} style={{ boxShadow: '0 1px 4px rgba(0,0,0,.08)' }}>
        <Spin spinning={isLoading}>
          {items.length === 0 && !isLoading ? (
            <Empty
              description={filter === 'unread' ? 'Нет непрочитанных уведомлений' : 'Уведомлений нет'}
              style={{ padding: '48px 0' }}
            />
          ) : (
            <List
              dataSource={items}
              pagination={{
                current: page,
                pageSize: PAGE_SIZE,
                total,
                onChange: (p) => setPage(p),
                showTotal: (t) => `Всего: ${t}`,
                style: { padding: '12px 16px' },
                size: 'default',
              }}
              renderItem={(item) => {
                const cfg = getCfg(item.notification_type);
                return (
                  <List.Item
                    key={item.id}
                    style={{
                      padding: '14px 20px',
                      background: item.is_read ? 'transparent' : '#e6f4ff',
                      transition: 'background .15s',
                      cursor: item.is_read ? 'default' : 'pointer',
                      borderLeft: item.is_read ? '3px solid transparent' : `3px solid ${cfg.color}`,
                    }}
                    onClick={() => !item.is_read && markRead(item.id)}
                    actions={
                      !item.is_read
                        ? [
                            <Tooltip title="Отметить прочитанным" key="read">
                              <Button
                                type="text"
                                size="small"
                                icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
                                onClick={(e) => { e.stopPropagation(); markRead(item.id); }}
                              />
                            </Tooltip>,
                          ]
                        : []
                    }
                  >
                    <List.Item.Meta
                      avatar={
                        <Avatar
                          icon={cfg.icon}
                          style={{ background: item.is_read ? '#d9d9d9' : cfg.color, flexShrink: 0 }}
                          size={40}
                        />
                      }
                      title={
                        <Space size={8} wrap>
                          <Text
                            strong={!item.is_read}
                            style={{ fontSize: 14, color: item.is_read ? '#595959' : '#000' }}
                          >
                            {item.title}
                          </Text>
                          <NotifTypeTag type={item.notification_type} />
                          {!item.is_read && (
                            <span
                              style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: '#1677ff' }}
                            />
                          )}
                        </Space>
                      }
                      description={
                        <div>
                          <Paragraph
                            style={{ margin: 0, fontSize: 13, color: '#595959' }}
                            ellipsis={{ rows: 2 }}
                          >
                            {item.message}
                          </Paragraph>
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {dayjs(item.created_at).format('DD.MM.YYYY, HH:mm')}
                            {' · '}
                            {dayjs(item.created_at).fromNow()}
                          </Text>
                        </div>
                      }
                    />
                  </List.Item>
                );
              }}
            />
          )}
        </Spin>
      </Card>
    </div>
  );
}
