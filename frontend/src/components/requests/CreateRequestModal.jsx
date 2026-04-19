import React from 'react';
import { Modal, Form, Select, Input, Button, Space } from 'antd';
import { Controller, useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { equipmentApi, requestsApi } from '../../services/requests';
import { PRIORITY_OPTIONS } from './constants';

export default function CreateRequestModal({ open, onClose }) {
  const queryClient = useQueryClient();
  const { control, handleSubmit, reset, formState: { errors } } = useForm({
    defaultValues: { equipment: null, title: '', description: '', priority: 'medium' },
  });

  const { data: equipment = [], isLoading: equipLoading } = useQuery({
    queryKey: ['equipment-list'],
    queryFn: () => equipmentApi.list({ status: 'active' }),
    enabled: open,
  });

  const { mutate, isPending } = useMutation({
    mutationFn: requestsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['requests'] });
      reset();
      onClose();
    },
  });

  const equipOptions = equipment.map((e) => ({
    value: e.id,
    label: `${e.name} [${e.inventory_number}]`,
  }));

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
      title="Новая заявка на ремонт"
      open={open}
      onCancel={() => { reset(); onClose(); }}
      footer={null}
      width={560}
      destroyOnClose
    >
      <Form layout="vertical" onFinish={handleSubmit((d) => mutate(d))} style={{ marginTop: 16 }}>
        {field('equipment', 'Оборудование', { required: 'Выберите оборудование' }, ({ field: f }) => (
          <Select
            {...f}
            showSearch
            loading={equipLoading}
            placeholder="Выберите оборудование"
            options={equipOptions}
            filterOption={(input, opt) => opt.label.toLowerCase().includes(input.toLowerCase())}
          />
        ))}

        {field('title', 'Тема', { required: 'Введите тему' }, ({ field: f }) => (
          <Input {...f} placeholder="Краткое описание неисправности" />
        ))}

        {field('description', 'Описание неисправности', { required: 'Введите описание' }, ({ field: f }) => (
          <Input.TextArea {...f} rows={4} placeholder="Подробно опишите проблему" />
        ))}

        {field('priority', 'Приоритет', {}, ({ field: f }) => (
          <Select {...f} options={PRIORITY_OPTIONS} />
        ))}

        <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
          <Space>
            <Button onClick={() => { reset(); onClose(); }}>Отмена</Button>
            <Button type="primary" htmlType="submit" loading={isPending}>
              Создать заявку
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
}
