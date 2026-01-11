import type { TaskStatus } from '@/types'

export const getStatusColor = (status: TaskStatus): string => {
  const colorMap: Record<TaskStatus, string> = {
    PENDING: 'default',
    OPTIMIZING: 'processing',
    TRAINING: 'processing',
    EVALUATING: 'processing',
    LOOPING: 'processing',
    COMPLETED: 'success',
    FAILED: 'error',
    CANCELLED: 'default',
    SUSPENDED: 'warning',
  }
  return colorMap[status] || 'default'
}

export const getStatusText = (status: TaskStatus): string => {
  const textMap: Record<TaskStatus, string> = {
    PENDING: '待处理',
    OPTIMIZING: '数据优化中',
    TRAINING: '训练中',
    EVALUATING: '评估中',
    LOOPING: '循环中',
    COMPLETED: '已完成',
    FAILED: '失败',
    CANCELLED: '已取消',
    SUSPENDED: '已暂停',
  }
  return textMap[status] || status
}

export const formatFileSize = (bytes?: number): string => {
  if (!bytes) return '-'
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`
}

export const formatDuration = (seconds?: number): string => {
  if (!seconds) return '-'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}小时${minutes}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟${secs}秒`
  } else {
    return `${secs}秒`
  }
}

export const getPhaseText = (phase: string): string => {
  const phaseMap: Record<string, string> = {
    optimization: '数据优化',
    training: '模型训练',
    evaluation: '模型评估',
  }
  return phaseMap[phase] || phase
}
