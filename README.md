# IMTS - 智能模型训练与迭代系统

Intelligent Model Training System - 基于Spring Boot + Python微服务的AI训练平台

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│              React 前端界面 (3000)                        │
│  - 数据集管理                                            │
│  - 任务管理                                              │
│  - 实时监控                                              │
│  - 可视化展示                                            │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/REST
                         ↓
┌─────────────────────────────────────────────────────────┐
│              Spring Boot 主控制系统 (8080)                │
│  - 任务管理                                              │
│  - 数据持久化 (PostgreSQL)                               │
│  - 业务逻辑编排                                          │
│  - Web API                                              │
└────────────┬────────────┬────────────┬──────────────────┘
             │            │            │
             │ HTTP REST  │            │
             ↓            ↓            ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ 训练服务     │ │ 数据分析服务  │ │ 评测服务     │
│ (8004)      │ │ (8002)       │ │ (8003)      │
│             │ │              │ │             │
│ LLaMA       │ │ 数据分析     │ │ 多智能体    │
│ Factory     │ │ 智能体       │ │ 评测法官    │
└──────────────┘ └──────────────┘ └──────────────┘
   Python          Python          Python
```

## 核心特性

- 🎨 **现代化前端** - React + TypeScript + Ant Design 5 的直观界面
- 🎯 **Spring Boot主控** - 统一的任务管理和业务编排
- 🤖 **Python微服务** - 独立的训练、分析、评测服务
- 🔄 **控制与数据分离** - 清晰的架构边界
- 📊 **数据持久化** - PostgreSQL存储任务和结果
- 🚀 **高性能训练** - 基于LLaMA Factory的分布式训练
- 🧠 **智能分析** - AI驱动的数据分析和优化
- ⚖️ **多智能体评测** - 辩论机制的深度评估
- 📈 **实时监控** - 任务状态实时更新和可视化展示

## 项目状态

✅ **代码框架**: 100%完成  
⏳ **环境安装**: 待完成  
⏳ **功能测试**: 待完成  

详见 [CURRENT_STATUS.md](./CURRENT_STATUS.md)

## 快速开始

### 1. 环境准备

**必需**:
- Java 17+
- Python 3.9+
- MySQL 8.0+
- Maven 3.6+

**详细安装指南**: 参见 [ENVIRONMENT_SETUP.md](./ENVIRONMENT_SETUP.md)

### 2. 克隆项目

```bash
git clone https://github.com/WangShuo0317/WLOps.git
cd WLOps

# 克隆LLaMA Factory
git clone https://github.com/hiyouga/LLaMA-Factory.git
```

### 3. 配置数据库

```sql
CREATE DATABASE imts CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

编辑 `springboot-backend/src/main/resources/application.yml` 配置数据库连接。

### 4. 启动Python微服务

**Windows**:
```bash
start-services.bat
```

**Linux/Mac**:
```bash
chmod +x start-services.sh
./start-services.sh
```

### 5. 启动Spring Boot后端

```bash
cd springboot-backend
mvn spring-boot:run
```

### 6. 启动前端（新增）

**Windows**:
```bash
cd frontend
start-frontend.bat
```

**Linux/Mac**:
```bash
cd frontend
chmod +x start-frontend.sh
./start-frontend.sh
```

或手动启动：
```bash
cd frontend
npm install
npm run dev
```

### 7. 访问系统

- **前端界面**: http://localhost:3000 ⭐ 推荐使用
- **Spring Boot API**: http://localhost:8080
- **训练服务**: http://localhost:8004/docs
- **数据分析服务**: http://localhost:8002/docs
- **评测服务**: http://localhost:8003/docs

### 8. 开始使用

通过前端界面：
1. 访问 http://localhost:3000
2. 上传数据集
3. 创建训练任务
4. 启动任务并实时监控
5. 查看执行历史和结果

通过 API：
参见 [springboot-backend/API_EXAMPLES.md](./springboot-backend/API_EXAMPLES.md) 进行完整测试。

## 项目结构

```
WLOps/
├── frontend/                    # React 前端界面 ⭐ 新增
│   ├── src/
│   │   ├── components/         # 公共组件
│   │   ├── pages/              # 页面组件
│   │   ├── services/           # API 服务
│   │   ├── types/              # TypeScript 类型
│   │   └── utils/              # 工具函数
│   ├── package.json
│   └── vite.config.ts
│
├── springboot-backend/          # Spring Boot主控系统
│   ├── src/main/java/com/imts/
│   │   ├── client/             # Python服务客户端
│   │   ├── controller/         # REST控制器
│   │   ├── service/            # 业务服务层
│   │   ├── entity/             # 数据库实体
│   │   ├── repository/         # 数据访问层
│   │   ├── orchestrator/       # 工作流编排器
│   │   └── dto/                # 数据传输对象
│   └── pom.xml
│
├── python-services/             # Python微服务
│   ├── training-service/       # 训练服务 (LLaMA Factory)
│   │   ├── api.py
│   │   └── llamafactory_adapter.py
│   ├── data-analyzer-service/  # 数据分析智能体
│   │   └── api.py
│   └── evaluation-service/     # 评测法官智能体
│       └── api.py
│
├── LLaMA-Factory/              # 训练引擎 (git clone)
│
└── docs/                       # 文档
    ├── ARCHITECTURE.md
    ├── FRONTEND_GUIDE.md       # 前端使用指南 ⭐ 新增
    ├── FRONTEND_OVERVIEW.md    # 前端项目总览 ⭐ 新增
    └── QUICK_START_FRONTEND.md # 前端快速启动 ⭐ 新增
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

### 前端 ⭐ 新增
- React 18
- TypeScript
- Vite
- Ant Design 5
- React Router 6
- Axios

### Spring Boot后端
- Spring Boot 3.2
- Spring Data JPA
- Spring WebFlux
- PostgreSQL 14+
- Lombok

### Python微服务
- FastAPI
- LLaMA Factory
- PyTorch
- Transformers
- Loguru

## 文档

### 前端文档 ⭐ 新增
- [前端快速启动](./QUICK_START_FRONTEND.md)
- [前端使用指南](./FRONTEND_GUIDE.md)
- [前端项目总览](./FRONTEND_OVERVIEW.md)
- [功能详解](./frontend/FEATURES.md)
- [前端 README](./frontend/README.md)

### 后端文档
- [系统架构](./springboot-backend/ARCHITECTURE.md)
- [API 示例](./springboot-backend/API_EXAMPLES.md)
- [快速启动](./springboot-backend/QUICK_START.md)
- [项目结构](./springboot-backend/PROJECT_STRUCTURE.md)

## 许可证

Apache License 2.0
