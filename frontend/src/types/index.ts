export type TaskStatus = 
  | 'PENDING' 
  | 'OPTIMIZING' 
  | 'TRAINING' 
  | 'EVALUATING' 
  | 'COMPLETED' 
  | 'LOOPING' 
  | 'FAILED' 
  | 'CANCELLED' 
  | 'SUSPENDED'

export type TaskMode = 'STANDARD' | 'CONTINUOUS'

export interface Dataset {
  id?: number
  datasetId: string
  name: string
  description?: string
  storagePath: string
  fileSize?: number
  sampleCount?: number
  datasetType?: string
  domain: string
  userId: number
  isOptimized: boolean
  sourceDatasetId?: string
  createdAt: string
  updatedAt?: string
}

export interface MLTask {
  id?: number
  taskId: string
  taskName: string
  taskMode: TaskMode
  status: TaskStatus
  modelName: string
  datasetId: string
  currentDatasetId?: string
  userId: number
  currentIteration: number
  maxIterations?: number
  performanceThreshold?: number
  hyperparameters?: string
  latestModelPath?: string
  latestEvaluationPath?: string
  latestScore?: number
  errorMessage?: string
  createdAt: string
  updatedAt?: string
  startedAt?: string
  completedAt?: string
}

export interface TaskExecution {
  id?: number
  taskId: string
  iteration: number
  phase: 'optimization' | 'training' | 'evaluation'
  status: string
  inputDatasetId?: string
  outputDatasetId?: string
  modelPath?: string
  evaluationPath?: string
  score?: number
  logPath?: string
  details?: string
  errorMessage?: string
  startedAt: string
  completedAt?: string
  durationSeconds?: number
}

export interface CreateStandardTaskRequest {
  taskName: string
  modelName: string
  datasetId: string
  userId: number
  hyperparameters?: string
}

export interface CreateContinuousTaskRequest extends CreateStandardTaskRequest {
  maxIterations?: number
  performanceThreshold?: number
}
