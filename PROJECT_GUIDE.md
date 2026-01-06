# IMTS 项目指南

## 项目重构说明

本项目已完成架构重构，采用**Spring Boot + Python微服务**的混合架构。

### 重构前后对比

| 方面 | 重构前 | 重构后 |
|------|--------|--------|
| 主控系统 | Python FastAPI | **Spring Boot** |
| 训练服务 | 集成在主系统 | **独立Python微服务** |
| 数据分析 | 集成在主系统 | **独立Python微服务** |
| 评测服务 | 集成在主系统 | **独立Python微服务** |
| 数据持久化 | 无 | **MySQL数据库** |
| 业务编排 | 简单 | **完整的业务流程编排** |

## 新架构优势

1. **职责清晰**: Spring Boot负责控制，Python负责AI计算
2. **易于扩展**: 各微服务独立部署和扩展
3. **技术适配**: Java处理业务逻辑，Python处理AI任务
4. **企业级**: 完整的数据持久化、权限控制、监控告警

## 项目结构

```
imts/
├── springboot-backend/          # Spring Boot主控系统
│   ├── src/main/java/com/imts/
│   │   ├── client/             # Python服务客户端
│   │   ├── controller/         # REST API控制器
│   │   ├── service/            # 业务服务层
│   │   ├── entity/             # JPA实体
│   │   ├── repository/         # 数据访问层
│   │   └── dto/                # 数据传输对象
│   ├── src/main/resources/
│   │   └── application.yml     # 配置文件
│   └── pom.xml                 # Maven配置
│
├── python-services/             # Python微服务
│   ├── training-service/       # 训练服务 (8001)
│   │   ├── app.py             # FastAPI应用
│   │   └── llamafactory_adapter.py  # LLaMA Factory适配器
│   ├── data-analyzer-service/  # 数据分析服务 (8002)
│   │   └── app.py
│   ├── evaluation-service/     # 评测服务 (8003)
│   │   └── app.py
│   └── requirements.txt        # Python依赖
│
├── LLaMA-Factory/              # 训练引擎 (需git clone)
│
├── docs/                       # 文档
│   ├── ARCHITECTURE.md         # 架构文档
│   └── SPRINGBOOT_INTEGRATION.md  # 集成说明
│
├── start-services.sh           # 启动脚本 (Linux/Mac)
├── start-services.bat          # 启动脚本 (Windows)
├── README.md                   # 项目说明
└── PROJECT_GUIDE.md            # 本文件
```

## 快速开始

### 1. 环境准备

**必需**:
- Java 17+
- Python 3.9+
- MySQL 8.0+
- Maven 3.6+

### 2. 克隆LLaMA Factory

```bash
git clone https://github.com/hiyouga/LLaMA-Factory.git
```

### 3. 配置数据库

编辑 `springboot-backend/src/main/resources/application.yml`:

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/imts
    username: your_username
    password: your_password
```

创建数据库:

```sql
CREATE DATABASE imts CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 启动Python微服务

**Linux/Mac**:
```bash
chmod +x start-services.sh
./start-services.sh
```

**Windows**:
```bash
start-services.bat
```

### 5. 启动Spring Boot

```bash
cd springboot-backend
mvn spring-boot:run
```

### 6. 验证

- Spring Boot: http://localhost:8080
- 训练服务: http://localhost:8001/docs
- 数据分析服务: http://localhost:8002/docs
- 评测服务: http://localhost:8003/docs

## 核心功能

### 1. 训练任务管理

**创建训练任务**:
```bash
curl -X POST http://localhost:8080/api/training/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "modelName": "meta-llama/Llama-3-8b",
    "dataset": "alpaca_en_demo",
    "stage": "sft",
    "finetuningType": "lora",
    "batchSize": 2,
    "learningRate": 5e-5,
    "epochs": 3.0
  }'
```

**查询任务状态**:
```bash
curl http://localhost:8080/api/training/jobs/{jobId}
```

### 2. 数据分析

通过Spring Boot调用数据分析智能体，分析数据集质量。

### 3. 模型评测

通过Spring Boot调用评测智能体，进行多智能体辩论评测。

## 开发指南

### 添加新的API端点

1. 在Python服务中添加新端点
2. 在Spring Boot的Client中添加调用方法
3. 在Service层编排业务逻辑
4. 在Controller中暴露REST API

### 扩展训练功能

修改 `python-services/training-service/llamafactory_adapter.py`

### 扩展智能体功能

修改对应的Python服务 `app.py`

## 部署

### Docker部署

```bash
docker-compose up -d
```

### Kubernetes部署

```bash
kubectl apply -f k8s/
```

## 技术栈

### Spring Boot
- Spring Boot 3.2
- Spring Data JPA
- Spring WebFlux
- MySQL 8.0

### Python微服务
- FastAPI
- LLaMA Factory
- PyTorch
- Transformers

## 文档

- [README.md](./README.md) - 项目概述
- [ARCHITECTURE.md](./docs/ARCHITECTURE.md) - 系统架构
- [SPRINGBOOT_INTEGRATION.md](./docs/SPRINGBOOT_INTEGRATION.md) - Spring Boot集成

## 常见问题

### Q: 为什么要重构？

A: 原架构将所有功能集成在Python中，不利于企业级应用。新架构采用Spring Boot作为主控，更适合企业环境。

### Q: Python服务可以独立使用吗？

A: 可以。每个Python服务都是独立的FastAPI应用，可以单独调用。

### Q: 如何添加新的Python服务？

A: 创建新的FastAPI应用，在Spring Boot中添加对应的Client即可。

### Q: 数据库必须是MySQL吗？

A: 不是。可以使用PostgreSQL、Oracle等，只需修改配置和驱动。

## 下一步

1. 完善Spring Boot的业务逻辑
2. 实现完整的数据分析智能体
3. 实现完整的评测智能体
4. 添加前端界面
5. 完善监控和告警
6. 添加用户认证和权限控制

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

Apache License 2.0
