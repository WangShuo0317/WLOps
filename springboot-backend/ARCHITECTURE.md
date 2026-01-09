# WLOps 系统架构文档

## 系统概述

WLOps 是一个基于微服务的自动化模型训练与持续演进平台，严格遵循"控制层与计算层解耦"的原则，实现从数据管理到模型持续学习的闭环流程。

## 核心架构原则

1. **控制层与计算层解耦**：Spring Boot 控制中心负责业务编排，Python 微服务负责计算任务
2. **状态机驱动**：任务生命周期由严格的状态机管理
3. **工作流编排**：支持标准训练流和持续学习流两种模式
4. **数据隔离**：用户数据严格隔离，基于角色的访问控制

---

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                     Spring Boot 控制中心                          │
│                   (Control System / Orchestrator)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 用户权限管理  │  │ 数据集管理    │  │ 任务管理      │          │
│  │    (IAM)     │  │   (Dataset)   │  │   (Task)     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  ┌─────────────────────────────────────────────────────┐        │
│  │          工作流编排器 (Workflow Orchestrator)         │        │
│  │  - 标准训练流 (Standard Pipeline)                     │        │
│  │  - 持续学习流 (Continuous Learning Loop)             │        │
│  │  - 任务状态机 (Task State Machine)                    │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │ HTTP/gRPC/消息队列
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│                      微服务集群 (Microservices)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  数据优化服务     │  │  模型训练服务     │  │  模型评估服务 │  │
│  │  (Data Optimizer) │  │  (Model Trainer) │  │  (Evaluator) │  │
│  │                   │  │                   │  │              │  │
│  │  Port: 8002       │  │  Port: 8004       │  │  Port: 8003  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│                      基础设施层 (Infrastructure)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 对象存储      │  │ 关系数据库    │  │ 消息队列      │          │
│  │ (MinIO/S3)   │  │ (PostgreSQL) │  │ (RabbitMQ)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 核心组件

### 1. 控制中心 (Spring Boot)

#### 1.1 用户权限管理 (IAM)
- **职责**：基于角色的访问控制，确保用户数据隔离
- **功能**：
  - 用户认证与授权
  - 角色权限管理
  - 数据访问控制

#### 1.2 数据集管理 (Dataset Manager)
- **职责**：数据集的CRUD操作和元数据管理
- **约束**：
  - ✅ 仅负责文件上传（流式上传至对象存储）
  - ✅ 仅负责元数据记录
  - ❌ 严禁在此阶段进行任何数据清洗或优化操作
- **核心类**：
  - `DatasetManagementService`
  - `DatasetController`
  - `Dataset` (实体)

#### 1.3 任务管理 (Task Manager)
- **职责**：管理训练任务的生命周期
- **功能**：
  - 任务创建（标准流/持续学习流）
  - 任务启动、暂停、取消
  - 任务状态查询
  - 执行历史记录
- **核心类**：
  - `TaskManagementService`
  - `TaskController`
  - `MLTask` (实体)
  - `TaskExecution` (执行记录)

#### 1.4 工作流编排器 (Workflow Orchestrator)
- **职责**：编排任务执行流程，协调微服务调用
- **核心类**：`WorkflowOrchestrator`
- **支持的工作流**：
  - 标准训练流 (Standard Pipeline)
  - 持续学习流 (Continuous Learning Loop)

---

### 2. 任务状态机 (Task State Machine)

```
状态转换图：

PENDING (待处理)
   │
   ↓
OPTIMIZING (数据优化中)
   │
   ↓
TRAINING (训练中)
   │
   ↓
EVALUATING (评估中)
   │
   ├─→ COMPLETED (已完成)  [标准流]
   │
   └─→ LOOPING (循环中)    [持续学习流]
        │
        └─→ OPTIMIZING (下一轮迭代)

终态：COMPLETED, FAILED, CANCELLED
```

#### 状态枚举 (`TaskStatus`)
- `PENDING` - 待处理
- `OPTIMIZING` - 数据优化中
- `TRAINING` - 训练中
- `EVALUATING` - 评估中
- `COMPLETED` - 已完成
- `LOOPING` - 循环中（持续学习）
- `FAILED` - 已失败
- `CANCELLED` - 已取消
- `SUSPENDED` - 已暂停

#### 状态转换规则
```java
public boolean canTransitionTo(TaskStatus target) {
    return switch (this) {
        case PENDING -> target == OPTIMIZING || target == CANCELLED;
        case OPTIMIZING -> target == TRAINING || target == FAILED || target == CANCELLED;
        case TRAINING -> target == EVALUATING || target == FAILED || target == CANCELLED;
        case EVALUATING -> target == COMPLETED || target == LOOPING || target == FAILED;
        case LOOPING -> target == OPTIMIZING || target == COMPLETED || target == CANCELLED;
        case SUSPENDED -> target == OPTIMIZING || target == TRAINING || target == EVALUATING;
        case COMPLETED, FAILED, CANCELLED -> false; // 终态不可转换
    };
}
```

---

### 3. 工作流模式

#### 模式 A：标准训练流 (Standard Pipeline)

**流程**：
```
1. 用户指定数据集ID，发起任务
   ↓
2. 控制中心调用数据优化服务
   - Input: 原始数据集路径
   - Output: 优化后的数据集路径 + 优化日志
   ↓
3. 优化完成后，调用模型训练服务
   - Input: 优化后的数据集路径 + 训练超参数
   - Output: 模型权重文件路径 + 训练Metrics
   ↓
4. 训练完成后，调用模型评估服务
   - Input: 模型权重路径 + 测试集
   - Output: 评估报告（Metrics + Bad Case分析 + 改进建议）
   ↓
5. 生成最终报告，任务结束
```

**代码实现**：
```java
private Mono<Void> executeStandardPipeline(MLTask task) {
    return executeOptimization(task, 0)
        .flatMap(optimizedDatasetId -> {
            task.updateStatus(TaskStatus.TRAINING);
            return executeTraining(task, 0, optimizedDatasetId);
        })
        .flatMap(modelPath -> {
            task.updateStatus(TaskStatus.EVALUATING);
            return executeEvaluation(task, 0, modelPath);
        })
        .flatMap(evaluationResult -> {
            task.updateStatus(TaskStatus.COMPLETED);
            return Mono.empty();
        });
}
```

#### 模式 B：持续学习流 (Continuous Learning Loop)

**流程**：
```
1. 执行标准训练流的所有步骤
   ↓
2. 评估结束时，控制中心检查任务配置
   ↓
3. 如果是持续学习模式：
   a. 解析评估报告中的"改进建议"
   b. 提取 Bad Case 特征
   ↓
4. 反馈循环：
   - 将"改进建议"和"当前数据集"再次送入数据优化服务
   - 触发新一轮的优化 -> 训练 -> 评估
   ↓
5. 检查终止条件：
   - 达到最大循环次数？
   - 达到性能阈值？
   ↓
6. 如果未达到终止条件，继续下一轮迭代
   如果达到终止条件，任务完成
```

**终止条件**：
- **最大迭代次数** (`maxIterations`)
- **性能阈值** (`performanceThreshold`)

**代码实现**：
```java
private Mono<Void> executeContinuousLearningLoop(MLTask task) {
    return executeIteration(task, task.getCurrentIteration())
        .flatMap(v -> {
            if (task.shouldContinueIteration()) {
                task.updateStatus(TaskStatus.LOOPING);
                task.incrementIteration();
                return executeContinuousLearningLoop(task); // 递归
            } else {
                task.updateStatus(TaskStatus.COMPLETED);
                return Mono.empty();
            }
        });
}

private Mono<Void> executeIteration(MLTask task, int iteration) {
    return getImprovementSuggestions(task.getLatestEvaluationPath())
        .flatMap(suggestions -> 
            executeOptimizationWithFeedback(task, iteration, suggestions))
        .flatMap(optimizedDatasetId -> 
            executeTraining(task, iteration, optimizedDatasetId))
        .flatMap(modelPath -> 
            executeEvaluation(task, iteration, modelPath));
}
```

---

### 4. 微服务集群

#### 4.1 数据优化服务 (Data Optimization Service)
- **端口**：8002
- **技术栈**：Python + FastAPI
- **职责**：
  - 数据清洗、增强、去重
  - 在持续学习模式下，解析评估报告中的 Bad Case 特征
  - 针对性地生成或筛选数据
- **API**：
  - `POST /api/v1/optimize` - 异步优化
  - `POST /api/v1/optimize/sync` - 同步优化
  - `GET /api/v1/optimize/{taskId}` - 查询结果

#### 4.2 模型训练服务 (Model Training Service)
- **端口**：8004
- **技术栈**：Python + PyTorch/TensorFlow
- **职责**：
  - 执行模型训练
  - 记录训练过程 Metrics
  - 保存模型权重
- **API**：
  - `POST /api/v1/train` - 启动训练
  - `GET /api/v1/train/{jobId}` - 查询状态

#### 4.3 模型评估服务 (Model Evaluation Service)
- **端口**：8003
- **技术栈**：Python + 评估框架
- **职责**：
  - 执行模型评估
  - 生成详细评估报告
  - 分析 Bad Case
  - 提供改进建议
- **API**：
  - `POST /api/v1/evaluate` - 启动评估
  - `GET /api/v1/evaluate/{taskId}` - 查询结果

---

## 数据模型

### 核心实体

#### 1. Dataset (数据集)
```java
@Entity
@Table(name = "datasets")
public class Dataset {
    private Long id;
    private String datasetId;        // 唯一标识
    private String name;             // 名称
    private String storagePath;      // 对象存储路径
    private Long fileSize;           // 文件大小
    private Integer sampleCount;     // 样本数量
    private String domain;           // 领域
    private Long userId;             // 所属用户
    private Boolean isOptimized;     // 是否优化后的数据集
    private String sourceDatasetId;  // 源数据集ID
}
```

#### 2. MLTask (机器学习任务)
```java
@Entity
@Table(name = "ml_tasks")
public class MLTask {
    private Long id;
    private String taskId;              // 唯一标识
    private String taskName;            // 任务名称
    private TaskMode taskMode;          // STANDARD / CONTINUOUS
    private TaskStatus status;          // 任务状态
    private String modelName;           // 模型名称
    private String datasetId;           // 原始数据集ID
    private String currentDatasetId;    // 当前使用的数据集ID
    private Long userId;                // 所属用户
    private Integer currentIteration;   // 当前迭代轮次
    private Integer maxIterations;      // 最大迭代次数
    private Double performanceThreshold; // 性能阈值
    private String latestModelPath;     // 最新模型路径
    private String latestEvaluationPath; // 最新评估报告路径
    private Double latestScore;         // 最新评估分数
}
```

#### 3. TaskExecution (任务执行记录)
```java
@Entity
@Table(name = "task_executions")
public class TaskExecution {
    private Long id;
    private String taskId;           // 所属任务ID
    private Integer iteration;       // 迭代轮次
    private String phase;            // optimization / training / evaluation
    private String status;           // running / completed / failed
    private String inputDatasetId;   // 输入数据集ID
    private String outputDatasetId;  // 输出数据集ID
    private String modelPath;        // 模型路径
    private String evaluationPath;   // 评估报告路径
    private Double score;            // 评估分数
    private LocalDateTime startedAt; // 开始时间
    private LocalDateTime completedAt; // 完成时间
}
```

---

## API 接口

### 任务管理 API

#### 创建标准训练任务
```http
POST /api/tasks/standard
Content-Type: application/json

{
  "taskName": "数学推理模型训练",
  "modelName": "qwen-7b",
  "datasetId": "dataset_abc123",
  "userId": 1,
  "hyperparameters": "{\"learning_rate\": 0.001, \"epochs\": 10}"
}
```

#### 创建持续学习任务
```http
POST /api/tasks/continuous
Content-Type: application/json

{
  "taskName": "持续学习任务",
  "modelName": "qwen-7b",
  "datasetId": "dataset_abc123",
  "userId": 1,
  "hyperparameters": "{\"learning_rate\": 0.001}",
  "maxIterations": 5,
  "performanceThreshold": 0.95
}
```

#### 启动任务
```http
POST /api/tasks/{taskId}/start
```

#### 查询任务详情
```http
GET /api/tasks/{taskId}
```

#### 查询任务执行历史
```http
GET /api/tasks/{taskId}/executions
```

### 数据集管理 API

#### 上传数据集
```http
POST /api/datasets/upload
Content-Type: multipart/form-data

file: <binary>
name: "数学推理数据集"
datasetType: "training"
domain: "math"
userId: 1
```

#### 查询数据集详情
```http
GET /api/datasets/{datasetId}
```

#### 查询用户的所有数据集
```http
GET /api/datasets/user/{userId}
```

---

## 部署架构

### 服务端口分配
- Spring Boot 控制中心：`8080`
- 数据优化服务：`8002`
- 模型评估服务：`8003`
- 模型训练服务：`8004`

### 数据库
- PostgreSQL：`5432`
- 表：`datasets`, `ml_tasks`, `task_executions`

### 对象存储
- MinIO/S3
- Bucket 结构：
  ```
  bucket/
  ├── datasets/{userId}/{datasetId}/
  ├── optimized/{datasetId}/
  ├── models/{taskId}/
  └── evaluations/{taskId}/
  ```

---

## 最佳实践

### 1. 任务创建
- 标准流：适用于一次性训练任务
- 持续学习流：适用于需要迭代优化的场景

### 2. 终止条件设置
- `maxIterations`：建议设置为 3-10 次
- `performanceThreshold`：根据业务需求设置（如 0.90, 0.95）

### 3. 数据集管理
- 使用流式上传处理大文件
- 定期清理优化后的临时数据集

### 4. 监控与日志
- 监控任务执行时长
- 记录每个阶段的详细日志
- 追踪性能提升趋势

---

**版本**：1.0.0  
**更新日期**：2026-01-09
