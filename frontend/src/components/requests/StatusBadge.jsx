import React from 'react';
import { Badge } from 'antd';
import { STATUS } from './constants';

export default function StatusBadge({ status }) {
  const cfg = STATUS[status] ?? { label: status, color: 'default' };
  return <Badge color={cfg.color} text={cfg.label} />;
}
