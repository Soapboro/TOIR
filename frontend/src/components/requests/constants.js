export const PRIORITY = {
  critical: { label: 'Критический', color: '#ff4d4f', antColor: 'error'   },
  high:     { label: 'Высокий',     color: '#fa8c16', antColor: 'warning'  },
  medium:   { label: 'Средний',     color: '#faad14', antColor: 'default'  },
  low:      { label: 'Низкий',      color: '#52c41a', antColor: 'success'  },
};

export const STATUS = {
  new:         { label: 'Новая',           color: 'blue'      },
  assigned:    { label: 'Назначена',       color: 'geekblue'  },
  in_progress: { label: 'В работе',        color: 'processing'},
  on_hold:     { label: 'Приостановлена',  color: 'orange'    },
  completed:   { label: 'Выполнена',       color: 'green'     },
  closed:      { label: 'Закрыта',         color: 'default'   },
  cancelled:   { label: 'Отменена',        color: 'red'       },
};

export const VALID_TRANSITIONS = {
  new:         ['cancelled'],
  assigned:    ['in_progress', 'cancelled'],
  in_progress: ['completed', 'on_hold', 'cancelled'],
  on_hold:     ['in_progress', 'cancelled'],
  completed:   ['closed'],
  closed:      [],
  cancelled:   [],
};

export const PRIORITY_OPTIONS = Object.entries(PRIORITY).map(([value, { label }]) => ({ value, label }));
export const STATUS_OPTIONS   = Object.entries(STATUS).map(([value, { label }]) => ({ value, label }));
