# API 使用示例

## 完整工作流示例

### 场景 1：标准训练流

#### 步骤 1：上传数据集

```bash
curl -X POST http://localhost:8080/api/datasets/upload \
  -F "file=@math_dataset.json" \
  -F "name=数学推理数据集" \
  -F "description=小学数学推理题" \
  -F "datasetType=training" \
  -F "domain=math" \
  -F "userId=1"
```

**响应**：
```json
{
  "datasetId": "dataset_abc123",
  "name": "数学推理数据集",
  "storagePath": "s3://bucket/datasets/1/dataset_abc123/math_dataset.json",
  "fileSize": 1048576,
  "domain": "math",
  "userId": 1,
  "isOptimized": false,
  "createdAt": "2026-01-09T10:00:00"
}
```

#### 步骤 2：创建标准训练任务

```bash
curl -X POST http://localhost:8080/api/tasks/standard \
  -H "Content-Type: application/json" \
  -d '{
    "taskName": "数学推理模型训练",
    "modelName": "qwen-7b",
    "datasetId": "dataset_abc123",
    "userId": 1,
    "hyperparameters": "{\"learning_rate\": 0.001, \"epochs\": 10, \"batch_size\": 32}"
  }'
```

**响应**：
```json
{
  "taskId": "task_xyz789",
  "taskName": "数学推理模型训练",
  "taskMode": "STANDARD",
  "status": "PENDING",
  "modelName": "qwen-7b",
  "datasetId": "dataset_abc123",
  "userId": 1,
  "currentIteration": 0,
  "createdAt": "2026-01-09T10:05:00"
}
```

#### 步骤 3：启动任务

```bash
curl -X POST http://localhost:8080/api/tasks/task_xyz789/start
```

**响应**：
```json
{
  "message": "任务已启动",
  "taskId": "task_xyz789"
}
```

#### 步骤 4：查询任务状态

```bash
# 轮询查询任务状态
curl http://localhost:8080/api/tasks/task_xyz789
```

**响应（优化阶段）**：
```json
{
  "taskId": "task_xyz789",
  "taskName": "数学推理模型训练",
  "taskMode": "STANDARD",
  "status": "OPTIMIZING",
  "currentDatasetId": "dataset_abc123",
  "currentIteration": 0,
  "startedAt": "2026-01-09T10:05:30"
}
```

**响应（训练阶段）**：
```json
{
  "taskId": "task_xyz789",
  "status": "TRAINING",
  "currentDatasetId": "dataset_opt_def456",
  "currentIteration": 0
}
```

**响应（评估阶段）**：
```json
{
  "taskId": "task_xyz789",
  "status": "EVALUATING",
  "latestModelPath": "s3://bucket/models/task_xyz789_iter0.pth",
  "currentIteration": 0
}
```

**响应（完成）**：
```json
{
  "taskId": "task_xyz789",
  "status": "COMPLETED",
  "latestModelPath": "s3://bucket/models/task_xyz789_iter0.pth",
  "latestEvaluationPath": "s3://bucket/evaluations/task_xyz789_iter0.json",
  "latestScore": 0.88,
  "completedAt": "2026-01-09T10:45:00"
}
```

#### 步骤 5：查询执行历史

```bash
curl http://localhost:8080/api/tasks/task_xyz789/executions
```

**响应**：
```json
[
  {
    "taskId": "task_xyz789",
    "iteration": 0,
    "phase": "optimization",
    "status": "completed",
    "inputDatasetId": "dataset_abc123",
    "outputDatasetId": "dataset_opt_def456",
    "startedAt": "2026-01-09T10:05:30",
    "completedAt": "2026-01-09T10:15:00",
    "durationSeconds": 570
  },
  {
    "taskId": "task_xyz789",
    "iteration": 0,
    "phase": "training",
    "status": "completed",
    "inputDatasetId": "dataset_opt_def456",
    "modelPath": "s3://bucket/models/task_xyz789_iter0.pth",
    "startedAt": "2026-01-09T10:15:00",
    "completedAt": "2026-01-09T10:40:00",
    "durationSeconds": 1500
  },
  {
    "taskId": "task_xyz789",
    "iteration": 0,
    "phase": "evaluation",
    "status": "completed",
    "evaluationPath": "s3://bucket/evaluations/task_xyz789_iter0.json",
    "score": 0.88,
    "startedAt": "2026-01-09T10:40:00",
    "completedAt": "2026-01-09T10:45:00",
    "durationSeconds": 300
  }
]
```

---

### 场景 2：持续学习流

#### 步骤 1：创建持续学习任务

```bash
curl -X POST http://localhost:8080/api/tasks/continuous \
  -H "Content-Type: application/json" \
  -d '{
    "taskName": "持续学习任务",
    "modelName": "qwen-7b",
    "datasetId": "dataset_abc123",
    "userId": 1,
    "hyperparameters": "{\"learning_rate\": 0.001, \"epochs\": 5}",
    "maxIterations": 5,
    "performanceThreshold": 0.95
  }'
```

**响应**：
```json
{
  "taskId": "task_cont001",
  "taskName": "持续学习任务",
  "taskMode": "CONTINUOUS",
  "status": "PENDING",
  "maxIterations": 5,
  "performanceThreshold": 0.95,
  "currentIteration": 0
}
```

#### 步骤 2：启动任务

```bash
curl -X POST http://localhost:8080/api/tasks/task_cont001/start
```

#### 步骤 3：监控迭代过程

```bash
# 第一轮迭代
curl http://localhost:8080/api/tasks/task_cont001
```

**响应（第一轮完成）**：
```json
{
  "taskId": "task_cont001",
  "status": "LOOPING",
  "currentIteration": 1,
  "latestScore": 0.88
}
```

**响应（第二轮完成）**：
```json
{
  "taskId": "task_cont001",
  "status": "LOOPING",
  "currentIteration": 2,
  "latestScore": 0.91
}
```

**响应（第三轮完成）**：
```json
{
  "taskId": "task_cont001",
  "status": "LOOPING",
  "currentIteration": 3,
  "latestScore": 0.94
}
```

**响应（达到阈值，完成）**：
```json
{
  "taskId": "task_cont001",
  "status": "COMPLETED",
  "currentIteration": 4,
  "latestScore": 0.96,
  "completedAt": "2026-01-09T14:30:00"
}
```

#### 步骤 4：查看所有迭代的执行记录

```bash
curl http://localhost:8080/api/tasks/task_cont001/executions
```

**响应**：
```json
[
  {
    "iteration": 3,
    "phase": "evaluation",
    "score": 0.96,
    "completedAt": "2026-01-09T14:30:00"
  },
  {
    "iteration": 3,
    "phase": "training",
    "modelPath": "s3://bucket/models/task_cont001_iter3.pth",
    "completedAt": "2026-01-09T14:25:00"
  },
  {
    "iteration": 3,
    "phase": "optimization",
    "outputDatasetId": "dataset_opt_iter3",
    "completedAt": "2026-01-09T14:10:00"
  },
  {
    "iteration": 2,
    "phase": "evaluation",
    "score": 0.94,
    "completedAt": "2026-01-09T13:50:00"
  },
  // ... 更多记录
]
```

---

### 场景 3：任务控制

#### 暂停任务

```bash
curl -X POST http://localhost:8080/api/tasks/task_xyz789/suspend
```

**响应**：
```json
{
  "message": "任务已暂停",
  "taskId": "task_xyz789"
}
```

#### 取消任务

```bash
curl -X POST http://localhost:8080/api/tasks/task_xyz789/cancel
```

**响应**：
```json
{
  "message": "任务已取消",
  "taskId": "task_xyz789"
}
```

#### 删除任务

```bash
curl -X DELETE http://localhost:8080/api/tasks/task_xyz789
```

**响应**：
```json
{
  "message": "任务已删除",
  "taskId": "task_xyz789"
}
```

---

### 场景 4：数据集管理

#### 查询用户的所有数据集

```bash
curl http://localhost:8080/api/datasets/user/1
```

**响应**：
```json
[
  {
    "datasetId": "dataset_abc123",
    "name": "数学推理数据集",
    "domain": "math",
    "isOptimized": false,
    "createdAt": "2026-01-09T10:00:00"
  },
  {
    "datasetId": "dataset_opt_def456",
    "name": "数学推理模型训练_optimized_iter0",
    "domain": "math",
    "isOptimized": true,
    "sourceDatasetId": "dataset_abc123",
    "createdAt": "2026-01-09T10:15:00"
  }
]
```

#### 查询优化后的数据集

```bash
curl http://localhost:8080/api/datasets/dataset_abc123/optimized
```

**响应**：
```json
[
  {
    "datasetId": "dataset_opt_def456",
    "name": "数学推理模型训练_optimized_iter0",
    "sourceDatasetId": "dataset_abc123",
    "isOptimized": true
  },
  {
    "datasetId": "dataset_opt_iter1",
    "name": "持续学习任务_optimized_iter1",
    "sourceDatasetId": "dataset_abc123",
    "isOptimized": true
  }
]
```

#### 获取数据集下载URL

```bash
curl http://localhost:8080/api/datasets/dataset_abc123/download-url
```

**响应**：
```json
{
  "datasetId": "dataset_abc123",
  "downloadUrl": "https://s3.amazonaws.com/bucket/datasets/1/dataset_abc123/math_dataset.json?X-Amz-Expires=3600&..."
}
```

#### 更新数据集元数据

```bash
curl -X PUT http://localhost:8080/api/datasets/dataset_abc123 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "数学推理数据集 v2",
    "description": "更新后的描述",
    "sampleCount": 1000
  }'
```

#### 删除数据集

```bash
curl -X DELETE http://localhost:8080/api/datasets/dataset_abc123
```

---

## 错误处理

### 任务不存在

```bash
curl http://localhost:8080/api/tasks/invalid_task_id
```

**响应**：
```json
{
  "status": 404,
  "error": "Not Found",
  "message": "任务不存在: invalid_task_id"
}
```

### 状态转换错误

```bash
# 尝试启动已完成的任务
curl -X POST http://localhost:8080/api/tasks/task_xyz789/start
```

**响应**：
```json
{
  "error": "任务状态不允许启动: COMPLETED"
}
```

### 数据集不存在

```bash
curl -X POST http://localhost:8080/api/tasks/standard \
  -H "Content-Type: application/json" \
  -d '{
    "datasetId": "invalid_dataset_id",
    ...
  }'
```

**响应**：
```json
{
  "error": "数据集不存在: invalid_dataset_id"
}
```

---

## 监控与调试

### 查询用户的所有任务

```bash
curl http://localhost:8080/api/tasks/user/1
```

### 查询当前迭代的执行记录

```bash
curl http://localhost:8080/api/tasks/task_cont001/executions/current
```

### 查询数据优化服务健康状态

```bash
curl http://localhost:8080/api/data-optimization/health
```

**响应**：
```json
{
  "status": "healthy",
  "service": "data-optimization-service",
  "version": "3.1.0",
  "llm_available": true
}
```

---

**版本**：1.0.0  
**更新日期**：2026-01-09
