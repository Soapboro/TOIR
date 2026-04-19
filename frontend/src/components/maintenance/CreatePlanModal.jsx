import React from 'react';
import { Modal, Form, Select, Input, Button, Space, InputNumber } from 'antd';
import { Controller, useForm } from 'react-hook-form';
import { DatePicker } from 'antd';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { equipmentApi, maintenanceApi } from '../../services/maintenance';
import { TYPE_OPTIONS } from './constants';

export default function CreatePlanModal({ open, onClose, defaultDate }) {
  const queryClient = useQueryClient();
  const { control, handleSubmit, reset, formState: { errors } } = useForm({
    defaultValues: {
      equipment: null,
      maintenance_type: 'scheduled',
      scheduled_date: defaultDate ?? null,
      estimated_duration_hours: null,
      notes: '',
    },
  });

  const { data: equipment = [], isLoading: equipLoading } = useQuery({
    queryKey: ['equipment-list'],
    queryFn: () => equipmentApi.list(),
    enabled: open,
  });

  const { mutate, isPending } = useMutation({
    mutationFn: (data) => maintenanceApi.create({
      ...data,
      scheduled_date: data.scheduled_date
        ? dayjs(data.scheduled_date).format('YYYY-MM-DD')
        : null,
      status: 'planned',
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance-plans'] });
      reset();
      onClose();
    },
  });

  const field = (name, label, rules, render) => (
    <Form.Item
      label={label}
      validateStatus={errors[name] ? 'error' : ''}
      help={errors[name]?.message}
    >
      <Controller name={name} control={control} rules={rules} render={render} />
    </Form.Item>
  );

  return (
    <Modal
      title="Новая запись планирования ТО"
      open={open}
      onCancel={() => { reset(); onClose(); }}
      footer={null}
      width={520}
      destroyOnClose
    >
      <Form layout="vertical" onFinish={handleSubmit((d) => mutate(d))} style={{ marginTop: 16 }}>
        {field('equipment', 'Оборудование', { required: 'Выберите оборудование' }, ({ field: f }) => (
          <Select
            {...f}
            showSearch
            loading={equipLoading}
            placeholder="Выберите оборудование"
            options={equipment.map((e) => ({ value: e.id, label: `${e.name} [${e.inventory_number}]` }))}
            filterOption={(input, opt) => opt.label.toLowerCase().includes(input.toLowerCase())}
          />
        ))}

        {field('maintenance_type', 'Вид ТО', { required: 'Выберите вид ТО' }, ({ field: f }) => (
          <Select {...f} options={TYPE_OPTIONS} />
        ))}

        {field('scheduled_date', 'Плановая дата', { required: 'Укажите дату' }, ({ field: f }) => (
          <DatePicker
            style={{ width: '100%' }}
            format="DD.MM.YYYY"
            value={f.value ? dayjs(f.value) : null}
            onChange={(d) => f.onChange(d)}
          />
        ))}

        {field('estimated_duration_hours', 'Плановая трудоёмкость (ч)', {}, ({ field: f }) => (
          <InputNumber
            {...f}
            style={{ width: '100%' }}
            min={0}
            step={0.5}
            placeholder="например, 4"
          />
        ))}

        {field('notes', 'Примечания', {}, ({ field: f }) => (
          <Input.TextArea {...f} rows={3} placeholder="Дополнительная информация" />
        ))}

        <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
          <Space>
            <Button onClick={() => { reset(); onClose(); }}>Отмена</Button>
            <Button type="primary" htmlType="submit" loading={isPending}>
              Создать
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
}
