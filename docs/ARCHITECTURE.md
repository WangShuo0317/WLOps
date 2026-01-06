# IMTS 系统架构文档

## 1. 总体架构

IMTS采用**Spring Boot + Python微服务**的混合架构，实现控制与数据分离。

### 1.1 架构图

```
┌───────────────────────────────────────────────────────────────┐
│                    前端 (可选)                                  │
│                  React / Vue.js                                │
└────────────────────────┬──────────────────────────────────────┘
                         │ HTTP/REST
                         ↓
┌───────────────────────────────────────────────────────────────┐
│              Spring Boot 主控系统 (端口8080)                    │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Controller Layer                                       │  │
│  │  - TrainingController                                   │  │
│  │  - DataAnalyzerController                               │  │
│  │  - EvaluationController                                 │  │
│  └────────────────────┬────────────────────────────────────┘  │
│                       │                                        │
│  ┌────────────────────▼────────────────────────────────────┐  │
│  │  Service Layer                                          │  │
│  │  - TrainingService                                      │  │
│  │  - DataAnalyzerService                                  │  │
│  │  - EvaluationService                                    │  │
│  │  - WorkflowOrchestrationService                         │  │
│  └────────────────────┬────────────────────────────────────┘  │
│                       │                                        │
│  ┌────────────────────▼────────────────────────────────────┐  │
│  │  Client Layer (WebClient)                               │  │
│  │  - TrainingServiceClient                                │  │
│  │  - DataAnalyzerServiceClient                            │  │
│  │  - EvaluationServiceClient                              │  │
│  └────────────────────┬────────────────────────────────────┘  │
│                       │                                        │
│  ┌────────────────────▼────────────────────────────────────┐  │
│  │  Repository Layer                                       │  │
│  │  - TrainingJobRepository                                │  │
│  │  - DatasetRepository                                    │  │
│  │  - EvaluationResultRepository                           │  │
│  └─────────────────────────────────────────────────────────┘  │
│                       │                                        │
│                       ▼                                        │
│                  MySQL Database                                │
└────────────────────────┬──────────────────────────────────────┘
                         │ HTTP REST API
         ┌───────────────┼───────────────┐
         │               │               │
         ↓               ↓               ↓
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ 训练服务    │  │ 数据分析    │  │ 评测服务    │
│ (8001)     │  │ 服务(8002)  │  │ (8003)     │
│            │  │             │  │            │
│ FastAPI    │  │ FastAPI     │  │ FastAPI    │
│ +          │  │ +           │  │ +          │
│ LLaMA      │  │ 数据分析    │  │ 多智能体   │
│ Factory    │  │ 智能体      │  │ 评测法官   │
└─────────────┘  └─────────────┘  └─────────────┘
   Python          Python          Python
```

## 2. 设计原则

### 2.1 控制与数据分离

- **Spring Boot**: 负责业务逻辑、任务编排、数据持久化
- **Python服务**: 负责AI计算、模型训练、智能分析

### 2.2 微服务架构

每个Python服务都是独立的微服务：
- 独立部署
- 独立扩展
- 独立升级
- 通过HTTP REST API通信

### 2.3 职责清晰

| 组件 | 职责 |
|------|------|
| Spring Boot | 任务管理、流程编排、数据持久化、权限控制 |
| 训练服务 | 模型训练、Checkpoint管理 |
| 数据分析服务 | 数据质量诊断、数据优化 |
| 评测服务 | 模型评测、多智能体辩论 |

## 3. 核心组件

### 3.1 Spring Boot主控系统

**技术栈**:
- Spring Boot 3.2
- Spring Data JPA
- Spring WebFlux (异步HTTP客户端)
- MySQL 8.0

**核心功能**:
1. **任务管理**: 创建、查询、停止训练任务
2. **流程编排**: 协调数据分析→训练→评测的完整流程
3. **数据持久化**: 存储任务状态、评测结果
4. **权限控制**: 用户认证、多租户隔离
5. **监控告警**: 任务状态监控、异常告警

### 3.2 训练服务 (Python)

**技术栈**:
- FastAPI
- LLaMA Factory
- PyTorch
- DeepSpeed

**核心功能**:
1. 封装LLaMA Factory训练功能
2. 进程管理（启动、监控、停止）
3. 配置文件生成
4. 日志收集和解析
5. Checkpoint管理

**API端点**:
- `POST /train` - 创建训练任务
- `GET /jobs/{jobId}` - 查询任务状态
- `POST /jobs/{jobId}/stop` - 停止任务

### 3.3 数据分析服务 (Python)

**技术栈**:
- FastAPI
- LangChain / AutoGen
- OpenAI API / 本地LLM

**核心功能**:
1. 用户意图解析
2. 数据质量诊断
3. 分布偏差检测
4. 语义断层识别
5. 数据增强和优化
6. PII清洗

**API端点**:
- `POST /analyze` - 分析数据集
- `POST /optimize` - 优化数据集
- `POST /clean-pii` - 清洗敏感信息

### 3.4 评测服务 (Python)

**技术栈**:
- FastAPI
- LangChain
- vLLM (推理加速)

**核心功能**:
1. 批量模型推理
2. 多智能体辩论评测
3. 指标计算
4. Bad Case分析
5. 模型对比

**API端点**:
- `POST /evaluate` - 评测模型
- `POST /debate` - 多智能体辩论
- `POST /compare` - 对比模型
- `POST /analyze-bad-cases` - 分析Bad Cases

## 4. 数据流

### 4.1 完整训练流程

```
1. 用户通过前端/API提交训练请求
   ↓
2. Spring Boot接收请求，保存到数据库
   ↓
3. (可选) 调用数据分析服务分析数据集
   ↓
4. Spring Boot调用训练服务创建训练任务
   ↓
5. 训练服务启动LLaMA Factory进程
   ↓
6. Spring Boot定期轮询训练状态
   ↓
7. 训练完成后，调用评测服务评测模型
   ↓
8. 评测结果保存到数据库
   ↓
9. 返回结果给用户
```

### 4.2 数据分析流程

```
1. 用户上传数据集
   ↓
2. Spring Boot保存数据集元信息
   ↓
3. 调用数据分析服务
   ↓
4. 数据分析智能体：
   - 解析用户意图
   - 统计分析
   - 语义分析
   - 生成诊断报告
   ↓
5. 根据诊断结果，调用优化服务
   ↓
6. 返回优化后的数据集
```

### 4.3 评测流程

```
1. 训练完成后触发评测
   ↓
2. Spring Boot调用评测服务
   ↓
3. 评测服务：
   - 加载模型
   - 批量推理
   - 计算指标
   ↓
4. (可选) 启动多智能体辩论
   ↓
5. 生成评测报告
   ↓
6. Spring Boot保存结果到数据库
```

## 5. 通信机制

### 5.1 Spring Boot → Python服务

- **协议**: HTTP REST
- **格式**: JSON
- **客户端**: Spring WebFlux WebClient
- **超时**: 可配置（训练5分钟，其他1-2分钟）
- **重试**: 支持自动重试

### 5.2 Python服务内部

- **训练服务**: 通过subprocess启动LLaMA Factory
- **智能体**: 调用LLM API (OpenAI/本地)

## 6. 数据持久化

### 6.1 MySQL数据库

**核心表**:
- `training_jobs` - 训练任务
- `datasets` - 数据集
- `evaluation_results` - 评测结果
- `users` - 用户
- `projects` - 项目

### 6.2 文件存储

- **数据集**: `./data/datasets/`
- **模型**: `./data/models/`
- **日志**: `./logs/`
- **配置**: `./configs/`

## 7. 扩展性

### 7.1 水平扩展

- Spring Boot: 多实例 + 负载均衡
- Python服务: 多实例 + 负载均衡
- 数据库: 主从复制 / 分库分表

### 7.2 功能扩展

- 新增Python服务: 创建新的FastAPI应用
- 新增Spring Boot功能: 添加Controller/Service
- 新增训练类型: 扩展LLaMA Factory适配器

## 8. 安全性

- **认证**: JWT Token
- **授权**: Spring Security
- **数据加密**: 敏感数据加密存储
- **API限流**: Spring Cloud Gateway
- **审计日志**: 记录所有操作

## 9. 监控与运维

- **健康检查**: 所有服务提供 `/health` 端点
- **日志收集**: ELK Stack
- **指标监控**: Prometheus + Grafana
- **链路追踪**: Spring Cloud Sleuth + Zipkin
- **告警**: 基于Prometheus Alertmanager

## 10. 部署架构

### 10.1 开发环境

- 所有服务运行在本地
- 使用本地MySQL

### 10.2 生产环境

```
┌─────────────────────────────────────────┐
│           Nginx (负载均衡)               │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌────▼───┐
│ Spring │      │ Spring │  (多实例)
│ Boot 1 │      │ Boot 2 │
└───┬────┘      └────┬───┘
    │                │
    └────────┬───────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌────▼───┐
│ Python │      │ Python │  (多实例)
│ 服务1  │      │ 服务2  │
└────────┘      └────────┘
```

## 11. 技术选型理由

| 技术 | 理由 |
|------|------|
| Spring Boot | 成熟的企业级框架，生态完善 |
| FastAPI | 高性能Python Web框架，自动生成API文档 |
| MySQL | 关系型数据库，适合结构化数据 |
| WebFlux | 异步非阻塞，适合调用外部服务 |
| LLaMA Factory | 成熟的训练框架，支持多种微调方法 |
