# 数据优化模式使用规则

## 📋 规则说明

### ✅ 允许使用指定优化（Guided Mode）

**仅限：持续学习训练任务**

- **任务类型**：`TaskMode.CONTINUOUS`
- **调用位置**：`WorkflowOrchestrator.executeOptimizationWithFeedback()`
- **触发条件**：第 2 轮及以后的迭代（有评估反馈）
- **优化指导来源**：评估报告的改进建议

### ❌ 禁止使用指定优化（强制 Auto Mode）

**1. 标准训练任务**
- **任务类型**：`TaskMode.STANDARD`
- **调用位置**：`WorkflowOrchestrator.executeOptimization()`
- **原因**：标准训练任务只执行一次，无评估反馈

**2. 单独调用数据优化**
- **API 端点**：`/api/data-optimization/optimize` 和 `/api/data-optimization/optimize/sync`
- **控制器**：`DataOptimizationController`
- **原因**：外部调用不应该控制内部优化策略

## 🔄 工作流程

### 标准训练任务（Standard Pipeline）

```
数据优化（auto 模式）
    ↓
模型训练
    ↓
模型评估
    ↓
完成
```

**代码路径**：
```java
WorkflowOrchestrator.executeStandardPipeline()
  → executeOptimization()  // 使用 auto 模式
```

### 持续学习任务（Continuous Learning Loop）

```
第 1 轮迭代：
  数据优化（auto 模式）
    ↓
  模型训练
    ↓
  模型评估
    ↓
  检查是否继续

第 2+ 轮迭代：
  数据优化（guided 模式，基于评估反馈）
    ↓
  模型训练
    ↓
  模型评估
    ↓
  检查是否继续
    ↓
  ...循环...
```

**代码路径**：
```java
WorkflowOrchestrator.executeContinuousLearningLoop()
  → executeIteration()
    → iteration == 0: executeOptimization()  // auto 模式
    → iteration > 0: executeOptimizationWithFeedback()  // guided 模式
```

## 📊 模式对比

| 特性 | Auto 模式 | Guided 模式 |
|------|----------|------------|
| 使用场景 | 标准训练、单独调用、首轮迭代 | 持续学习第 2+ 轮 |
| 优化指导 | ❌ 无 | ✅ 有（评估反馈） |
| 诊断范围 | 全面诊断 | 针对性诊断 |
| 优化方式 | 自动优化 | 基于反馈优化 |
| 调用方法 | `optimizeDatasetSync()` | `optimizeDatasetWithGuidance()` |

## 🔧 实现细节

### 1. DataOptimizationController（外部 API）

**强制使用 auto 模式**：

```java
@PostMapping("/optimize/sync")
public Mono<ResponseEntity<OptimizationResult>> optimizeDatasetSync(
    @RequestBody OptimizationRequest request
) {
    // 忽略任何外部提供的 optimizationGuidance
    if (request.getOptimizationGuidance() != null) {
        log.warn("外部调用不允许使用 optimizationGuidance，已忽略");
        request.setOptimizationGuidance(null);
    }
    
    return dataAnalyzerClient.optimizeDatasetSync(
        request.getDataset(),
        request.getKnowledgeBase()
    );
}
```

### 2. WorkflowOrchestrator（内部编排）

**标准训练任务 - auto 模式**：

```java
private Mono<String> executeOptimization(MLTask task, int iteration) {
    // 不提供 optimizationGuidance，使用 auto 模式
    return dataAnalyzerClient.optimizeDatasetSync(
        dataset,
        null  // 不提供知识库
    );
}
```

**持续学习任务 - guided 模式**：

```java
private Mono<String> executeOptimizationWithFeedback(
    MLTask task, 
    int iteration, 
    List<String> suggestions
) {
    // 构建优化指导
    Map<String, Object> guidance = buildOptimizationGuidance(
        task, 
        iteration, 
        suggestions
    );
    
    // 使用 guided 模式
    return dataAnalyzerClient.optimizeDatasetWithGuidance(
        dataset,
        null,
        guidance  // 提供优化指导
    );
}
```

### 3. 优化指导构建

**基于评估反馈构建**：

```java
private Map<String, Object> buildOptimizationGuidance(
    MLTask task, 
    int iteration, 
    List<String> suggestions
) {
    Map<String, Object> guidance = new HashMap<>();
    
    // 关注领域（根据建议动态确定）
    List<String> focusAreas = new ArrayList<>();
    if (suggestions.stream().anyMatch(s -> s.contains("推理"))) {
        focusAreas.add("reasoning_quality");
    }
    if (suggestions.stream().anyMatch(s -> s.contains("样本"))) {
        focusAreas.add("semantic_distribution");
    }
    guidance.put("focus_areas", focusAreas);
    
    // 优化指令
    guidance.put("optimization_instructions", 
        String.format("根据第 %d 轮评估结果，重点改进：%s", 
            iteration, String.join("、", suggestions)));
    
    // 生成指令
    guidance.put("generation_instructions", 
        String.format("生成更多样本来解决：%s", 
            String.join("、", suggestions)));
    
    return guidance;
}
```

## 🚫 安全限制

### 1. 外部 API 限制

```java
// DataOptimizationController
// ✅ 允许：不提供 optimizationGuidance
{
    "dataset": [...],
    "knowledge_base": [...]
}

// ❌ 禁止：提供 optimizationGuidance（会被忽略）
{
    "dataset": [...],
    "knowledge_base": [...],
    "optimization_guidance": {...}  // 会被忽略并记录警告
}
```

### 2. 内部调用限制

```java
// WorkflowOrchestrator
// ✅ 标准训练任务：只能使用 executeOptimization()
if (task.getTaskMode() == TaskMode.STANDARD) {
    return executeOptimization(task, 0);  // auto 模式
}

// ✅ 持续学习任务：根据迭代选择
if (iteration == 0) {
    return executeOptimization(task, 0);  // auto 模式
} else {
    return executeOptimizationWithFeedback(task, iteration, suggestions);  // guided 模式
}
```

## 📝 日志示例

### Auto 模式

```
[Optimization] 开始数据优化（auto模式）: taskId=task_123, iteration=0
调用数据优化服务（同步，auto模式）: dataset_size=100
同步优化完成（auto模式）: input=100, output=120, quality_improvement=15.5%
```

### Guided 模式

```
[OptimizationWithFeedback] 开始数据优化（guided模式）: taskId=task_123, iteration=1, suggestions=2
[OptimizationGuidance] 构建优化指导: iteration=1, focusAreas=[reasoning_quality], suggestions=2
调用数据优化服务（同步，guided模式）: dataset_size=120, guidance={focus_areas=[reasoning_quality], ...}
同步优化完成（guided模式）: input=120, output=145, quality_improvement=20.8%
```

## 🎯 总结

### 使用规则

1. **标准训练任务** → 强制 auto 模式
2. **持续学习任务（第 1 轮）** → auto 模式
3. **持续学习任务（第 2+ 轮）** → guided 模式（基于评估反馈）
4. **单独调用数据优化 API** → 强制 auto 模式（忽略任何 guidance）

### 代码位置

- **外部 API**：`DataOptimizationController` - 强制 auto 模式
- **标准训练**：`WorkflowOrchestrator.executeOptimization()` - auto 模式
- **持续学习**：`WorkflowOrchestrator.executeOptimizationWithFeedback()` - guided 模式

### 安全保证

- ✅ 外部调用无法使用 guided 模式
- ✅ 标准训练任务无法使用 guided 模式
- ✅ 只有持续学习任务的第 2+ 轮才使用 guided 模式
- ✅ Guided 模式的优化指导来自评估反馈，不受外部控制

---

**更新日期**：2026-01-10  
**版本**：v4.0.0
