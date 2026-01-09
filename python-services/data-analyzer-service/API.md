# API 接口文档

## 概述

本服务提供 RESTful API 接口，供 Spring Boot 后端调用，实现数据集的自动优化。

**基础URL**: `http://localhost:8002/api/v1`

## 核心功能

将原始数据集（可能包含低质量样本）转换为纯净的高质量数据集。

## API 端点

### 1. 优化数据集（异步）

**POST** `/api/v1/optimize`

异步执行数据优化，适用于大数据集。

#### 请求体

```json
{
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
  ],
  "task_id": "optional_task_id",
  "save_reports": true
}
```

#### 响应

```json
{
  "task_id": "task_abc123",
  "status": "processing",
  "message": "数据优化任务已启动，数据集大小: 100"
}
```

### 2. 查询优化结果

**GET** `/api/v1/optimize/{task_id}`

查询异步任务的状态和结果。

#### 响应

```json
{
  "task_id": "task_abc123",
  "status": "completed",
  "optimized_dataset": [
    {
      "question": "3 + 5 = ?",
      "chain_of_thought": "这是一个加法运算。3加5等于8。",
      "answer": "8",
      "_optimized": true
    }
  ],
  "statistics": {
    "input_size": 100,
    "output_size": 120,
    "optimized_count": 60,
    "generated_count": 20,
    "quality_improvement": 45.5,
    "duration_seconds": 180.5
  },
  "error": null
}
```

### 3. 优化数据集（同步）

**POST** `/api/v1/optimize/sync`

同步执行数据优化，直接返回结果。适用于小数据集（< 100 样本）。

#### 请求体

```json
{
  "dataset": [...],
  "knowledge_base": [...],
  "save_reports": false
}
```

#### 响应

```json
{
  "task_id": "task_xyz789",
  "status": "completed",
  "optimized_dataset": [...],
  "statistics": {
    "input_size": 50,
    "output_size": 65,
    "optimized_count": 30,
    "generated_count": 15,
    "quality_improvement": 38.2,
    "duration_seconds": 45.3
  }
}
```

### 4. 加载知识库

**POST** `/api/v1/knowledge-base/load`

加载外部知识库，用于 RAG 校验。

#### 请求体

```json
[
  "知识1",
  "知识2",
  "知识3"
]
```

#### 响应

```json
{
  "status": "success",
  "message": "成功加载 3 条知识",
  "knowledge_base_stats": {
    "store_type": "faiss",
    "total_documents": 3
  }
}
```

### 5. 健康检查

**GET** `/api/v1/health`

检查服务状态。

#### 响应

```json
{
  "status": "healthy",
  "service": "data-optimization-service",
  "version": "3.1.0",
  "llm_available": true,
  "embedding_model": "BAAI/bge-m3"
}
```

### 6. 系统统计

**GET** `/api/v1/stats`

获取系统统计信息。

#### 响应

```json
{
  "system_stats": {
    "total_iterations": 5,
    "knowledge_base_stats": {...}
  },
  "active_tasks": 2,
  "completed_tasks": 10,
  "failed_tasks": 1
}
```

## Spring Boot 集成示例

### 1. 添加依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-webflux</artifactId>
</dependency>
```

### 2. 创建服务类

```java
@Service
public class DataOptimizationService {
    
    private final WebClient webClient;
    
    public DataOptimizationService() {
        this.webClient = WebClient.builder()
            .baseUrl("http://localhost:8002/api/v1")
            .build();
    }
    
    // 异步优化
    public Mono<OptimizationResponse> optimizeDatasetAsync(
        List<Map<String, Object>> dataset,
        List<String> knowledgeBase
    ) {
        OptimizationRequest request = new OptimizationRequest();
        request.setDataset(dataset);
        request.setKnowledgeBase(knowledgeBase);
        
        return webClient.post()
            .uri("/optimize")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(OptimizationResponse.class);
    }
    
    // 查询结果
    public Mono<OptimizationResult> getOptimizationResult(String taskId) {
        return webClient.get()
            .uri("/optimize/{taskId}", taskId)
            .retrieve()
            .bodyToMono(OptimizationResult.class);
    }
    
    // 同步优化（小数据集）
    public Mono<OptimizationResult> optimizeDatasetSync(
        List<Map<String, Object>> dataset
    ) {
        OptimizationRequest request = new OptimizationRequest();
        request.setDataset(dataset);
        request.setSaveReports(false);
        
        return webClient.post()
            .uri("/optimize/sync")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(OptimizationResult.class);
    }
}
```

### 3. 使用示例

```java
@RestController
@RequestMapping("/api/data")
public class DataController {
    
    @Autowired
    private DataOptimizationService optimizationService;
    
    @PostMapping("/optimize")
    public Mono<ResponseEntity<OptimizationResponse>> optimizeDataset(
        @RequestBody DatasetRequest request
    ) {
        return optimizationService.optimizeDatasetAsync(
            request.getDataset(),
            request.getKnowledgeBase()
        ).map(ResponseEntity::ok);
    }
    
    @GetMapping("/optimize/{taskId}")
    public Mono<ResponseEntity<OptimizationResult>> getResult(
        @PathVariable String taskId
    ) {
        return optimizationService.getOptimizationResult(taskId)
            .map(ResponseEntity::ok);
    }
}
```

## 数据格式

### 输入数据格式

```json
{
  "question": "问题文本",
  "answer": "答案文本",
  "chain_of_thought": "推理过程（可选）"
}
```

### 输出数据格式

```json
{
  "question": "问题文本",
  "chain_of_thought": "详细的推理过程",
  "answer": "答案文本",
  "_optimized": true,
  "_generated": false
}
```

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误描述"
}
```

### 常见错误码

- `400` - 请求参数错误
- `404` - 任务不存在
- `500` - 服务器内部错误
- `503` - 服务不可用（LLM 未配置）

## 性能建议

1. **小数据集（< 100）**: 使用同步接口 `/optimize/sync`
2. **大数据集（> 100）**: 使用异步接口 `/optimize`
3. **知识库**: 提前加载，避免每次请求都加载
4. **批处理**: 合并多个小请求为一个大请求

## 启动服务

```bash
# 配置环境变量
export OPENAI_API_KEY="your-api-key"

# 启动服务
python api.py
```

服务将在 `http://localhost:8002` 启动。

## Swagger 文档

启动服务后访问：
- Swagger UI: `http://localhost:8002/docs`
- ReDoc: `http://localhost:8002/redoc`

---

**版本**: 3.1.0  
**更新**: 2026-01-09
