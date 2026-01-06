# Spring Boot 集成指南

本文档说明如何在Spring Boot控制系统中调用IMTS训练API。

## 1. 架构说明

```
┌─────────────────────────────────────────────────────┐
│           Spring Boot 控制系统                        │
│  - 任务管理                                           │
│  - 用户界面                                           │
│  - 业务逻辑                                           │
└─────────────────┬───────────────────────────────────┘
                  │ HTTP REST API
                  ↓
┌─────────────────────────────────────────────────────┐
│           IMTS Python API 服务                       │
│  - FastAPI服务器                                     │
│  - 训练任务管理                                       │
│  - LLaMA Factory适配器                               │
└─────────────────┬───────────────────────────────────┘
                  │ 进程调用
                  ↓
┌─────────────────────────────────────────────────────┐
│           LLaMA Factory                             │
│  - 模型训练引擎                                       │
│  - 分布式训练                                         │
│  - LoRA/全量微调                                     │
└─────────────────────────────────────────────────────┘
```

## 2. API端点说明

### 2.1 创建训练任务

**端点**: `POST /api/v1/training/jobs`

**请求体**:
```json
{
  "model_name": "meta-llama/Llama-3-8b",
  "dataset": "alpaca_en_demo",
  "stage": "sft",
  "finetuning_type": "lora",
  "batch_size": 2,
  "learning_rate": 5e-5,
  "epochs": 3.0,
  "lora_rank": 8,
  "lora_alpha": 16,
  "custom_config": {
    "template": "llama3",
    "cutoff_len": 2048
  }
}
```

**响应**:
```json
{
  "job_id": "train_a1b2c3d4",
  "status": "pending",
  "message": "训练任务已创建，正在启动...",
  "created_at": "2025-01-06T10:30:00"
}
```

### 2.2 查询任务状态

**端点**: `GET /api/v1/training/jobs/{job_id}`

**响应**:
```json
{
  "job_id": "train_a1b2c3d4",
  "status": "running",
  "pid": 12345,
  "config_path": "./config/training_jobs/train_a1b2c3d4/training_config.yaml",
  "progress": 0.45,
  "current_loss": 0.523
}
```

**状态说明**:
- `pending`: 等待启动
- `running`: 训练中
- `completed`: 训练完成
- `failed`: 训练失败
- `stopped`: 已停止

### 2.3 列出所有任务

**端点**: `GET /api/v1/training/jobs`

**响应**:
```json
{
  "total": 3,
  "jobs": [
    {
      "job_id": "train_a1b2c3d4",
      "status": "running",
      "pid": 12345
    },
    {
      "job_id": "train_e5f6g7h8",
      "status": "completed",
      "pid": null
    }
  ]
}
```

### 2.4 停止训练任务

**端点**: `POST /api/v1/training/jobs/{job_id}/stop`

**响应**:
```json
{
  "message": "任务 train_a1b2c3d4 已停止"
}
```

### 2.5 导出模型

**端点**: `POST /api/v1/training/jobs/{job_id}/export`

**请求体**:
```json
{
  "job_id": "train_a1b2c3d4",
  "export_dir": "./models/exports/my_model",
  "merge_lora": true
}
```

**响应**:
```json
{
  "message": "模型导出成功",
  "model_path": "./models/exports/my_model"
}
```

### 2.6 健康检查

**端点**: `GET /api/v1/training/health`

**响应**:
```json
{
  "status": "healthy",
  "service": "training-api",
  "adapter_initialized": true
}
```

## 3. Spring Boot 集成示例

### 3.1 添加依赖

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-webflux</artifactId>
</dependency>
```

### 3.2 配置文件

```yaml
# application.yml
imts:
  api:
    base-url: http://localhost:8000
    timeout: 30000
```

### 3.3 创建API客户端

```java
package com.example.imts.client;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Component
public class ImtsApiClient {
    
    private final WebClient webClient;
    
    public ImtsApiClient(@Value("${imts.api.base-url}") String baseUrl) {
        this.webClient = WebClient.builder()
            .baseUrl(baseUrl)
            .build();
    }
    
    /**
     * 创建训练任务
     */
    public Mono<TrainingJobResponse> createTrainingJob(TrainingJobRequest request) {
        return webClient.post()
            .uri("/api/v1/training/jobs")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(TrainingJobResponse.class);
    }
    
    /**
     * 查询任务状态
     */
    public Mono<JobStatusResponse> getJobStatus(String jobId) {
        return webClient.get()
            .uri("/api/v1/training/jobs/{jobId}", jobId)
            .retrieve()
            .bodyToMono(JobStatusResponse.class);
    }
    
    /**
     * 停止训练任务
     */
    public Mono<Void> stopJob(String jobId) {
        return webClient.post()
            .uri("/api/v1/training/jobs/{jobId}/stop", jobId)
            .retrieve()
            .bodyToMono(Void.class);
    }
    
    /**
     * 导出模型
     */
    public Mono<ModelExportResponse> exportModel(String jobId, ModelExportRequest request) {
        return webClient.post()
            .uri("/api/v1/training/jobs/{jobId}/export", jobId)
            .bodyValue(request)
            .retrieve()
            .bodyToMono(ModelExportResponse.class);
    }
}
```

### 3.4 数据模型

```java
package com.example.imts.model;

import lombok.Data;
import java.util.Map;

@Data
public class TrainingJobRequest {
    private String modelName;
    private String dataset;
    private String stage = "sft";
    private String finetuningType = "lora";
    private Integer batchSize = 2;
    private Double learningRate = 5e-5;
    private Double epochs = 3.0;
    private Integer loraRank = 8;
    private Integer loraAlpha = 16;
    private Map<String, Object> customConfig;
}

@Data
public class TrainingJobResponse {
    private String jobId;
    private String status;
    private String message;
    private String createdAt;
}

@Data
public class JobStatusResponse {
    private String jobId;
    private String status;
    private Integer pid;
    private String configPath;
    private Double progress;
    private Double currentLoss;
}
```

### 3.5 服务层

```java
package com.example.imts.service;

import com.example.imts.client.ImtsApiClient;
import com.example.imts.model.*;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
@RequiredArgsConstructor
public class TrainingService {
    
    private final ImtsApiClient imtsApiClient;
    
    /**
     * 启动训练任务
     */
    public Mono<TrainingJobResponse> startTraining(TrainingJobRequest request) {
        log.info("启动训练任务: model={}, dataset={}", 
            request.getModelName(), request.getDataset());
        
        return imtsApiClient.createTrainingJob(request)
            .doOnSuccess(response -> 
                log.info("训练任务已创建: jobId={}", response.getJobId()))
            .doOnError(error -> 
                log.error("创建训练任务失败", error));
    }
    
    /**
     * 轮询任务状态直到完成
     */
    public Mono<JobStatusResponse> waitForCompletion(String jobId) {
        return Mono.defer(() -> imtsApiClient.getJobStatus(jobId))
            .flatMap(status -> {
                if ("completed".equals(status.getStatus())) {
                    return Mono.just(status);
                } else if ("failed".equals(status.getStatus())) {
                    return Mono.error(new RuntimeException("训练失败"));
                } else {
                    // 等待5秒后重试
                    return Mono.delay(Duration.ofSeconds(5))
                        .then(waitForCompletion(jobId));
                }
            });
    }
    
    /**
     * 停止训练
     */
    public Mono<Void> stopTraining(String jobId) {
        log.info("停止训练任务: jobId={}", jobId);
        return imtsApiClient.stopJob(jobId);
    }
}
```

### 3.6 控制器

```java
package com.example.imts.controller;

import com.example.imts.model.*;
import com.example.imts.service.TrainingService;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/training")
@RequiredArgsConstructor
public class TrainingController {
    
    private final TrainingService trainingService;
    
    @PostMapping("/start")
    public Mono<TrainingJobResponse> startTraining(
            @RequestBody TrainingJobRequest request) {
        return trainingService.startTraining(request);
    }
    
    @PostMapping("/{jobId}/stop")
    public Mono<Void> stopTraining(@PathVariable String jobId) {
        return trainingService.stopTraining(jobId);
    }
    
    @GetMapping("/{jobId}/status")
    public Mono<JobStatusResponse> getStatus(@PathVariable String jobId) {
        return trainingService.getJobStatus(jobId);
    }
}
```

## 4. 使用示例

### 4.1 启动IMTS API服务

```bash
# 在IMTS项目根目录
python main.py --mode api --port 8000
```

### 4.2 从Spring Boot调用

```java
// 在Spring Boot应用中
@Autowired
private TrainingService trainingService;

public void trainModel() {
    TrainingJobRequest request = new TrainingJobRequest();
    request.setModelName("meta-llama/Llama-3-8b");
    request.setDataset("alpaca_en_demo");
    request.setStage("sft");
    request.setFinetuningType("lora");
    request.setBatchSize(2);
    request.setLearningRate(5e-5);
    request.setEpochs(3.0);
    
    trainingService.startTraining(request)
        .flatMap(response -> {
            String jobId = response.getJobId();
            log.info("训练任务已启动: {}", jobId);
            
            // 等待训练完成
            return trainingService.waitForCompletion(jobId);
        })
        .subscribe(
            status -> log.info("训练完成: {}", status),
            error -> log.error("训练失败", error)
        );
}
```

## 5. 部署建议

### 5.1 开发环境

- IMTS API服务和Spring Boot应用运行在同一台机器
- 使用localhost通信

### 5.2 生产环境

- IMTS API服务部署在GPU服务器上
- Spring Boot应用部署在应用服务器上
- 通过内网IP通信
- 建议使用Nginx做反向代理

### 5.3 高可用部署

```
┌──────────────┐
│   Nginx      │  负载均衡
└──────┬───────┘
       │
   ┌───┴────┬────────┐
   │        │        │
┌──▼──┐ ┌──▼──┐ ┌──▼──┐
│IMTS1│ │IMTS2│ │IMTS3│  多个IMTS实例
└──┬──┘ └──┬──┘ └──┬──┘
   │        │        │
   └────────┴────────┘
          │
    ┌─────▼─────┐
    │  GPU集群  │
    └───────────┘
```

## 6. 监控与日志

### 6.1 日志位置

- IMTS API日志: `./logs/imts.log`
- 训练任务日志: `./logs/training_jobs/{job_id}/training.log`

### 6.2 监控指标

建议监控以下指标：
- API响应时间
- 训练任务数量
- GPU使用率
- 训练进度
- 错误率

### 6.3 告警

建议设置以下告警：
- 训练任务失败
- API服务不可用
- GPU资源不足
- 磁盘空间不足

## 7. 故障排查

### 7.1 连接失败

**问题**: Spring Boot无法连接到IMTS API

**解决**:
1. 检查IMTS API是否启动: `curl http://localhost:8000/api/v1/training/health`
2. 检查防火墙设置
3. 检查网络连通性

### 7.2 训练失败

**问题**: 训练任务状态变为failed

**解决**:
1. 查看训练日志: `./logs/training_jobs/{job_id}/training.log`
2. 检查GPU资源是否充足
3. 检查数据集是否正确
4. 检查模型配置是否正确

### 7.3 性能问题

**问题**: 训练速度慢

**解决**:
1. 调整batch_size
2. 启用DeepSpeed
3. 使用混合精度训练
4. 检查GPU利用率

## 8. 最佳实践

1. **异步处理**: 训练任务通常耗时较长，建议使用异步方式处理
2. **状态轮询**: 定期轮询任务状态，建议间隔5-10秒
3. **错误重试**: 网络请求失败时应该重试
4. **超时设置**: 设置合理的超时时间
5. **日志记录**: 记录所有API调用和训练任务状态变化
6. **资源管理**: 及时清理完成的训练任务和临时文件
