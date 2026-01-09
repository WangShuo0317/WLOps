# Spring Boot 集成示例

## 概述

本文档展示如何在 Spring Boot 中集成和使用数据优化服务。

## 核心功能

将原始数据集（可能包含低质量样本）转换为纯净的高质量数据集。

## API 端点

### 1. 智能优化数据集（同步）

**POST** `/api/data-optimization/optimize/sync`

适用于小数据集（< 100 样本），直接返回优化结果。

```bash
curl -X POST http://localhost:8080/api/data-optimization/optimize/sync \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": [
      {
        "question": "3 + 5 = ?",
        "answer": "8"
      },
      {
        "question": "小明有10元，买了3元的笔，还剩多少？",
        "answer": "7元"
      }
    ],
    "knowledge_base": [
      "加法运算：两个数相加，得到它们的和",
      "减法运算：从一个数中减去另一个数"
    ]
  }'
```

**响应示例**：
```json
{
  "task_id": "task_abc123",
  "status": "completed",
  "optimized_dataset": [
    {
      "question": "3 + 5 = ?",
      "chain_of_thought": "这是一个加法运算问题。根据加法定义，我们需要将两个数相加。3 + 5 = 8",
      "answer": "8",
      "_optimized": true
    }
  ],
  "statistics": {
    "input_size": 2,
    "output_size": 2,
    "optimized_count": 2,
    "generated_count": 0,
    "quality_improvement": 45.5,
    "duration_seconds": 3.2
  }
}
```

### 2. 异步优化（大数据集）

**POST** `/api/data-optimization/optimize`

适用于大数据集（> 100 样本），返回任务 ID，需要轮询查询结果。

```bash
# 启动优化任务
curl -X POST http://localhost:8080/api/data-optimization/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": [...],
    "knowledge_base": [...]
  }'

# 响应
{
  "task_id": "task_xyz789",
  "status": "processing",
  "message": "数据优化任务已启动，数据集大小: 500"
}

# 查询结果
curl -X GET http://localhost:8080/api/data-optimization/optimize/task_xyz789
```

### 3. 加载知识库

**POST** `/api/data-optimization/knowledge-base`

```bash
curl -X POST http://localhost:8080/api/data-optimization/knowledge-base \
  -H "Content-Type: application/json" \
  -d '[
    "加法运算：两个数相加，得到它们的和",
    "减法运算：从一个数中减去另一个数"
  ]'
```

### 4. 健康检查

**GET** `/api/data-optimization/health`

```bash
curl -X GET http://localhost:8080/api/data-optimization/health
```

**响应示例**：
```json
{
  "status": "healthy",
  "service": "data-optimization-service",
  "version": "3.1.0",
  "llm_available": true,
  "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
}
```

### 5. 系统统计

**GET** `/api/data-optimization/stats`

```bash
curl -X GET http://localhost:8080/api/data-optimization/stats
```

## Java 使用示例

### 1. 在 Service 中使用

```java
@Service
@RequiredArgsConstructor
public class TrainingDataService {
    
    private final DataOptimizationService optimizationService;
    
    public Mono<List<Map<String, Object>>> prepareTrainingData(
        List<Map<String, Object>> rawData,
        String domain
    ) {
        // 1. 预处理数据
        List<Map<String, Object>> cleanData = 
            optimizationService.preprocessDataset(rawData);
        
        // 2. 构建知识库
        List<String> knowledgeBase = 
            optimizationService.buildDefaultKnowledgeBase(domain);
        
        // 3. 智能优化
        return optimizationService.smartOptimize(cleanData, knowledgeBase)
            .map(result -> {
                // 4. 验证结果
                if (optimizationService.validateOptimizationResult(result)) {
                    return result.getOptimizedDataset();
                } else {
                    throw new RuntimeException("数据优化质量不达标");
                }
            });
    }
}
```

### 2. 在 Controller 中使用

```java
@RestController
@RequestMapping("/api/training")
@RequiredArgsConstructor
public class TrainingController {
    
    private final TrainingDataService trainingDataService;
    
    @PostMapping("/prepare-data")
    public Mono<ResponseEntity<List<Map<String, Object>>>> prepareData(
        @RequestBody PrepareDataRequest request
    ) {
        return trainingDataService.prepareTrainingData(
            request.getRawData(),
            request.getDomain()
        ).map(ResponseEntity::ok);
    }
}
```

### 3. 直接使用客户端

```java
@Service
@RequiredArgsConstructor
public class MyService {
    
    private final DataAnalyzerServiceClient client;
    
    public Mono<OptimizationResult> optimizeData(
        List<Map<String, Object>> dataset
    ) {
        // 同步优化（小数据集）
        return client.optimizeDatasetSync(dataset, null);
    }
    
    public Mono<OptimizationResult> optimizeLargeData(
        List<Map<String, Object>> dataset
    ) {
        // 异步优化（大数据集）
        return client.optimizeDatasetAsync(dataset, null)
            .flatMap(response -> {
                // 轮询查询结果
                return pollResult(response.getTaskId());
            });
    }
    
    private Mono<OptimizationResult> pollResult(String taskId) {
        return client.getOptimizationResult(taskId)
            .flatMap(result -> {
                if ("completed".equals(result.getStatus())) {
                    return Mono.just(result);
                } else if ("failed".equals(result.getStatus())) {
                    return Mono.error(new RuntimeException(result.getError()));
                } else {
                    return Mono.delay(Duration.ofSeconds(5))
                        .then(pollResult(taskId));
                }
            });
    }
}
```

## 配置

### application.yml

```yaml
python-services:
  data-analyzer:
    url: http://localhost:8002

logging:
  level:
    com.imts.client: DEBUG
    com.imts.service: INFO
```

## 数据格式

### 输入格式

```json
{
  "dataset": [
    {
      "question": "问题文本",
      "answer": "答案文本",
      "chain_of_thought": "推理过程（可选）"
    }
  ],
  "knowledge_base": [
    "知识1",
    "知识2"
  ]
}
```

### 输出格式

```json
{
  "task_id": "task_abc123",
  "status": "completed",
  "optimized_dataset": [
    {
      "question": "问题文本",
      "chain_of_thought": "详细的推理过程",
      "answer": "答案文本",
      "_optimized": true
    }
  ],
  "statistics": {
    "input_size": 100,
    "output_size": 120,
    "optimized_count": 60,
    "generated_count": 20,
    "quality_improvement": 45.5,
    "duration_seconds": 12.5
  }
}
```

## 最佳实践

### 1. 数据预处理

```java
// 清洗无效数据
List<Map<String, Object>> cleanData = rawData.stream()
    .filter(item -> item.containsKey("question") && item.containsKey("answer"))
    .filter(item -> !String.valueOf(item.get("question")).trim().isEmpty())
    .toList();
```

### 2. 知识库管理

```java
// 根据领域构建知识库
List<String> knowledgeBase = switch (domain) {
    case "math" -> buildMathKnowledgeBase();
    case "language" -> buildLanguageKnowledgeBase();
    default -> buildGeneralKnowledgeBase();
};
```

### 3. 错误处理

```java
return optimizationService.smartOptimize(dataset, knowledgeBase)
    .onErrorResume(error -> {
        log.error("数据优化失败", error);
        // 返回原始数据或默认处理
        return Mono.just(createFallbackResult(dataset));
    });
```

### 4. 结果验证

```java
if (!optimizationService.validateOptimizationResult(result)) {
    log.warn("优化结果质量不达标，使用原始数据");
    return originalDataset;
}
```

## 性能建议

1. **小数据集（< 100）**: 使用同步接口 `/optimize/sync`
2. **大数据集（> 100）**: 使用异步接口 `/optimize`
3. **知识库**: 提前加载，避免重复加载
4. **批处理**: 合并多个小请求

## 架构图

```
Spring Boot Backend
├── DataOptimizationController    # REST API 控制器
├── DataOptimizationService       # 业务逻辑服务
├── DataAnalyzerServiceClient     # Python 服务客户端
└── DTO Classes                   # 数据传输对象
    ↓ HTTP 调用
Python Data Optimization Service (Port 8002)
├── api.py                        # RESTful API 服务
├── system_integration.py         # 核心优化逻辑
└── Multi-Agent Modules           # 四大智能体模块
    ├── Diagnostic Agent          # 诊断智能体
    ├── Optimization Agent        # 优化智能体
    ├── Verification Agent        # 校验智能体
    └── Privacy Agent             # 隐私清洗智能体
```

---

**版本**: 3.1.0  
**更新**: 2026-01-09
