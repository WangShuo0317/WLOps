import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Card, 
  Descriptions, 
  Tag, 
  Button, 
  Space, 
  Timeline, 
  message,
  Spin,
  Empty,
} from 'antd'
import { 
  ArrowLeftOutlined, 
  PlayCircleOutlined, 
  PauseCircleOutlined, 
  StopOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons'
import { taskApi } from '@/services/api'
import { getStatusColor, getStatusText, getPhaseText, formatDuration } from '@/utils/helpers'
import type { MLTask, TaskExecution } from '@/types'
import dayjs from 'dayjs'

const TaskDetail = () => {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const [task, setTask] = useState<MLTask | null>(null)
  const [executions, setExecutions] = useState<TaskExecution[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (taskId) {
      loadTaskDetail()
      const interval = setInterval(loadTaskDetail, 3000) // 每3秒刷新
      return () => clearInterval(interval)
    }
  }, [taskId])

  const loadTaskDetail = async () => {
    if (!taskId) return
    
    try {
      const [taskRes, executionsRes] = await Promise.all([
        taskApi.getById(taskId),
        taskApi.getExecutions(taskId),
      ])
      setTask(taskRes.data)
      setExecutions(executionsRes.data)
    } catch (error) {
      message.error('加载任务详情失败')
    } finally {
      setLoading(false)
    }
  }

  const handleStart = async () => {
    if (!taskId) return
    try {
      await taskApi.start(taskId)
      message.success('任务已启动')
      loadTaskDetail()
    } catch (error: any) {
      message.error(error.response?.data?.error || '启动失败')
    }
  }

  const handleSuspend = async () => {
    if (!taskId) return
    try {
      await taskApi.suspend(taskId)
      message.success('任务已暂停')
      loadTaskDetail()
    } catch (error) {
      message.error('暂停失败')
    }
  }

  const handleCancel = async () => {
    if (!taskId) return
    try {
      await taskApi.cancel(taskId)
      message.success('任务已取消')
      loadTaskDetail()
    } catch (error) {
      message.error('取消失败')
    }
  }

  const getTimelineIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'running':
        return <SyncOutlined spin style={{ color: '#1890ff' }} />
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />
    }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!task) {
    return <Empty description="任务不存在" />
  }

  const hyperparameters = task.hyperparameters ? JSON.parse(task.hyperparameters) : {}

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/tasks')}>
          返回
        </Button>
      </div>

      <Card 
        title={task.taskName}
        extra={
          <Space>
            {task.status === 'PENDING' && (
              <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleStart}>
                启动
              </Button>
            )}
            {['OPTIMIZING', 'TRAINING', 'EVALUATING', 'LOOPING'].includes(task.status) && (
              <>
                <Button icon={<PauseCircleOutlined />} onClick={handleSuspend}>
                  暂停
                </Button>
                <Button danger icon={<StopOutlined />} onClick={handleCancel}>
                  取消
                </Button>
              </>
            )}
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        <Descriptions column={2}>
          <Descriptions.Item label="任务ID">{task.taskId}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={getStatusColor(task.status)}>
              {getStatusText(task.status)}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="任务模式">
            <Tag color={task.taskMode === 'STANDARD' ? 'blue' : 'purple'}>
              {task.taskMode === 'STANDARD' ? '标准训练流' : '持续学习流'}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="模型名称">{task.modelName}</Descriptions.Item>
          <Descriptions.Item label="当前迭代">
            {task.maxIterations 
              ? `${task.currentIteration}/${task.maxIterations}` 
              : task.currentIteration}
          </Descriptions.Item>
          {task.performanceThreshold && (
            <Descriptions.Item label="性能阈值">
              {task.performanceThreshold}
            </Descriptions.Item>
          )}
          <Descriptions.Item label="最新分数">
            {task.latestScore ? task.latestScore.toFixed(4) : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="数据集ID">{task.datasetId}</Descriptions.Item>
          <Descriptions.Item label="创建时间">
            {dayjs(task.createdAt).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          {task.startedAt && (
            <Descriptions.Item label="开始时间">
              {dayjs(task.startedAt).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
          )}
          {task.completedAt && (
            <Descriptions.Item label="完成时间">
              {dayjs(task.completedAt).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
          )}
        </Descriptions>

        <Descriptions column={1} style={{ marginTop: 16 }}>
          <Descriptions.Item label="超参数">
            <pre style={{ margin: 0 }}>
              {JSON.stringify(hyperparameters, null, 2)}
            </pre>
          </Descriptions.Item>
        </Descriptions>

        {task.errorMessage && (
          <Descriptions column={1} style={{ marginTop: 16 }}>
            <Descriptions.Item label="错误信息">
              <span style={{ color: '#ff4d4f' }}>{task.errorMessage}</span>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Card>

      <Card title="执行历史">
        {executions.length === 0 ? (
          <Empty description="暂无执行记录" />
        ) : (
          <Timeline>
            {executions.map((exec, index) => (
              <Timeline.Item key={exec.id || index} dot={getTimelineIcon(exec.status)}>
                <div>
                  <strong>
                    迭代 {exec.iteration} - {getPhaseText(exec.phase)}
                  </strong>
                  <Tag 
                    color={exec.status === 'completed' ? 'success' : exec.status === 'failed' ? 'error' : 'processing'}
                    style={{ marginLeft: 8 }}
                  >
                    {exec.status === 'completed' ? '已完成' : exec.status === 'failed' ? '失败' : '运行中'}
                  </Tag>
                </div>
                <div style={{ marginTop: 8, color: '#666' }}>
                  <div>开始时间: {dayjs(exec.startedAt).format('YYYY-MM-DD HH:mm:ss')}</div>
                  {exec.completedAt && (
                    <div>完成时间: {dayjs(exec.completedAt).format('YYYY-MM-DD HH:mm:ss')}</div>
                  )}
                  {exec.durationSeconds && (
                    <div>耗时: {formatDuration(exec.durationSeconds)}</div>
                  )}
                  {exec.score && (
                    <div>评估分数: {exec.score.toFixed(4)}</div>
                  )}
                  {exec.outputDatasetId && (
                    <div>输出数据集: {exec.outputDatasetId}</div>
                  )}
                  {exec.modelPath && (
                    <div>模型路径: {exec.modelPath}</div>
                  )}
                  {exec.errorMessage && (
                    <div style={{ color: '#ff4d4f' }}>错误: {exec.errorMessage}</div>
                  )}
                </div>
              </Timeline.Item>
            ))}
          </Timeline>
        )}
      </Card>
    </div>
  )
}

export default TaskDetail
