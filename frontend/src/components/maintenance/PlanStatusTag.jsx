import React from 'react';
import { Tag } from 'antd';
import { PLAN_STATUS, resolveStatus } from './constants';

export default function PlanStatusTag({ plan }) {
  const key = resolveStatus(plan);
  const cfg = PLAN_STATUS[key] ?? { label: key, color: '#d9d9d9' };
  return (
    <Tag
      style={{
        color: '#fff',
        background: cfg.color,
        border: 'none',
        fontWeight: 600,
        minWidth: 110,
        textAlign: 'center',
      }}
    >
      {cfg.label}
    </Tag>
  );
}
