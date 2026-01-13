# 数据分析服务集成指南

## 版本信息

- **数据分析服务**: v5.0.0
- **Spring Boot 后端**: 最新版本
- **集成方式**: WebClient (响应式)

## 架构说明

### 数据分析服务特性

**智能分批策略**:
1. **全量诊断**: 使用完整数据集进行语义分布分析
2. **分批优化**: 仅在 LLM 调用阶段分批处理
3. **实时进度**: 支持进度跟踪和阶段查询

**技术栈**:
- LangGraph: 工作流引擎
- Celery: 异步任务队列
- Redis: 任务状态持久化
- Flower: 监控面板

## 使用方式

### 1. 小数据集（< 100 样本）- 同步处理

```java
@Autowired
private DataAnalyzerServiceClient analyzerClient;

public void optimizeSmallDataset() {
    // 准备数据
    List<Map<String, Object>> dataset = prepareDataset();
    List<String> knowledgeBase = prepareKnowledgeBase();
    
    // 同步优化（auto 模式）
    analyzerClient.optimizeDatasetSync(dataset, knowledgeBase)
        .subscribe(result -> {
            if ("completed".equals(result.getStatus())) {
                List<Map<String, Object>> optimizedData = result.getOptimizedDataset();
                log.info("优化完成: {} -> {} 样本", 
                    result.getStatistics().get("input_size"),
                    result.getStatistics().get("output_size"));
                
                // 使用优化后的数据
                processOptimizedData(optimizedData);
            }
        });
}
```

### 2. 大数据集（> 100 样本）- 异步处理

```java
public void optimizeLargeDataset() {
    // 准备数据
    List<Map<String, Object>> dataset = prepareDataset(); // 10,000 条
    List<String> knowledgeBase = prepareKnowledgeBase();
    
    // 提交异步任务
    analyzerClient.optimizeDatasetAsync(dataset, knowledgeBase)
        .flatMap(response -> {
            String taskId = response.getTaskId();
            log.info("任务已提交: {}, 模式: {}", taskId, response.getMode());
            
            // 轮询任务直到完成
            return analyzerClient.pollUntilComplete(
                taskId,
                5000,  // 每 5 秒查询一次
                720    // 最多查询 720 次（1 小时）
            );
        })
        .subscribe(result -> {
            if ("completed".equals(result.getStatus())) {
                List<Map<String, Object>> optimizedData = result.getOptimizedDataset();
                log.info("优化完成: {} -> {} 样本", 
                    result.getStatistics().get("input_size"),
                    result.getStatistics().get("output_size"));
                
                // 使用优化后的数据
                processOptimizedData(optimizedData);
            } else {
                log.error("优化失败: {}", result.getError());
            }
        });
}
```

### 3. 实时进度跟踪

```java
public void monitorOptimizationProgress(String taskId) {
    // 定时查询进度
    Flux.interval(Duration.ofSeconds(3))
        .flatMap(tick -> analyzerClient.getOptimizationResult(taskId))
        .takeUntil(result -> 
            "completed".equals(result.getStatus()) || 
            "failed".equals(result.getStatus()))
        .subscribe(result -> {
            // 显示进度
            log.info("任务进度: {}%", result.getProgress());
            log.info("当前阶段: {}", getPhaseText(result.getCurrentPhase()));
            
            // 更新前端进度条
            updateProgressBar(result.getProgress(), result.getCurrentPhase());
        });
}

private String getPhaseText(String phase) {
    switch (phase) {
        case "diagnostic": return "阶段 1: 全量诊断";
        case "optimization": return "阶段 2: 分批优化";
        case "generation": return "阶段 3: 分批生成";
        case "verification": return "阶段 4: 分批校验";
        case "cleaning": return "阶段 5: 全量清洗";
        default: return "未知阶段";
    }
}
```

### 4. 带优化指导（Guided 模式）

```java
public void optimizeWithGuidance() {
    // 准备数据
    List<Map<String, Object>> dataset = prepareDataset();
    List<String> knowledgeBase = prepareKnowledgeBase();
    
    // 准备优化指导
    Map<String, Object> guidance = new HashMap<>();
    guidance.put("focus_areas", Arrays.asList("reasoning_quality"));
    guidance.put("optimization_instructions", "为每个样本添加详细的推理步骤");
    guidance.put("generation_instructions", "生成更多关于深度学习的样本");
    
    // 使用 guided 模式优化
    analyzerClient.optimizeDatasetWithGuidance(dataset, knowledgeBase, guidance)
        .subscribe(result -> {
            log.info("Guided 优化完成: mode={}", result.getMode());
            processOptimizedData(result.getOptimizedDataset());
        });
}
```

### 5. 任务管理

```java
// 列出所有任务
public void listAllTasks() {
    analyzerClient.listTasks()
        .subscribe(response -> {
            List<Map<String, Object>> tasks = 
                (List<Map<String, Object>>) response.get("tasks");
            log.info("总任务数: {}", response.get("total"));
            
            tasks.forEach(task -> {
                log.info("任务: {}, 状态: {}, 进度: {}%",
                    task.get("task_id"),
                    task.get("status"),
                    task.get("progress"));
            });
        });
}

// 恢复中断的任务
public void resumeInterruptedTask(String taskId) {
    analyzerClient.resumeTask(taskId)
        .subscribe(response -> {
            log.info("任务已恢复: {}", response.get("message"));
        });
}

// 删除任务
public void deleteTask(String taskId) {
    analyzerClient.deleteTask(taskId)
        .subscribe(response -> {
            log.info("任务已删除: {}", response.get("message"));
        });
}
```

### 6. 健康检查

```java
// 详细健康检查
public void checkServiceHealth() {
    analyzerClient.healthCheck()
        .subscribe(health -> {
            log.info("服务状态: {}", health.getStatus());
            log.info("版本: {}", health.getVersion());
            log.info("工作流引擎: {}", health.getWorkflowEngine());
            log.info("LLM 可用: {}", health.getLlmAvailable());
        });
}

// 简单健康检查
public void isServiceHealthy() {
    analyzerClient.isHealthy()
        .subscribe(healthy -> {
            if (healthy) {
                log.info("数据分析服务正常");
            } else {
                log.warn("数据分析服务不可用");
            }
        });
}

// 获取系统统计
public void getSystemStats() {
    analyzerClient.getSystemStats()
        .subscribe(stats -> {
            log.info("总任务数: {}", stats.get("total_tasks"));
            log.info("处理中: {}", stats.get("processing_tasks"));
            log.info("已完成: {}", stats.get("completed_tasks"));
            log.info("批次大小: {}", stats.get("batch_size"));
            log.info("最大 Worker: {}", stats.get("max_workers"));
        });
}
```

## 配置

### application.yml

```yaml
python-services:
  data-analyzer:
    url: http://localhost:8001
```

### 超时配置

对于大数据集，建议增加超时时间：

```java
@Bean
public WebClient dataAnalyzerWebClient(
    @Value("${python-services.data-analyzer.url}") String baseUrl
) {
    return WebClient.builder()
        .baseUrl(baseUrl + "/api/v1")
        .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
        .clientConnector(new ReactorClientHttpConnector(
            HttpClient.create()
                .responseTimeout(Duration.ofMinutes(60))  // 60 分钟超时
        ))
        .build();
}
```

## 最佳实践

### 1. 数据集大小选择

| 数据集大小 | 推荐方式 | 预计时间 |
|-----------|---------|---------|
| < 100 | 同步 | < 5 分钟 |
| 100 - 1,000 | 异步 | 5-10 分钟 |
| 1,000 - 10,000 | 异步 | 30-60 分钟 |
| 10,000+ | 异步 | 1-8 小时 |

### 2. 错误处理

```java
public void optimizeWithErrorHandling() {
    analyzerClient.optimizeDatasetAsync(dataset, knowledgeBase)
        .flatMap(response -> 
            analyzerClient.pollUntilComplete(response.getTaskId(), 5000, 720))
        .doOnError(error -> {
            if (error instanceof WebClientResponseException) {
                WebClientResponseException ex = (WebClientResponseException) error;
                if (ex.getStatusCode().value() == 400) {
                    log.error("请求参数错误: {}", ex.getResponseBodyAsString());
                } else if (ex.getStatusCode().value() == 503) {
                    log.error("服务不可用，请检查 Redis 和 Celery Worker");
                }
            }
        })
        .retry(3)  // 失败重试 3 次
        .subscribe(
            result -> processResult(result),
            error -> handleError(error)
        );
}
```

### 3. 进度通知

```java
@Service
public class OptimizationProgressService {
    
    @Autowired
    private DataAnalyzerServiceClient analyzerClient;
    
    @Autowired
    private SimpMessagingTemplate messagingTemplate;
    
    public void startOptimizationWithProgress(String userId, List<Map<String, Object>> dataset) {
        analyzerClient.optimizeDatasetAsync(dataset, null)
            .flatMapMany(response -> {
                String taskId = response.getTaskId();
                
                // 定时查询进度并推送到前端
                return Flux.interval(Duration.ofSeconds(3))
                    .flatMap(tick -> analyzerClient.getOptimizationResult(taskId))
                    .takeUntil(result -> 
                        "completed".equals(result.getStatus()) || 
                        "failed".equals(result.getStatus()))
                    .doOnNext(result -> {
                        // 推送进度到前端
                        messagingTemplate.convertAndSendToUser(
                            userId,
                            "/queue/optimization-progress",
                            Map.of(
                                "taskId", taskId,
                                "progress", result.getProgress(),
                                "phase", result.getCurrentPhase(),
                                "status", result.getStatus()
                            )
                        );
                    });
            })
            .subscribe();
    }
}
```

### 4. 批量任务管理

```java
@Service
public class BatchOptimizationService {
    
    @Autowired
    private DataAnalyzerServiceClient analyzerClient;
    
    public Flux<OptimizationResult> optimizeMultipleDatasets(
        List<List<Map<String, Object>>> datasets
    ) {
        return Flux.fromIterable(datasets)
            .flatMap(dataset -> 
                analyzerClient.optimizeDatasetAsync(dataset, null)
                    .flatMap(response -> 
                        analyzerClient.pollUntilComplete(
                            response.getTaskId(), 5000, 720
                        )
                    )
            )
            .buffer(Duration.ofMinutes(10))  // 每 10 分钟收集一批结果
            .flatMapIterable(results -> results);
    }
}
```

## 监控

### Flower 监控面板

访问 http://localhost:5555 查看：
- 实时任务状态
- Worker 负载
- 任务执行历史

### 日志监控

```java
@Slf4j
@Component
public class DataAnalyzerMonitor {
    
    @Autowired
    private DataAnalyzerServiceClient analyzerClient;
    
    @Scheduled(fixedRate = 60000)  // 每分钟检查一次
    public void monitorService() {
        analyzerClient.getSystemStats()
            .subscribe(stats -> {
                int processing = (int) stats.get("processing_tasks");
                int failed = (int) stats.get("failed_tasks");
                
                if (processing > 10) {
                    log.warn("处理中任务过多: {}", processing);
                }
                
                if (failed > 0) {
                    log.error("存在失败任务: {}", failed);
                }
            });
    }
}
```

## 故障排查

### 1. 服务不可用

```java
// 检查服务健康
analyzerClient.isHealthy()
    .subscribe(healthy -> {
        if (!healthy) {
            log.error("数据分析服务不可用，请检查:");
            log.error("1. Redis 是否运行: redis-cli ping");
            log.error("2. API 服务是否运行: curl http://localhost:8001/api/v1/health");
            log.error("3. Celery Worker 是否运行: celery -A celery_app inspect active");
        }
    });
```

### 2. 任务卡住

```java
// 检查任务状态
analyzerClient.getOptimizationResult(taskId)
    .subscribe(result -> {
        if ("processing".equals(result.getStatus())) {
            // 检查进度是否更新
            Double progress = result.getProgress();
            if (progress != null && progress < 1.0) {
                log.warn("任务可能卡住: taskId={}, progress={}%", taskId, progress);
                
                // 尝试恢复任务
                analyzerClient.resumeTask(taskId).subscribe();
            }
        }
    });
```

### 3. 内存不足

如果遇到内存不足错误，调整配置：

```yaml
# application.yml
python-services:
  data-analyzer:
    batch-size: 25  # 减小批次大小
    max-workers: 2  # 减少 Worker 数量
```

## 总结

数据分析服务 v5.0.0 提供了强大的大规模数据处理能力：

- ✅ 智能分批：全量诊断 + 分批优化
- ✅ 实时进度：支持进度跟踪和阶段查询
- ✅ 持久化：Redis 存储，支持断点续传
- ✅ 分布式：Celery 队列，支持横向扩展

通过本集成指南，你可以轻松地在 Spring Boot 后端中使用数据分析服务！
