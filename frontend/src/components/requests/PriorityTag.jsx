import React from 'react';
import { Tag } from 'antd';
import { PRIORITY } from './constants';

export default function PriorityTag({ priority }) {
  const cfg = PRIORITY[priority] ?? { label: priority, color: '#d9d9d9' };
  return (
    <Tag
      style={{
        color: '#fff',
        background: cfg.color,
        border: 'none',
        fontWeight: 600,
        minWidth: 90,
        textAlign: 'center',
      }}
    >
      {cfg.label}
    </Tag>
  );
}
