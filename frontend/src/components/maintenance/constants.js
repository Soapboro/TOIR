import dayjs from 'dayjs';

export const PLAN_STATUS = {
  planned:     { label: 'Запланировано', color: '#1677ff', badgeStatus: 'processing' },
  in_progress: { label: 'Выполняется',  color: '#fa8c16', badgeStatus: 'warning'    },
  completed:   { label: 'Выполнено',    color: '#52c41a', badgeStatus: 'success'    },
  overdue:     { label: 'Просрочено',   color: '#ff4d4f', badgeStatus: 'error'      },
  cancelled:   { label: 'Отменено',     color: '#bfbfbf', badgeStatus: 'default'    },
};

export const MAINTENANCE_TYPE = {
  scheduled:   'Плановое ТО',
  unscheduled: 'Внеплановое ТО',
  inspection:  'Осмотр',
  calibration: 'Калибровка',
  lubrication: 'Смазка',
  overhaul:    'Капитальный ремонт',
};

export const STATUS_OPTIONS = Object.entries(PLAN_STATUS).map(([value, { label }]) => ({ value, label }));
export const TYPE_OPTIONS   = Object.entries(MAINTENANCE_TYPE).map(([value, label]) => ({ value, label }));

/** Визуальный статус с учётом просроченности */
export function resolveStatus(plan) {
  if (plan.status === 'planned' && dayjs(plan.scheduled_date).isBefore(dayjs(), 'day')) {
    return 'overdue';
  }
  return plan.status;
}
