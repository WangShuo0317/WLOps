package com.imts.orchestrator;

import com.imts.client.DataAnalyzerServiceClient;
import com.imts.client.EvaluationServiceClient;
import com.imts.client.TrainingServiceClient;
import com.imts.entity.Dataset;
import com.imts.entity.MLTask;
import com.imts.entity.TaskExecution;
import com.imts.enums.TaskMode;
import com.imts.enums.TaskStatus;
import com.imts.repository.DatasetRepository;
import com.imts.repository.MLTaskRepository;
import com.imts.repository.TaskExecutionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * 工作流编排器
 * 
 * 核心职责：
 * 1. 编排标准训练流（Standard Pipeline）
 * 2. 编排持续学习流（Continuous Learning Loop）
 * 3. 管理任务状态转换
 * 4. 协调微服务调用
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class WorkflowOrchestrator {
    
    private final MLTaskRepository taskRepository;
    private final DatasetRepository datasetRepository;
    private final TaskExecutionRepository executionRepository;
    
    private final DataAnalyzerServiceClient dataAnalyzerClient;
    private final TrainingServiceClient trainingClient;
    private final EvaluationServiceClient evaluationClient;
    
    /**
     * 启动任务执行
     * 
     * 根据任务模式选择执行流程
     */
    public Mono<Void> startTask(String taskId) {
        log.info("[Orchestrator] 启动任务: {}", taskId);
        
        return Mono.fromCallable(() -> taskRepository.findByTaskId(taskId)
                .orElseThrow(() -> new RuntimeException("任务不存在: " + taskId)))
            .flatMap(task -> {
                // 更新状态为 OPTIMIZING
                task.updateStatus(TaskStatus.OPTIMIZING);
                taskRepository.save(task);
                
                // 根据模式选择流程
                if (task.getTaskMode() == TaskMode.STANDARD) {
                    return executeStandardPipeline(task);
                } else {
                    return executeContinuousLearningLoop(task);
                }
            })
            .doOnError(error -> log.error("[Orchestrator] 任务启动失败: {}", taskId, error));
    }
    
    /**
     * 模式 A：标准训练流
     * 
     * 流程：
     * 1. 数据优化
     * 2. 模型训练
     * 3. 模型评估
     * 4. 完成
     */
    private Mono<Void> executeStandardPipeline(MLTask task) {
        log.info("[StandardPipeline] 开始执行标准训练流: taskId={}", task.getTaskId());
        
        return executeOptimization(task, 0)
            .flatMap(optimizedDatasetId -> {
                // 更新任务状态为 TRAINING
                task.setCurrentDatasetId(optimizedDatasetId);
                task.updateStatus(TaskStatus.TRAINING);
                taskRepository.save(task);
                
                return executeTraining(task, 0, optimizedDatasetId);
            })
            .flatMap(modelPath -> {
                // 更新任务状态为 EVALUATING
                task.setLatestModelPath(modelPath);
                task.updateStatus(TaskStatus.EVALUATING);
                taskRepository.save(task);
                
                return executeEvaluation(task, 0, modelPath);
            })
            .flatMap(evaluationResult -> {
                // 更新任务状态为 COMPLETED
                task.setLatestEvaluationPath(evaluationResult.get("reportPath"));
                task.setLatestScore((Double) evaluationResult.get("score"));
                task.updateStatus(TaskStatus.COMPLETED);
                taskRepository.save(task);
                
                log.info("[StandardPipeline] 标准训练流完成: taskId={}, score={}", 
                    task.getTaskId(), task.getLatestScore());
                
                return Mono.empty();
            })
            .onErrorResume(error -> handleTaskError(task, error));
    }
    
    /**
     * 模式 B：持续学习流
     * 
     * 流程：
     * 1. 执行标准训练流
     * 2. 检查是否继续迭代
     * 3. 如果继续：解析评估报告 -> 反馈优化 -> 重新训练
     * 4. 循环直到达到终止条件
     */
    private Mono<Void> executeContinuousLearningLoop(MLTask task) {
        log.info("[ContinuousLearning] 开始执行持续学习流: taskId={}", task.getTaskId());
        
        return executeIteration(task, task.getCurrentIteration())
            .flatMap(v -> {
                // 检查是否继续迭代
                if (task.shouldContinueIteration()) {
                    log.info("[ContinuousLearning] 准备下一轮迭代: taskId={}, iteration={}", 
                        task.getTaskId(), task.getCurrentIteration() + 1);
                    
                    // 更新状态为 LOOPING
                    task.updateStatus(TaskStatus.LOOPING);
                    task.incrementIteration();
                    taskRepository.save(task);
                    
                    // 递归执行下一轮
                    return executeContinuousLearningLoop(task);
                } else {
                    // 达到终止条件，完成任务
                    log.info("[ContinuousLearning] 达到终止条件，任务完成: taskId={}, iterations={}, score={}", 
                        task.getTaskId(), task.getCurrentIteration(), task.getLatestScore());
                    
                    task.updateStatus(TaskStatus.COMPLETED);
                    taskRepository.save(task);
                    
                    return Mono.empty();
                }
            })
            .onErrorResume(error -> handleTaskError(task, error));
    }
    
    /**
     * 执行单次迭代
     * 
     * 包含：优化 -> 训练 -> 评估
     */
    private Mono<Void> executeIteration(MLTask task, int iteration) {
        log.info("[Iteration] 执行迭代: taskId={}, iteration={}", task.getTaskId(), iteration);
        
        // 获取评估建议（如果不是第一轮）
        Mono<List<String>> improvementSuggestions = iteration > 0 
            ? getImprovementSuggestions(task.getLatestEvaluationPath())
            : Mono.just(List.of());
        
        return improvementSuggestions
            .flatMap(suggestions -> {
                // 1. 数据优化（带反馈）
                task.updateStatus(TaskStatus.OPTIMIZING);
                taskRepository.save(task);
                
                return executeOptimizationWithFeedback(task, iteration, suggestions);
            })
            .flatMap(optimizedDatasetId -> {
                // 2. 模型训练
                task.setCurrentDatasetId(optimizedDatasetId);
                task.updateStatus(TaskStatus.TRAINING);
                taskRepository.save(task);
                
                return executeTraining(task, iteration, optimizedDatasetId);
            })
            .flatMap(modelPath -> {
                // 3. 模型评估
                task.setLatestModelPath(modelPath);
                task.updateStatus(TaskStatus.EVALUATING);
                taskRepository.save(task);
                
                return executeEvaluation(task, iteration, modelPath);
            })
            .flatMap(evaluationResult -> {
                // 更新任务评估结果
                task.setLatestEvaluationPath(evaluationResult.get("reportPath"));
                task.setLatestScore((Double) evaluationResult.get("score"));
                taskRepository.save(task);
                
                log.info("[Iteration] 迭代完成: taskId={}, iteration={}, score={}", 
                    task.getTaskId(), iteration, task.getLatestScore());
                
                return Mono.empty();
            });
    }
    
    /**
     * 执行数据优化
     */
    private Mono<String> executeOptimization(MLTask task, int iteration) {
        log.info("[Optimization] 开始数据优化: taskId={}, iteration={}", task.getTaskId(), iteration);
        
        // 创建执行记录
        TaskExecution execution = TaskExecution.builder()
            .taskId(task.getTaskId())
            .iteration(iteration)
            .phase("optimization")
            .status("running")
            .inputDatasetId(task.getDatasetId())
            .startedAt(LocalDateTime.now())
            .build();
        executionRepository.save(execution);
        
        // 获取数据集信息
        return Mono.fromCallable(() -> datasetRepository.findByDatasetId(task.getDatasetId())
                .orElseThrow(() -> new RuntimeException("数据集不存在: " + task.getDatasetId())))
            .flatMap(dataset -> {
                // 调用数据优化服务
                return dataAnalyzerClient.optimizeDatasetSync(
                    List.of(Map.of("storagePath", dataset.getStoragePath())),
                    null
                );
            })
            .map(result -> {
                // 保存优化后的数据集
                String optimizedDatasetId = "dataset_opt_" + UUID.randomUUID().toString().substring(0, 8);
                
                Dataset optimizedDataset = Dataset.builder()
                    .datasetId(optimizedDatasetId)
                    .name(task.getTaskName() + "_optimized_iter" + iteration)
                    .storagePath("s3://bucket/optimized/" + optimizedDatasetId + ".json")
                    .userId(task.getUserId())
                    .isOptimized(true)
                    .sourceDatasetId(task.getDatasetId())
                    .domain(datasetRepository.findByDatasetId(task.getDatasetId())
                        .map(Dataset::getDomain).orElse("general"))
                    .createdAt(LocalDateTime.now())
                    .build();
                
                datasetRepository.save(optimizedDataset);
                
                // 更新执行记录
                execution.setOutputDatasetId(optimizedDatasetId);
                execution.markCompleted();
                executionRepository.save(execution);
                
                log.info("[Optimization] 数据优化完成: taskId={}, outputDatasetId={}", 
                    task.getTaskId(), optimizedDatasetId);
                
                return optimizedDatasetId;
            })
            .onErrorResume(error -> {
                execution.markFailed(error.getMessage());
                executionRepository.save(execution);
                return Mono.error(error);
            });
    }
    
    /**
     * 执行数据优化（带反馈）
     */
    private Mono<String> executeOptimizationWithFeedback(MLTask task, int iteration, List<String> suggestions) {
        log.info("[OptimizationWithFeedback] 开始数据优化（带反馈）: taskId={}, iteration={}, suggestions={}", 
            task.getTaskId(), iteration, suggestions.size());
        
        // 如果有改进建议，将其作为知识库传递给优化服务
        return executeOptimization(task, iteration);
        // TODO: 实际实现中应该将 suggestions 传递给优化服务
    }
    
    /**
     * 执行模型训练
     */
    private Mono<String> executeTraining(MLTask task, int iteration, String datasetId) {
        log.info("[Training] 开始模型训练: taskId={}, iteration={}, datasetId={}", 
            task.getTaskId(), iteration, datasetId);
        
        // 创建执行记录
        TaskExecution execution = TaskExecution.builder()
            .taskId(task.getTaskId())
            .iteration(iteration)
            .phase("training")
            .status("running")
            .inputDatasetId(datasetId)
            .startedAt(LocalDateTime.now())
            .build();
        executionRepository.save(execution);
        
        // 调用训练服务
        String modelPath = "s3://bucket/models/" + task.getTaskId() + "_iter" + iteration + ".pth";
        
        // TODO: 实际调用训练服务
        // return trainingClient.train(...)
        
        // 模拟训练完成
        return Mono.just(modelPath)
            .doOnSuccess(path -> {
                execution.setModelPath(path);
                execution.markCompleted();
                executionRepository.save(execution);
                
                log.info("[Training] 模型训练完成: taskId={}, modelPath={}", task.getTaskId(), path);
            })
            .onErrorResume(error -> {
                execution.markFailed(error.getMessage());
                executionRepository.save(execution);
                return Mono.error(error);
            });
    }
    
    /**
     * 执行模型评估
     */
    private Mono<Map<String, Object>> executeEvaluation(MLTask task, int iteration, String modelPath) {
        log.info("[Evaluation] 开始模型评估: taskId={}, iteration={}, modelPath={}", 
            task.getTaskId(), iteration, modelPath);
        
        // 创建执行记录
        TaskExecution execution = TaskExecution.builder()
            .taskId(task.getTaskId())
            .iteration(iteration)
            .phase("evaluation")
            .status("running")
            .startedAt(LocalDateTime.now())
            .build();
        executionRepository.save(execution);
        
        // 调用评估服务
        String reportPath = "s3://bucket/evaluations/" + task.getTaskId() + "_iter" + iteration + ".json";
        double score = 0.85 + (iteration * 0.03); // 模拟分数提升
        
        // TODO: 实际调用评估服务
        // return evaluationClient.evaluate(...)
        
        return Mono.just(Map.of(
                "reportPath", reportPath,
                "score", score,
                "badCases", List.of(),
                "suggestions", List.of("增加数学推理样本", "优化问题表述")
            ))
            .doOnSuccess(result -> {
                execution.setEvaluationPath(reportPath);
                execution.setScore(score);
                execution.markCompleted();
                executionRepository.save(execution);
                
                log.info("[Evaluation] 模型评估完成: taskId={}, score={}", task.getTaskId(), score);
            })
            .onErrorResume(error -> {
                execution.markFailed(error.getMessage());
                executionRepository.save(execution);
                return Mono.error(error);
            });
    }
    
    /**
     * 从评估报告中提取改进建议
     */
    private Mono<List<String>> getImprovementSuggestions(String evaluationPath) {
        log.info("[Feedback] 提取改进建议: evaluationPath={}", evaluationPath);
        
        // TODO: 实际实现中应该解析评估报告JSON
        return Mono.just(List.of(
            "增加数学推理样本",
            "优化问题表述",
            "补充边界案例"
        ));
    }
    
    /**
     * 处理任务错误
     */
    private Mono<Void> handleTaskError(MLTask task, Throwable error) {
        log.error("[Orchestrator] 任务执行失败: taskId={}", task.getTaskId(), error);
        
        task.updateStatus(TaskStatus.FAILED);
        task.setErrorMessage(error.getMessage());
        taskRepository.save(task);
        
        return Mono.empty();
    }
    
    /**
     * 暂停任务
     */
    public Mono<Void> suspendTask(String taskId) {
        log.info("[Orchestrator] 暂停任务: {}", taskId);
        
        return Mono.fromCallable(() -> {
            MLTask task = taskRepository.findByTaskId(taskId)
                .orElseThrow(() -> new RuntimeException("任务不存在: " + taskId));
            
            task.updateStatus(TaskStatus.SUSPENDED);
            taskRepository.save(task);
            
            return task;
        }).then();
    }
    
    /**
     * 取消任务
     */
    public Mono<Void> cancelTask(String taskId) {
        log.info("[Orchestrator] 取消任务: {}", taskId);
        
        return Mono.fromCallable(() -> {
            MLTask task = taskRepository.findByTaskId(taskId)
                .orElseThrow(() -> new RuntimeException("任务不存在: " + taskId));
            
            task.updateStatus(TaskStatus.CANCELLED);
            taskRepository.save(task);
            
            return task;
        }).then();
    }
}
