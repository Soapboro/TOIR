import React from 'react';
import {
  FileTextOutlined, CalendarOutlined, ExclamationCircleOutlined,
  WarningOutlined, InfoCircleOutlined, CheckCircleOutlined,
} from '@ant-design/icons';

export const NOTIF_TYPE_CFG = {
  request_created:        { icon: <FileTextOutlined />,          color: '#1677ff', label: 'Создана заявка'        },
  request_assigned:       { icon: <CheckCircleOutlined />,       color: '#52c41a', label: 'Заявка назначена'       },
  request_status_changed: { icon: <FileTextOutlined />,          color: '#fa8c16', label: 'Статус заявки'          },
  maintenance_due:        { icon: <CalendarOutlined />,          color: '#13c2c2', label: 'Плановое ТО'            },
  maintenance_overdue:    { icon: <ExclamationCircleOutlined />, color: '#ff4d4f', label: 'Просрочено ТО'          },
  failure_prediction:     { icon: <WarningOutlined />,           color: '#fa8c16', label: 'Прогноз неисправности'  },
  system:                 { icon: <InfoCircleOutlined />,        color: '#8c8c8c', label: 'Системное'              },
};

export function getCfg(type) {
  return NOTIF_TYPE_CFG[type] ?? { icon: <InfoCircleOutlined />, color: '#8c8c8c', label: type };
}
