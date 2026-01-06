# IMTS - 智能模型训练与迭代系统

Intelligent Model Training System - 基于Spring Boot + Python微服务的AI训练平台

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│              Spring Boot 主控制系统 (8080)                │
│  - 任务管理                                              │
│  - 数据持久化 (MySQL)                                    │
│  - 业务逻辑编排                                          │
│  - Web API                                              │
└────────────┬────────────┬────────────┬──────────────────┘
             │            │            │
             │ HTTP REST  │            │
             ↓            ↓            ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ 训练服务     │ │ 数据分析服务  │ │ 评测服务     │
│ (8001)      │ │ (8002)       │ │ (8003)      │
│             │ │              │ │             │
│ LLaMA       │ │ 数据分析     │ │ 多智能体    │
│ Factory     │ │ 智能体       │ │ 评测法官    │
└──────────────┘ └──────────────┘ └──────────────┘
   Python          Python          Python
```

## 核心特性

- 🎯 **Spring Boot主控** - 统一的任务管理和业务编排
- 🤖 **Python微服务** - 独立的训练、分析、评测服务
- 🔄 **控制与数据分离** - 清晰的架构边界
- 📊 **数据持久化** - MySQL存储任务和结果
- 🚀 **高性能训练** - 基于LLaMA Factory的分布式训练
- 🧠 **智能分析** - AI驱动的数据分析和优化
- ⚖️ **多智能体评测** - 辩论机制的深度评估

## 快速开始

### 1. 环境准备

**必需**:
- Java 17+
- Python 3.9+
- MySQL 8.0+
- Maven 3.6+

**可选**:
- NVIDIA GPU (用于模型训练)
- CUDA 11.8+

### 2. 克隆项目

```bash
git clone <repository-url>
cd imts

# 克隆LLaMA Factory
git clone https://github.com/hiyouga/LLaMA-Factory.git
```

### 3. 启动Python微服务

```bash
# 安装Python依赖
pip install -r python-services/requirements.txt

# 启动训练服务 (端口8001)
cd python-services/training-service
python app.py

# 启动数据分析服务 (端口8002)
cd python-services/data-analyzer-service
python app.py

# 启动评测服务 (端口8003)
cd python-services/evaluation-service
python app.py
```

### 4. 启动Spring Boot后端

```bash
cd springboot-backend

# 配置数据库
# 编辑 src/main/resources/application.yml
# 修改数据库连接信息

# 启动应用
mvn spring-boot:run
```

### 5. 访问系统

- **Spring Boot API**: http://localhost:8080
- **训练服务**: http://localhost:8001/docs
- **数据分析服务**: http://localhost:8002/docs
- **评测服务**: http://localhost:8003/docs

## 项目结构

```
imts/
├── springboot-backend/          # Spring Boot主控系统
│   ├── src/main/java/com/imts/
│   │   ├── client/             # Python服务客户端
│   │   ├── controller/         # REST控制器
│   │   ├── service/            # 业务服务层
│   │   ├── entity/             # 数据库实体
│   │   ├── repository/         # 数据访问层
│   │   └── dto/                # 数据传输对象
│   └── pom.xml
│
├── python-services/             # Python微服务
│   ├── training-service/       # 训练服务 (LLaMA Factory)
│   │   ├── app.py
│   │   └── llamafactory_adapter.py
│   ├── data-analyzer-service/  # 数据分析智能体
│   │   └── app.py
│   └── evaluation-service/     # 评测法官智能体
│       └── app.py
│
├── LLaMA-Factory/              # 训练引擎 (git clone)
│
└── docs/                       # 文档
    ├── ARCHITECTURE.md
    └── API.md
```

## API文档

### Spring Boot主控API

#### 创建训练任务
```http
POST /api/training/jobs
Content-Type: application/json

{
  "modelName": "meta-llama/Llama-3-8b",
  "dataset": "alpaca_en_demo",
  "stage": "sft",
  "finetuningType": "lora",
  "batchSize": 2,
  "learningRate": 5e-5,
  "epochs": 3.0
}
```

#### 查询任务状态
```http
GET /api/training/jobs/{jobId}
```

#### 停止训练任务
```http
POST /api/training/jobs/{jobId}/stop
```

### Python微服务API

详见各服务的 `/docs` 端点 (FastAPI自动生成的Swagger文档)

## 开发指南

### 添加新的训练类型

1. 在 `TrainingRequest.java` 中添加新参数
2. 在 `llamafactory_adapter.py` 中处理新配置
3. 更新API文档

### 扩展智能体功能

1. 在对应的Python服务中添加新端点
2. 在Spring Boot中创建对应的Client方法
3. 在Service层编排业务逻辑

## 部署

### Docker部署

```bash
# 构建镜像
docker-compose build

# 启动所有服务
docker-compose up -d
```

### Kubernetes部署

```bash
kubectl apply -f k8s/
```

## 技术栈

### Spring Boot后端
- Spring Boot 3.2
- Spring Data JPA
- Spring WebFlux
- MySQL 8.0
- Lombok

### Python微服务
- FastAPI
- LLaMA Factory
- PyTorch
- Transformers
- Loguru

## 文档

- [系统架构](./docs/ARCHITECTURE.md)
- [API文档](./docs/API.md)
- [部署指南](./docs/DEPLOYMENT.md)
- [开发指南](./docs/DEVELOPMENT.md)

## 许可证

Apache License 2.0
