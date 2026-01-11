import { useState, useEffect } from 'react'
import { Form, Input, Select, Button, Card, InputNumber, message, Radio } from 'antd'
import { useNavigate } from 'react-router-dom'
import { taskApi, datasetApi } from '@/services/api'
import { authStorage } from '@/services/auth'
import type { Dataset, TaskMode } from '@/types'

const CreateTask = () => {
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [taskMode, setTaskMode] = useState<TaskMode>('STANDARD')

  const userInfo = authStorage.getUser()
  const userId = userInfo?.userId || 1

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    try {
      const res = await datasetApi.getUserDatasets(userId)
      setDatasets(res.data.filter(d => !d.isOptimized))
    } catch (error) {
      message.error('加载数据集失败')
    }
  }

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      const data = {
        taskName: values.taskName,
        modelName: values.modelName,
        datasetId: values.datasetId,
        userId,
        hyperparameters: JSON.stringify({
          learning_rate: values.learning_rate,
          epochs: values.epochs,
          batch_size: values.batch_size,
        }),
      }

      if (taskMode === 'STANDARD') {
        await taskApi.createStandard(data)
      } else {
        await taskApi.createContinuous({
          ...data,
          maxIterations: values.maxIterations,
          performanceThreshold: values.performanceThreshold,
        })
      }

      message.success('任务创建成功')
      navigate('/tasks')
    } catch (error) {
      message.error('任务创建失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>创建训练任务</h1>

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            taskMode: 'STANDARD',
            learning_rate: 0.001,
            epochs: 10,
            batch_size: 32,
            maxIterations: 5,
            performanceThreshold: 0.95,
          }}
        >
          <Form.Item
            name="taskName"
            label="任务名称"
            rules={[{ required: true, message: '请输入任务名称' }]}
          >
            <Input placeholder="请输入任务名称" />
          </Form.Item>

          <Form.Item
            name="taskMode"
            label="任务模式"
            rules={[{ required: true }]}
          >
            <Radio.Group onChange={(e) => setTaskMode(e.target.value)}>
              <Radio.Button value="STANDARD">标准训练流</Radio.Button>
              <Radio.Button value="CONTINUOUS">持续学习流</Radio.Button>
            </Radio.Group>
          </Form.Item>

          <Form.Item
            name="modelName"
            label="模型名称"
            rules={[{ required: true, message: '请选择模型' }]}
          >
            <Select placeholder="请选择模型">
              <Select.Option value="qwen-7b">Qwen-7B</Select.Option>
              <Select.Option value="qwen-14b">Qwen-14B</Select.Option>
              <Select.Option value="llama2-7b">LLaMA2-7B</Select.Option>
              <Select.Option value="llama2-13b">LLaMA2-13B</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="datasetId"
            label="数据集"
            rules={[{ required: true, message: '请选择数据集' }]}
          >
            <Select placeholder="请选择数据集">
              {datasets.map(ds => (
                <Select.Option key={ds.datasetId} value={ds.datasetId}>
                  {ds.name} ({ds.domain})
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <h3 style={{ marginTop: 24, marginBottom: 16 }}>训练超参数</h3>

          <Form.Item
            name="learning_rate"
            label="学习率"
            rules={[{ required: true }]}
          >
            <InputNumber
              min={0.00001}
              max={0.1}
              step={0.0001}
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Form.Item
            name="epochs"
            label="训练轮数"
            rules={[{ required: true }]}
          >
            <InputNumber min={1} max={100} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="batch_size"
            label="批次大小"
            rules={[{ required: true }]}
          >
            <InputNumber min={1} max={256} style={{ width: '100%' }} />
          </Form.Item>

          {taskMode === 'CONTINUOUS' && (
            <>
              <h3 style={{ marginTop: 24, marginBottom: 16 }}>持续学习配置</h3>

              <Form.Item
                name="maxIterations"
                label="最大迭代次数"
                rules={[{ required: true }]}
              >
                <InputNumber min={1} max={20} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                name="performanceThreshold"
                label="性能阈值"
                rules={[{ required: true }]}
              >
                <InputNumber
                  min={0}
                  max={1}
                  step={0.01}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </>
          )}

          <Form.Item style={{ marginTop: 32 }}>
            <Button type="primary" htmlType="submit" loading={loading} style={{ marginRight: 8 }}>
              创建任务
            </Button>
            <Button onClick={() => navigate('/tasks')}>
              取消
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default CreateTask
