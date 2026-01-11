import { useEffect, useState } from 'react'
import { Button, Table, Space, Tag, message, Popconfirm } from 'antd'
import { PlusOutlined, PlayCircleOutlined, PauseCircleOutlined, StopOutlined, DeleteOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { taskApi } from '@/services/api'
import { authStorage } from '@/services/auth'
import { getStatusColor, getStatusText } from '@/utils/helpers'
import type { MLTask } from '@/types'
import dayjs from 'dayjs'

const TaskList = () => {
  const navigate = useNavigate()
  const [tasks, setTasks] = useState<MLTask[]>([])
  const [loading, setLoading] = useState(false)

  const userInfo = authStorage.getUser()
  const userId = userInfo?.userId || 1

  useEffect(() => {
    loadTasks()
    const interval = setInterval(loadTasks, 5000) // 每5秒刷新
    return () => clearInterval(interval)
  }, [])

  const loadTasks = async () => {
    setLoading(true)
    try {
      const res = await taskApi.getUserTasks(userId)
      setTasks(res.data)
    } catch (error) {
      console.error('加载任务失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleStart = async (taskId: string) => {
    try {
      await taskApi.start(taskId)
      message.success('任务已启动')
      loadTasks()
    } catch (error: any) {
      message.error(error.response?.data?.error || '启动失败')
    }
  }

  const handleSuspend = async (taskId: string) => {
    try {
      await taskApi.suspend(taskId)
      message.success('任务已暂停')
      loadTasks()
    } catch (error) {
      message.error('暂停失败')
    }
  }

  const handleCancel = async (taskId: string) => {
    try {
      await taskApi.cancel(taskId)
      message.success('任务已取消')
      loadTasks()
    } catch (error) {
      message.error('取消失败')
    }
  }

  const handleDelete = async (taskId: string) => {
    try {
      await taskApi.delete(taskId)
      message.success('任务已删除')
      loadTasks()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const columns = [
    {
      title: '任务名称',
      dataIndex: 'taskName',
      key: 'taskName',
      render: (text: string, record: MLTask) => (
        <a onClick={() => navigate(`/tasks/${record.taskId}`)}>{text}</a>
      ),
    },
    {
      title: '模型',
      dataIndex: 'modelName',
      key: 'modelName',
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
      title: '最新分数',
      dataIndex: 'latestScore',
      key: 'latestScore',
      render: (score?: number) => score ? score.toFixed(4) : '-',
    },
    {
      title: '创建时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: MLTask) => (
        <Space>
          {record.status === 'PENDING' && (
            <Button
              type="link"
              icon={<PlayCircleOutlined />}
              onClick={() => handleStart(record.taskId)}
            >
              启动
            </Button>
          )}
          {['OPTIMIZING', 'TRAINING', 'EVALUATING', 'LOOPING'].includes(record.status) && (
            <>
              <Button
                type="link"
                icon={<PauseCircleOutlined />}
                onClick={() => handleSuspend(record.taskId)}
              >
                暂停
              </Button>
              <Popconfirm
                title="确定取消此任务？"
                onConfirm={() => handleCancel(record.taskId)}
                okText="确定"
                cancelText="取消"
              >
                <Button type="link" danger icon={<StopOutlined />}>
                  取消
                </Button>
              </Popconfirm>
            </>
          )}
          {['COMPLETED', 'FAILED', 'CANCELLED'].includes(record.status) && (
            <Popconfirm
              title="确定删除此任务？"
              onConfirm={() => handleDelete(record.taskId)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" danger icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1>任务管理</h1>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => navigate('/tasks/create')}
        >
          创建任务
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={tasks}
        rowKey="taskId"
        loading={loading}
      />
    </div>
  )
}

export default TaskList
