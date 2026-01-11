import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Space } from 'antd'
import { 
  DatabaseOutlined, 
  RocketOutlined, 
  CheckCircleOutlined, 
  SyncOutlined 
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { datasetApi, taskApi } from '@/services/api'
import { authStorage } from '@/services/auth'
import { getStatusColor, getStatusText } from '@/utils/helpers'
import type { Dataset, MLTask } from '@/types'
import dayjs from 'dayjs'

const Dashboard = () => {
  const navigate = useNavigate()
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [tasks, setTasks] = useState<MLTask[]>([])
  const [loading, setLoading] = useState(true)

  const userInfo = authStorage.getUser()
  const userId = userInfo?.userId || 1

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [datasetsRes, tasksRes] = await Promise.all([
        datasetApi.getUserDatasets(userId),
        taskApi.getUserTasks(userId),
      ])
      setDatasets(datasetsRes.data)
      setTasks(tasksRes.data)
    } catch (error) {
      console.error('加载数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const runningTasks = tasks.filter(t => 
    ['OPTIMIZING', 'TRAINING', 'EVALUATING', 'LOOPING'].includes(t.status)
  )
  const completedTasks = tasks.filter(t => t.status === 'COMPLETED')

  const taskColumns = [
    {
      title: '任务名称',
      dataIndex: 'taskName',
      key: 'taskName',
      render: (text: string, record: MLTask) => (
        <a onClick={() => navigate(`/tasks/${record.taskId}`)}>{text}</a>
      ),
    },
    {
      title: '模式',
      dataIndex: 'taskMode',
      key: 'taskMode',
      render: (mode: string) => (
        <Tag color={mode === 'STANDARD' ? 'blue' : 'purple'}>
          {mode === 'STANDARD' ? '标准训练' : '持续学习'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status as any)}>
          {getStatusText(status as any)}
        </Tag>
      ),
    },
    {
      title: '迭代',
      dataIndex: 'currentIteration',
      key: 'currentIteration',
      render: (iter: number, record: MLTask) => 
        record.maxIterations ? `${iter}/${record.maxIterations}` : iter,
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
  ]

  return (
    <div>
      <h1 style={{ marginBottom: 24 }}>仪表盘</h1>
      
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="数据集总数"
              value={datasets.length}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="任务总数"
              value={tasks.length}
              prefix={<RocketOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="运行中"
              value={runningTasks.length}
              prefix={<SyncOutlined spin />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已完成"
              value={completedTasks.length}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="最近任务" style={{ marginBottom: 24 }}>
        <Table
          columns={taskColumns}
          dataSource={tasks.slice(0, 5)}
          rowKey="taskId"
          loading={loading}
          pagination={false}
        />
      </Card>
    </div>
  )
}

export default Dashboard
