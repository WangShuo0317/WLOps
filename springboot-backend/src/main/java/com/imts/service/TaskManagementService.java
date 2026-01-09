package com.imts.service;

import com.imts.entity.MLTask;
import com.imts.entity.TaskExecution;
import com.imts.enums.TaskMode;
import com.imts.enums.TaskStatus;
import com.imts.orchestrator.WorkflowOrchestrator;
import com.imts.repository.DatasetRepository;
import com.imts.repository.MLTaskRepository;
import com.imts.repository.TaskExecutionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import reactor.core.publisher.Mono;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

/**
 * 任务管理服务
 * 
 * 职责：
 * 1. 任务的CRUD操作
 * 2. 任务生命周期管理
 * 3. 任务状态查询
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class TaskManagementService {
    
    private final MLTaskRepository taskRepository;
    private final DatasetRepository datasetRepository;
    private final TaskExecutionRepository executionRepository;
    private final WorkflowOrchestrator orchestrator;
    
    /**
     * 创建标准训练任务
     */
    @Transactional
    public Mono<MLTask> createStandardTask(
        String taskName,
        String modelName,
        String datasetId,
        Long userId,
        String hyperparameters
    ) {
        log.info("创建标准训练任务: taskName={}, modelName={}, datasetId={}", 
            taskName, modelName, datasetId);
        
        return Mono.fromCallable(() -> {
            // 验证数据集存在
            if (!datasetRepository.existsByDatasetId(datasetId)) {
                throw new RuntimeException("数据集不存在: " + datasetId);
            }
            
            // 创建任务
            String taskId = "task_" + UUID.randomUUID().toString().substring(0, 8);
            
            MLTask task = MLTask.builder()
                .taskId(taskId)
                .taskName(taskName)
                .taskMode(TaskMode.STANDARD)
                .status(TaskStatus.PENDING)
                .modelName(modelName)
                .datasetId(datasetId)
                .currentDatasetId(datasetId)
                .userId(userId)
                .currentIteration(0)
                .hyperparameters(hyperparameters)
                .createdAt(LocalDateTime.now())
                .build();
            
            return taskRepository.save(task);
        });
    }
    
    /**
     * 创建持续学习任务
     */
    @Transactional
    public Mono<MLTask> createContinuousTask(
        String taskName,
        String modelName,
        String datasetId,
        Long userId,
        String hyperparameters,
        Integer maxIterations,
        Double performanceThreshold
    ) {
        log.info("创建持续学习任务: taskName={}, modelName={}, datasetId={}, maxIterations={}, threshold={}", 
            taskName, modelName, datasetId, maxIterations, performanceThreshold);
        
        return Mono.fromCallable(() -> {
            // 验证数据集存在
            if (!datasetRepository.existsByDatasetId(datasetId)) {
                throw new RuntimeException("数据集不存在: " + datasetId);
            }
            
            // 验证终止条件
            if (maxIterations == null && performanceThreshold == null) {
                throw new RuntimeException("持续学习任务必须指定至少一个终止条件（最大迭代次数或性能阈值）");
            }
            
            // 创建任务
            String taskId = "task_" + UUID.randomUUID().toString().substring(0, 8);
            
            MLTask task = MLTask.builder()
                .taskId(taskId)
                .taskName(taskName)
                .taskMode(TaskMode.CONTINUOUS)
                .status(TaskStatus.PENDING)
                .modelName(modelName)
                .datasetId(datasetId)
                .currentDatasetId(datasetId)
                .userId(userId)
                .currentIteration(0)
                .maxIterations(maxIterations)
                .performanceThreshold(performanceThreshold)
                .hyperparameters(hyperparameters)
                .createdAt(LocalDateTime.now())
                .build();
            
            return taskRepository.save(task);
        });
    }
    
    /**
     * 启动任务
     */
    public Mono<Void> startTask(String taskId) {
        log.info("启动任务: {}", taskId);
        
        return Mono.fromCallable(() -> taskRepository.findByTaskId(taskId)
                .orElseThrow(() -> new RuntimeException("任务不存在: " + taskId)))
            .flatMap(task -> {
                // 检查任务状态
                if (task.getStatus() != TaskStatus.PENDING && task.getStatus() != TaskStatus.SUSPENDED) {
                    return Mono.error(new RuntimeException(
                        "任务状态不允许启动: " + task.getStatus()
                    ));
                }
                
                // 委托给编排器执行
                return orchestrator.startTask(taskId);
            });
    }
    
    /**
     * 暂停任务
     */
    public Mono<Void> suspendTask(String taskId) {
        log.info("暂停任务: {}", taskId);
        return orchestrator.suspendTask(taskId);
    }
    
    /**
     * 取消任务
     */
    public Mono<Void> cancelTask(String taskId) {
        log.info("取消任务: {}", taskId);
        return orchestrator.cancelTask(taskId);
    }
    
    /**
     * 查询任务详情
     */
    public Mono<MLTask> getTask(String taskId) {
        return Mono.fromCallable(() -> taskRepository.findByTaskId(taskId)
            .orElseThrow(() -> new RuntimeException("任务不存在: " + taskId)));
    }
    
    /**
     * 查询用户的所有任务
     */
    public Mono<List<MLTask>> getUserTasks(Long userId) {
        return Mono.fromCallable(() -> taskRepository.findByUserId(userId));
    }
    
    /**
     * 查询任务执行历史
     */
    public Mono<List<TaskExecution>> getTaskExecutions(String taskId) {
        return Mono.fromCallable(() -> 
            executionRepository.findByTaskIdOrderByIterationDesc(taskId)
        );
    }
    
    /**
     * 查询任务当前迭代的执行记录
     */
    public Mono<List<TaskExecution>> getCurrentIterationExecutions(String taskId) {
        return Mono.fromCallable(() -> {
            MLTask task = taskRepository.findByTaskId(taskId)
                .orElseThrow(() -> new RuntimeException("任务不存在: " + taskId));
            
            return executionRepository.findByTaskIdAndIteration(
                taskId, 
                task.getCurrentIteration()
            );
        });
    }
    
    /**
     * 删除任务
     */
    @Transactional
    public Mono<Void> deleteTask(String taskId) {
        log.info("删除任务: {}", taskId);
        
        return Mono.fromCallable(() -> {
            MLTask task = taskRepository.findByTaskId(taskId)
                .orElseThrow(() -> new RuntimeException("任务不存在: " + taskId));
            
            // 只能删除终态任务
            if (!task.getStatus().isTerminal()) {
                throw new RuntimeException("只能删除已完成、已失败或已取消的任务");
            }
            
            // 删除执行记录
            List<TaskExecution> executions = executionRepository.findByTaskId(taskId);
            executionRepository.deleteAll(executions);
            
            // 删除任务
            taskRepository.delete(task);
            
            return null;
        }).then();
    }
}
