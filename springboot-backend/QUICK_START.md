# 快速启动指南

## 前置要求

- Java 17+
- Maven 3.8+
- PostgreSQL 14+
- MinIO 或 AWS S3（可选）
- Python 3.9+（用于微服务）

---

## 步骤 1：数据库初始化

### 创建数据库

```sql
CREATE DATABASE wlops;
```

### 创建表结构

```sql
-- 数据集表
CREATE TABLE datasets (
    id BIGSERIAL PRIMARY KEY,
    dataset_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    storage_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    sample_count INTEGER,
    dataset_type VARCHAR(50),
    domain VARCHAR(50),
    user_id BIGINT NOT NULL,
    is_optimized BOOLEAN DEFAULT FALSE,
    source_dataset_id VARCHAR(255),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP
);

-- ML任务表
CREATE TABLE ml_tasks (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    task_mode VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    model_name VARCHAR(255) NOT NULL,
    dataset_id VARCHAR(255) NOT NULL,
    current_dataset_id VARCHAR(255),
    user_id BIGINT NOT NULL,
    current_iteration INTEGER DEFAULT 0,
    max_iterations INTEGER,
    performance_threshold DOUBLE PRECISION,
    hyperparameters TEXT,
    latest_model_path VARCHAR(500),
    latest_evaluation_path VARCHAR(500),
    latest_score DOUBLE PRECISION,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 任务执行记录表
CREATE TABLE task_executions (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL,
    iteration INTEGER NOT NULL,
    phase VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    input_dataset_id VARCHAR(255),
    output_dataset_id VARCHAR(255),
    model_path VARCHAR(500),
    evaluation_path VARCHAR(500),
    score DOUBLE PRECISION,
    log_path VARCHAR(500),
    details TEXT,
    error_message TEXT,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    duration_seconds BIGINT
);

-- 创建索引
CREATE INDEX idx_datasets_user_id ON datasets(user_id);
CREATE INDEX idx_datasets_dataset_id ON datasets(dataset_id);
CREATE INDEX idx_ml_tasks_user_id ON ml_tasks(user_id);
CREATE INDEX idx_ml_tasks_task_id ON ml_tasks(task_id);
CREATE INDEX idx_ml_tasks_status ON ml_tasks(status);
CREATE INDEX idx_task_executions_task_id ON task_executions(task_id);
CREATE INDEX idx_task_executions_iteration ON task_executions(task_id, iteration);
```

---

## 步骤 2：配置 application.yml

```yaml
spring:
  application:
    name: wlops-control-center
  
  datasource:
    url: jdbc:postgresql://localhost:5432/wlops
    username: postgres
    password: your_password
    driver-class-name: org.postgresql.Driver
  
  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: true
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        format_sql: true

# 微服务配置
python-services:
  data-analyzer:
    url: http://localhost:8002
  training:
    url: http://localhost:8004
  evaluation:
    url: http://localhost:8003

# 对象存储配置（可选）
storage:
  type: minio  # 或 s3
  endpoint: http://localhost:9000
  access-key: minioadmin
  secret-key: minioadmin
  bucket: wlops-data

# 日志配置
logging:
  level:
    com.imts: DEBUG
    org.springframework.web: INFO
```

---

## 步骤 3：启动 Python 微服务

### 启动数据优化服务

```bash
cd WLOps/python-services/data-analyzer-service
python api.py
# 服务运行在 http://localhost:8002
```

### 启动模型训练服务

```bash
cd WLOps/python-services/training-service
python api.py
# 服务运行在 http://localhost:8004
```

### 启动模型评估服务

```bash
cd WLOps/python-services/evaluation-service
python api.py
# 服务运行在 http://localhost:8003
```

---

## 步骤 4：启动 Spring Boot 控制中心

```bash
cd WLOps/springboot-backend
mvn clean install
mvn spring-boot:run
# 服务运行在 http://localhost:8080
```

---

## 步骤 5：验证服务

### 检查健康状态

```bash
# 检查控制中心
curl http://localhost:8080/actuator/health

# 检查数据优化服务
curl http://localhost:8002/api/v1/health

# 检查训练服务
curl http://localhost:8004/api/v1/health

# 检查评估服务
curl http://localhost:8003/api/v1/health
```

---

## 步骤 6：运行第一个任务

### 6.1 上传数据集

创建测试数据文件 `test_dataset.json`:

```json
[
  {
    "question": "3 + 5 = ?",
    "answer": "8"
  },
  {
    "question": "10 - 3 = ?",
    "answer": "7"
  },
  {
    "question": "小明有10个苹果，吃了3个，还剩几个？",
    "answer": "7个"
  }
]
```

上传数据集：

```bash
curl -X POST http://localhost:8080/api/datasets/upload \
  -F "file=@test_dataset.json" \
  -F "name=测试数据集" \
  -F "description=用于测试的数学数据集" \
  -F "datasetType=training" \
  -F "domain=math" \
  -F "userId=1"
```

**响应示例**：
```json
{
  "datasetId": "dataset_abc123",
  "name": "测试数据集",
  "storagePath": "s3://bucket/datasets/1/dataset_abc123/test_dataset.json",
  "domain": "math",
  "userId": 1
}
```

### 6.2 创建标准训练任务

```bash
curl -X POST http://localhost:8080/api/tasks/standard \
  -H "Content-Type: application/json" \
  -d '{
    "taskName": "我的第一个训练任务",
    "modelName": "qwen-7b",
    "datasetId": "dataset_abc123",
    "userId": 1,
    "hyperparameters": "{\"learning_rate\": 0.001, \"epochs\": 5}"
  }'
```

**响应示例**：
```json
{
  "taskId": "task_xyz789",
  "taskName": "我的第一个训练任务",
  "taskMode": "STANDARD",
  "status": "PENDING",
  "modelName": "qwen-7b",
  "datasetId": "dataset_abc123",
  "currentIteration": 0
}
```

### 6.3 启动任务

```bash
curl -X POST http://localhost:8080/api/tasks/task_xyz789/start
```

### 6.4 监控任务进度

```bash
# 持续查询任务状态
watch -n 5 'curl -s http://localhost:8080/api/tasks/task_xyz789 | jq'
```

**状态变化**：
```
PENDING → OPTIMIZING → TRAINING → EVALUATING → COMPLETED
```

### 6.5 查看执行历史

```bash
curl http://localhost:8080/api/tasks/task_xyz789/executions | jq
```

---

## 步骤 7：运行持续学习任务

### 7.1 创建持续学习任务

```bash
curl -X POST http://localhost:8080/api/tasks/continuous \
  -H "Content-Type: application/json" \
  -d '{
    "taskName": "持续学习任务",
    "modelName": "qwen-7b",
    "datasetId": "dataset_abc123",
    "userId": 1,
    "hyperparameters": "{\"learning_rate\": 0.001, \"epochs\": 3}",
    "maxIterations": 3,
    "performanceThreshold": 0.95
  }'
```

### 7.2 启动并监控

```bash
# 启动
curl -X POST http://localhost:8080/api/tasks/task_cont001/start

# 监控（会看到多轮迭代）
watch -n 10 'curl -s http://localhost:8080/api/tasks/task_cont001 | jq ".status, .currentIteration, .latestScore"'
```

---

## 常见问题

### 1. 数据库连接失败

**错误**：`Connection refused`

**解决**：
- 确保 PostgreSQL 已启动
- 检查 `application.yml` 中的数据库配置
- 验证用户名和密码

### 2. 微服务连接失败

**错误**：`Connection refused to localhost:8002`

**解决**：
- 确保 Python 微服务已启动
- 检查端口是否被占用
- 验证 `application.yml` 中的服务地址

### 3. 文件上传失败

**错误**：`Maximum upload size exceeded`

**解决**：
在 `application.yml` 中增加上传限制：
```yaml
spring:
  servlet:
    multipart:
      max-file-size: 100MB
      max-request-size: 100MB
```

### 4. 任务启动失败

**错误**：`数据集不存在`

**解决**：
- 确保数据集已成功上传
- 检查 `datasetId` 是否正确

---

## 开发工具

### 推荐的 API 测试工具

- **Postman**：图形化 API 测试
- **curl**：命令行测试
- **HTTPie**：更友好的命令行工具

### 数据库管理工具

- **DBeaver**：通用数据库管理工具
- **pgAdmin**：PostgreSQL 专用工具

### 日志查看

```bash
# 查看 Spring Boot 日志
tail -f logs/spring-boot.log

# 查看 Python 服务日志
tail -f python-services/data-analyzer-service/logs/service.log
```

---

## 下一步

1. 阅读 [ARCHITECTURE.md](./ARCHITECTURE.md) 了解系统架构
2. 查看 [API_EXAMPLES.md](./API_EXAMPLES.md) 学习更多 API 用法
3. 参考 [REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md) 了解系统设计

---

**祝你使用愉快！**

如有问题，请查看文档或提交 Issue。
