import axios from 'axios'
import type { 
  Dataset, 
  MLTask, 
  TaskExecution, 
  CreateStandardTaskRequest, 
  CreateContinuousTaskRequest 
} from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 数据集 API
export const datasetApi = {
  upload: (formData: FormData) => 
    api.post<Dataset>('/datasets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
  
  getById: (datasetId: string) => 
    api.get<Dataset>(`/datasets/${datasetId}`),
  
  getUserDatasets: (userId: number) => 
    api.get<Dataset[]>(`/datasets/user/${userId}`),
  
  getUserDatasetsByDomain: (userId: number, domain: string) => 
    api.get<Dataset[]>(`/datasets/user/${userId}/domain/${domain}`),
  
  updateMetadata: (datasetId: string, data: Partial<Dataset>) => 
    api.put<Dataset>(`/datasets/${datasetId}`, data),
  
  delete: (datasetId: string, userId: number) => 
    api.delete(`/datasets/${datasetId}`, { params: { userId } }),
  
  getDownloadUrl: (datasetId: string) => 
    api.get<{ datasetId: string; downloadUrl: string }>(`/datasets/${datasetId}/download-url`),
  
  getOptimizedDatasets: (datasetId: string) => 
    api.get<Dataset[]>(`/datasets/${datasetId}/optimized`),
}

// 任务 API
export const taskApi = {
  createStandard: (data: CreateStandardTaskRequest) => 
    api.post<MLTask>('/tasks/standard', data),
  
  createContinuous: (data: CreateContinuousTaskRequest) => 
    api.post<MLTask>('/tasks/continuous', data),
  
  start: (taskId: string) => 
    api.post<{ message: string; taskId: string }>(`/tasks/${taskId}/start`),
  
  suspend: (taskId: string) => 
    api.post<{ message: string; taskId: string }>(`/tasks/${taskId}/suspend`),
  
  cancel: (taskId: string) => 
    api.post<{ message: string; taskId: string }>(`/tasks/${taskId}/cancel`),
  
  getById: (taskId: string) => 
    api.get<MLTask>(`/tasks/${taskId}`),
  
  getUserTasks: (userId: number) => 
    api.get<MLTask[]>(`/tasks/user/${userId}`),
  
  getExecutions: (taskId: string) => 
    api.get<TaskExecution[]>(`/tasks/${taskId}/executions`),
  
  getCurrentIterationExecutions: (taskId: string) => 
    api.get<TaskExecution[]>(`/tasks/${taskId}/executions/current`),
  
  delete: (taskId: string) => 
    api.delete(`/tasks/${taskId}`),
}

export default api
