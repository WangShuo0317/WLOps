# 项目结构

## 目录树

```
WLOps/springboot-backend/
├── src/main/java/com/imts/
│   ├── ImtsApplication.java                    # Spring Boot 启动类
│   │
│   ├── enums/                                  # 枚举类 ✨ NEW
│   │   ├── TaskStatus.java                     # 任务状态枚举（状态机）
│   │   └── TaskMode.java                       # 任务模式枚举
│   │
│   ├── entity/                                 # 实体类
│   │   ├── Dataset.java                        # 数据集实体 ✨ NEW
│   │   ├── MLTask.java                         # ML任务实体 ✨ NEW
│   │   ├── TaskExecution.java                  # 任务执行记录 ✨ NEW
│   │   └── TrainingJob.java                    # 旧训练任务实体 ⚠️ 待废弃
│   │
│   ├── repository/                             # 数据访问层
│   │   ├── DatasetRepository.java              # 数据集仓储 ✨ NEW
│   │   ├── MLTaskRepository.java               # ML任务仓储 ✨ NEW
│   │   ├── TaskExecutionRepository.java        # 执行记录仓储 ✨ NEW
│   │   └── TrainingJobRepository.java          # 旧仓储 ⚠️ 待废弃
│   │
│   ├── orchestrator/                           # 工作流编排器 ✨ NEW
│   │   └── WorkflowOrchestrator.java           # 核心编排逻辑
│   │       ├── executeStandardPipeline()       # 标准训练流
│   │       ├── executeContinuousLearningLoop() # 持续学习流
│   │       ├── executeIteration()              # 单次迭代
│   │       ├── executeOptimization()           # 数据优化
│   │       ├── executeTraining()               # 模型训练
│   │       └── executeEvaluation()             # 模型评估
│   │
│   ├── service/                                # 业务逻辑层
│   │   ├── TaskManagementService.java          # 任务管理服务 ✨ NEW
│   │   ├── DatasetManagementService.java       # 数据集管理服务 ✨ NEW
│   │   ├── DataOptimizationService.java        # 数据优化服务
│   │   └── TrainingService.java                # 旧训练服务 ⚠️ 待废弃
│   │
│   ├── controller/                             # REST API 控制器
│   │   ├── TaskController.java                 # 任务管理API ✨ NEW
│   │   ├── DatasetController.java              # 数据集管理API ✨ NEW
│   │   ├── DataOptimizationController.java     # 数据优化API
│   │   └── TrainingController.java             # 旧训练API ⚠️ 待废弃
│   │
│   ├── client/                                 # 微服务客户端
│   │   ├── DataAnalyzerServiceClient.java      # 数据优化服务客户端
│   │   ├── TrainingServiceClient.java          # 训练服务客户端
│   │   └── EvaluationServiceClient.java        # 评估服务客户端
│   │
│   └── dto/                                    # 数据传输对象
│       ├── analyzer/
│       │   ├── OptimizationRequest.java
│       │   ├── OptimizationResponse.java
│       │   ├── OptimizationResult.java
│       │   └── HealthResponse.java             ✨ NEW
│       └── training/
│           ├── TrainingRequest.java
│           ├── TrainingResponse.java
│           └── JobStatus.java
│
├── src/main/resources/
│   ├── application.yml                         # 应用配置
│   └── db/migration/                           # 数据库迁移脚本（待添加）
│
├── docs/                                       # 文档目录 ✨ NEW
│   ├── ARCHITECTURE.md                         # 系统架构文档
│   ├── API_EXAMPLES.md                         # API使用示例
│   ├── REFACTORING_SUMMARY.md                  # 重构总结
│   ├── QUICK_START.md                          # 快速启动指南
│   ├── INTEGRATION_EXAMPLE.md                  # 集成示例
│   ├── TESTING_GUIDE.md                        # 测试指南
│   └── UPDATE_SUMMARY.md                       # 更新总结
│
├── pom.xml                                     # Maven 配置
└── README.md                                   # 项目说明
```

---

## 核心模块说明

### 1. 枚举类 (enums/) ✨ NEW

#### TaskStatus.java
**职责**：定义任务状态机

**状态列表**：
- `PENDING` - 待处理
- `OPTIMIZING` - 数据优化中
- `TRAINING` - 训练中
- `EVALUATING` - 评估中
- `COMPLETED` - 已完成
- `LOOPING` - 循环中（持续学习）
- `FAILED` - 已失败
- `CANCELLED` - 已取消
- `SUSPENDED` - 已暂停

**核心方法**：
- `canTransitionTo(TaskStatus target)` - 验证状态转换
- `isTerminal()` - 是否为终态
- `isRunning()` - 是否为运行态

#### TaskMode.java
**职责**：定义任务模式

**模式列表**：
- `STANDARD` - 标准训练流
- `CONTINUOUS` - 持续学习流

---

### 2. 实体类 (entity/)

#### Dataset.java ✨ NEW
**职责**：数据集元数据管理

**关键字段**：
- `datasetId` - 唯一标识
- `storagePath` - 对象存储路径
- `isOptimized` - 是否优化后的数据集
- `sourceDatasetId` - 源数据集ID（用于追踪）

**约束**：
- ✅ 仅存储元数据
- ❌ 不包含实际数据内容

#### MLTask.java ✨ NEW
**职责**：机器学习任务管理

**关键字段**：
- `taskMode` - 任务模式（STANDARD/CONTINUOUS）
- `status` - 任务状态（状态机）
- `currentIteration` - 当前迭代轮次
- `maxIterations` - 最大迭代次数
- `performanceThreshold` - 性能阈值

**核心方法**：
- `updateStatus(TaskStatus)` - 更新状态（带验证）
- `shouldContinueIteration()` - 判断是否继续迭代
- `incrementIteration()` - 增加迭代次数

#### TaskExecution.java ✨ NEW
**职责**：记录任务执行详情

**记录内容**：
- 优化阶段：输入/输出数据集
- 训练阶段：模型路径、训练指标
- 评估阶段：评估报告、分数

---

### 3. 工作流编排器 (orchestrator/) ✨ NEW

#### WorkflowOrchestrator.java
**职责**：核心业务编排逻辑

**核心流程**：

##### 标准训练流
```java
executeStandardPipeline(MLTask task)
    → executeOptimization()      // 数据优化
    → executeTraining()           // 模型训练
    → executeEvaluation()         // 模型评估
    → COMPLETED
```

##### 持续学习流
```java
executeContinuousLearningLoop(MLTask task)
    → executeIteration(iteration)
        → getImprovementSuggestions()     // 获取改进建议
        → executeOptimizationWithFeedback() // 优化（带反馈）
        → executeTraining()                // 训练
        → executeEvaluation()              // 评估
    → 检查终止条件
    → 如果未达到，继续下一轮迭代
    → 如果达到，COMPLETED
```

**微服务协调**：
- 调用 `DataAnalyzerServiceClient` 进行数据优化
- 调用 `TrainingServiceClient` 进行模型训练
- 调用 `EvaluationServiceClient` 进行模型评估

---

### 4. 服务层 (service/)

#### TaskManagementService.java ✨ NEW
**职责**：任务生命周期管理

**核心方法**：
- `createStandardTask()` - 创建标准训练任务
- `createContinuousTask()` - 创建持续学习任务
- `startTask()` - 启动任务
- `suspendTask()` - 暂停任务
- `cancelTask()` - 取消任务
- `getTaskExecutions()` - 查询执行历史

#### DatasetManagementService.java ✨ NEW
**职责**：数据集管理

**核心方法**：
- `uploadDataset()` - 流式上传数据集
- `getDataset()` - 查询数据集详情
- `getUserDatasets()` - 查询用户数据集
- `getOptimizedDatasets()` - 查询优化后的数据集
- `deleteDataset()` - 删除数据集

**约束**：
- ✅ 仅负责文件上传和元数据管理
- ❌ 严禁在此阶段进行数据清洗或优化

---

### 5. 控制器层 (controller/)

#### TaskController.java ✨ NEW
**REST API 端点**：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/tasks/standard` | 创建标准训练任务 |
| POST | `/api/tasks/continuous` | 创建持续学习任务 |
| POST | `/api/tasks/{taskId}/start` | 启动任务 |
| POST | `/api/tasks/{taskId}/suspend` | 暂停任务 |
| POST | `/api/tasks/{taskId}/cancel` | 取消任务 |
| GET | `/api/tasks/{taskId}` | 查询任务详情 |
| GET | `/api/tasks/user/{userId}` | 查询用户任务 |
| GET | `/api/tasks/{taskId}/executions` | 查询执行历史 |
| DELETE | `/api/tasks/{taskId}` | 删除任务 |

#### DatasetController.java ✨ NEW
**REST API 端点**：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/datasets/upload` | 上传数据集 |
| GET | `/api/datasets/{datasetId}` | 查询数据集详情 |
| GET | `/api/datasets/user/{userId}` | 查询用户数据集 |
| PUT | `/api/datasets/{datasetId}` | 更新元数据 |
| DELETE | `/api/datasets/{datasetId}` | 删除数据集 |
| GET | `/api/datasets/{datasetId}/download-url` | 获取下载URL |
| GET | `/api/datasets/{datasetId}/optimized` | 查询优化后的数据集 |

---

### 6. 微服务客户端 (client/)

#### DataAnalyzerServiceClient.java
**调用服务**：数据优化服务 (Port 8002)

**核心方法**：
- `optimizeDatasetSync()` - 同步优化
- `optimizeDatasetAsync()` - 异步优化
- `getOptimizationResult()` - 查询结果
- `loadKnowledgeBase()` - 加载知识库

#### TrainingServiceClient.java
**调用服务**：模型训练服务 (Port 8004)

**核心方法**：
- `createTraining()` - 创建训练任务
- `getJobStatus()` - 查询训练状态
- `stopJob()` - 停止训练

#### EvaluationServiceClient.java
**调用服务**：模型评估服务 (Port 8003)

**核心方法**：
- `evaluate()` - 启动评估
- `getEvaluationResult()` - 查询评估结果

---

## 文档结构

### 核心文档

| 文档 | 说明 |
|------|------|
| `ARCHITECTURE.md` | 系统架构设计文档 |
| `API_EXAMPLES.md` | API 使用示例和场景 |
| `REFACTORING_SUMMARY.md` | 重构总结和变更说明 |
| `QUICK_START.md` | 快速启动指南 |
| `INTEGRATION_EXAMPLE.md` | 集成示例 |
| `TESTING_GUIDE.md` | 测试指南 |
| `UPDATE_SUMMARY.md` | 更新总结 |

---

## 待废弃的文件 ⚠️

以下文件为旧版本实现，将在后续版本中移除：

- `entity/TrainingJob.java` - 被 `MLTask.java` 替代
- `repository/TrainingJobRepository.java` - 被 `MLTaskRepository.java` 替代
- `service/TrainingService.java` - 被 `TaskManagementService.java` 替代
- `controller/TrainingController.java` - 被 `TaskController.java` 替代

---

## 技术栈

### 后端框架
- Spring Boot 3.x
- Spring Data JPA
- Spring WebFlux (Reactive)

### 数据库
- PostgreSQL 14+

### 对象存储
- MinIO / AWS S3

### 微服务通信
- HTTP/REST
- WebClient (Reactive)

### 构建工具
- Maven 3.8+

---

## 版本信息

- **当前版本**：2.0.0
- **重构日期**：2026-01-09
- **Java 版本**：17+
- **Spring Boot 版本**：3.x

---

## 下一步开发计划

### 短期（1-2周）
- [ ] 数据库迁移脚本（Flyway）
- [ ] 对象存储集成（MinIO/S3）
- [ ] 用户认证与授权（JWT）
- [ ] 单元测试覆盖

### 中期（1个月）
- [ ] 消息队列集成（RabbitMQ）
- [ ] 异步任务处理
- [ ] 监控与日志（Prometheus + Grafana）
- [ ] API 文档（Swagger/OpenAPI）

### 长期（3个月）
- [ ] 分布式追踪（Zipkin）
- [ ] 服务网格（Istio）
- [ ] 容器化部署（Docker + Kubernetes）
- [ ] CI/CD 流水线

---

**项目结构文档版本**：1.0.0  
**更新日期**：2026-01-09
