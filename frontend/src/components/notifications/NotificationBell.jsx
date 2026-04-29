import React, { useState } from 'react';
import {
  Badge, Popover, Button, List, Avatar, Typography,
  Divider, Space, Spin, Empty,
} from 'antd';
import { BellOutlined, CheckOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/ru';
import { notificationsApi } from '../../services/notifications';
import { getCfg } from './notifConfig';

dayjs.extend(relativeTime);
dayjs.locale('ru');

const { Text } = Typography;

function NotifItem({ item, onRead }) {
  const cfg = getCfg(item.notification_type);
  return (
    <List.Item
      onClick={() => !item.is_read && onRead(item.id)}
      style={{
        padding: '10px 16px',
        cursor: item.is_read ? 'default' : 'pointer',
        background: item.is_read ? 'transparent' : '#e6f4ff',
        transition: 'background .15s',
      }}
    >
      <List.Item.Meta
        avatar={
          <Avatar
            icon={cfg.icon}
            style={{ background: cfg.color, flexShrink: 0 }}
            size={34}
          />
        }
        title={
          <Space size={6}>
            {!item.is_read && (
              <span style={{ display: 'inline-block', width: 7, height: 7, borderRadius: '50%', background: '#1677ff', flexShrink: 0 }} />
            )}
            <Text strong style={{ fontSize: 13, lineHeight: '18px' }}>{item.title}</Text>
          </Space>
        }
        description={
          <div>
            <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 2 }}>
              {item.message.length > 80 ? `${item.message.slice(0, 80)}…` : item.message}
            </Text>
            <Text type="secondary" style={{ fontSize: 11 }}>
              {dayjs(item.created_at).fromNow()}
            </Text>
          </div>
        }
      />
    </List.Item>
  );
}

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const qc = useQueryClient();

  /* polling unread count every 30 s */
  const { data: unreadCount = 0 } = useQuery({
    queryKey: ['notif-unread-count'],
    queryFn: notificationsApi.unreadCount,
    refetchInterval: 30_000,
    refetchIntervalInBackground: true,
  });

  /* fetch recent 8 when popover opens */
  const { data: recent, isLoading: recentLoading } = useQuery({
    queryKey: ['notif-recent'],
    queryFn: () => notificationsApi.list({ page_size: 8, ordering: '-created_at' }),
    enabled: open,
    staleTime: 0,
  });
  const recentItems = recent?.results ?? [];

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['notif-unread-count'] });
    qc.invalidateQueries({ queryKey: ['notif-recent'] });
    qc.invalidateQueries({ queryKey: ['notifications'] });
  };

  const { mutate: markRead } = useMutation({
    mutationFn: notificationsApi.markRead,
    onSuccess: invalidate,
  });

  const { mutate: markAll, isPending: markAllPending } = useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: invalidate,
  });

  const content = (
    <div style={{ width: 360 }}>
      {/* header */}
      <div style={{ padding: '10px 16px 6px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Text strong style={{ fontSize: 14 }}>Уведомления</Text>
        <Button
          type="link"
          size="small"
          icon={<CheckOutlined />}
          loading={markAllPending}
          disabled={unreadCount === 0}
          onClick={() => markAll()}
          style={{ padding: 0, fontSize: 12 }}
        >
          Прочитать все
        </Button>
      </div>
      <Divider style={{ margin: 0 }} />

      {/* list */}
      <div style={{ maxHeight: 380, overflowY: 'auto' }}>
        <Spin spinning={recentLoading}>
          {recentItems.length === 0 && !recentLoading ? (
            <Empty description="Нет уведомлений" style={{ padding: '24px 0' }} image={Empty.PRESENTED_IMAGE_SIMPLE} />
          ) : (
            <List
              dataSource={recentItems}
              renderItem={(item) => (
                <NotifItem key={item.id} item={item} onRead={markRead} />
              )}
              split
            />
          )}
        </Spin>
      </div>

      {/* footer */}
      <Divider style={{ margin: 0 }} />
      <div style={{ padding: '8px 16px', textAlign: 'center' }}>
        <Button
          type="link"
          size="small"
          onClick={() => { setOpen(false); navigate('/notifications'); }}
          style={{ fontSize: 13 }}
        >
          Все уведомления →
        </Button>
      </div>
    </div>
  );

  return (
    <Popover
      content={content}
      trigger="click"
      open={open}
      onOpenChange={setOpen}
      placement="bottomRight"
      arrow={false}
      overlayInnerStyle={{ padding: 0, borderRadius: 8 }}
      overlayStyle={{ zIndex: 1100 }}
    >
      <Badge
        count={unreadCount}
        overflowCount={99}
        offset={[-2, 2]}
      >
        <Button
          type="text"
          icon={<BellOutlined style={{ fontSize: 18, color: '#fff' }} />}
          style={{ background: 'transparent', border: 'none', padding: '4px 8px' }}
        />
      </Badge>
    </Popover>
  );
}
