# WLOps v5.0 - 机器学习运维平台

[![Version](https://img.shields.io/badge/version-5.0.0-blue.svg)](https://github.com/WangShuo0317/WLOps)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Java](https://img.shields.io/badge/java-17+-orange.svg)](https://www.oracle.com/java/)
[![React](https://img.shields.io/badge/react-18+-61dafb.svg)](https://reactjs.org/)

一个完整的机器学习运维平台，专注于**智能数据优化**和**模型训练管理**。

## ✨ 核心特性

### 🎯 智能数据优化（v5.0 新特性）

- **全量诊断**: 使用完整数据集进行语义分布分析，准确识别稀缺样本
- **分批处理**: 仅在 LLM 调用阶段分批，控制成本和内存
- **实时进度**: 按阶段显示进度（诊断→优化→生成→校验→清洗）
- **断点续传**: Redis 持久化，服务重启不丢失进度

### 🚀 分布式架构（v5.0 新特性）

- **异步队列**: Celery + Redis 分布式任务处理
- **横向扩展**: 支持多 Worker 并行处理
- **高可用**: 服务重启自动恢复任务
- **实时监控**: Flower 监控面板

### 📊 性能卓越

| 数据量 | 诊断时间 | 优化时间 | 总时间 |
|--------|----------|----------|--------|
| 1,000 | ~30秒 | 5-10分钟 | 5-10分钟 |
| 10,000 | ~2分钟 | 30-60分钟 | 30-60分钟 |
| 100,000 | ~10分钟 | 4-8小时 | 4-8小时 |

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    前端 (React + TypeScript)                 │
│                    http://localhost:5173                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 Spring Boot 后端 (Java 17)                   │
│                    http://localhost:8080                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│          数据分析服务 (FastAPI + Celery + Redis)            │
│                    http://localhost:8001                     │
│  - 智能分批处理                                              │
│  - 全量诊断 + 分批优化                                       │
│  - 实时进度跟踪                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 前置要求

- **Java**: JDK 17+
- **Node.js**: 18+
- **Python**: 3.9+
- **MySQL**: 8.0+
- **Redis**: 6.0+

### 一键启动

```bash
# 1. 克隆项目
git clone https://github.com/WangShuo0317/WLOps.git
cd WLOps

# 2. 启动 Redis
redis-server

# 3. 初始化数据库
mysql -u root -p < init-database.sql

# 4. 启动数据分析服务
cd python-services/data-analyzer-service
start-all.bat  # Windows
# 或
./start-all.sh  # Linux/Mac

# 5. 启动 Spring Boot 后端
cd springboot-backend
./mvnw spring-boot:run

# 6. 启动前端
cd frontend
npm install && npm run dev
```

### 访问应用

- **前端**: http://localhost:5173
- **后端 API**: http://localhost:8080
- **数据分析服务**: http://localhost:8001/docs
- **Flower 监控**: http://localhost:5555

## 📖 使用示例

### 1. 创建数据优化任务

```typescript
// 前端
const response = await taskApi.create({
  taskName: "数据优化任务",
  datasetId: "dataset_001",
  taskMode: "STANDARD"
});
```

### 2. 查看实时进度

```typescript
// 轮询任务进度
const interval = setInterval(async () => {
  const result = await taskApi.getById(taskId);
  
  console.log(`进度: ${result.progress}%`);
  console.log(`阶段: ${result.currentPhase}`);
  
  if (result.status === 'completed') {
    clearInterval(interval);
  }
}, 3000);
```

### 3. 后端集成

```java
@Autowired
private DataAnalyzerServiceClient analyzerClient;

// 异步优化大数据集
public void optimizeLargeDataset() {
    analyzerClient.optimizeDatasetAsync(dataset, knowledgeBase)
        .flatMap(response -> 
            analyzerClient.pollUntilComplete(
                response.getTaskId(), 5000, 720
            )
        )
        .subscribe(result -> {
            log.info("优化完成: {} -> {} 样本", 
                result.getStatistics().get("input_size"),
                result.getStatistics().get("output_size"));
        });
}
```

## 📚 文档

### 核心文档

- [完整部署指南](DEPLOYMENT_COMPLETE_GUIDE.md) - 详细的部署步骤
- [项目总结](PROJECT_SUMMARY.md) - 项目概述和技术架构
- [架构设计说明](python-services/data-analyzer-service/ARCHITECTURE_DESIGN.md) - 智能分批策略

### 服务文档

- [数据分析服务](python-services/data-analyzer-service/README.md)
- [Spring Boot 集成指南](springboot-backend/DATA_ANALYZER_INTEGRATION.md)
- [前端功能文档](frontend/FEATURES.md)

## 🔧 配置

### 数据分析服务

```env
# python-services/data-analyzer-service/.env
LLM_API_KEY=your_api_key_here
LLM_MODEL=gpt-4
REDIS_HOST=localhost
REDIS_PORT=6379
BATCH_SIZE=50
MAX_WORKERS=4
```

### Spring Boot

```yaml
# springboot-backend/src/main/resources/application.yml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/wlops
    username: root
    password: your_password

python-services:
  data-analyzer:
    url: http://localhost:8001
```

## 🧪 测试

```bash
# 数据分析服务测试
cd python-services/data-analyzer-service
python test_large_dataset.py

# Spring Boot 测试
cd springboot-backend
./mvnw test

# 前端测试
cd frontend
npm test
```

## 📊 监控

- **Flower 监控**: http://localhost:5555 - Celery 任务监控
- **API 文档**: http://localhost:8001/docs - FastAPI 文档
- **系统统计**: http://localhost:8001/api/v1/stats

## 🐛 故障排查

### Redis 连接失败

```bash
redis-cli ping  # 应返回 PONG
```

### Celery Worker 无法启动

```bash
# Windows 使用 solo 池
celery -A celery_app worker --pool=solo
```

### 任务卡住

```bash
# 恢复任务
curl -X POST http://localhost:8001/api/v1/tasks/{task_id}/resume
```

更多问题请查看 [故障排查指南](DEPLOYMENT_COMPLETE_GUIDE.md#故障排查)。

## 🎯 版本历史

### v5.0.0 (2026-01-12) - 当前版本

**重大更新**:
- ✅ 智能分批策略（全量诊断 + 分批优化）
- ✅ 分布式架构（Celery + Redis）
- ✅ 实时进度跟踪（阶段化进度条）
- ✅ 断点续传（Redis 持久化）
- ✅ 支持 1 万到 10 万条数据处理

**性能提升**:
- 最大数据量：1,000 → 100,000+ (100倍)
- 诊断准确性：局部 → 全局（100%）
- 并发处理：1 → 4-8+ (4-8倍)

### v4.0.0 (2026-01-10)

- LangGraph 工作流引擎
- 双模式支持（auto/guided）
- 多智能体架构

### v3.0.0 (2023-11)

- 初始版本
- 基础数据优化功能

## 🤝 贡献

欢迎贡献代码！请查看 [贡献指南](CONTRIBUTING.md)。

### 代码规范

- **Python**: PEP 8
- **Java**: Google Java Style Guide
- **TypeScript**: ESLint + Prettier

### 提交规范

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式
refactor: 重构
test: 测试
chore: 构建/工具
```

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

感谢以下开源项目：

- [React](https://reactjs.org/) - 前端框架
- [Spring Boot](https://spring.io/projects/spring-boot) - 后端框架
- [FastAPI](https://fastapi.tiangolo.com/) - Python Web 框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - 工作流引擎
- [Celery](https://docs.celeryproject.org/) - 分布式任务队列
- [Redis](https://redis.io/) - 内存数据库
- [Ant Design](https://ant.design/) - UI 组件库
- [OpenAI](https://openai.com/) - LLM API

## 📞 联系方式

- **GitHub**: https://github.com/WangShuo0317/WLOps
- **Issues**: https://github.com/WangShuo0317/WLOps/issues
- **文档**: 项目 docs/ 目录

## 🌟 Star History

如果这个项目对你有帮助，请给我们一个 Star ⭐

---

**版本**: v5.0.0  
**更新时间**: 2026-01-12  
**状态**: ✅ 生产就绪

🚀 **让机器学习运维更简单！**
