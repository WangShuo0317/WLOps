package com.imts.client;

import com.imts.dto.analyzer.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;

/**
 * 数据优化服务客户端
 * 调用 Python 数据优化服务（LangGraph + Celery + Redis）
 * 
 * 核心功能：将原始数据集转换为纯净的高质量数据集
 * 
 * 架构特性：
 * - 智能分批：全量诊断 + 分批优化（仅 LLM 调用部分）
 * - 持久化：Redis 存储任务状态，支持断点续传
 * - 异步队列：Celery 分布式处理，支持横向扩展
 * - 进度跟踪：实时查看处理进度和当前阶段
 * 
 * 支持双模式：
 * - auto（标注流程优化）：无需优化指导，自动诊断和优化
 * - guided（指定优化）：提供优化指导，按需优化
 * 
 * @version 5.0.0
 */
@Slf4j
@Component
public class DataAnalyzerServiceClient {
    
    private final WebClient webClient;
    
    public DataAnalyzerServiceClient(@Value("${python-services.data-analyzer.url}") String baseUrl) {
        this.webClient = WebClient.builder()
            .baseUrl(baseUrl + "/api/v1")
            .build();
    }
    
    /**
     * 优化数据集（异步）
     * 
     * 适用于大数据集（> 100 样本）
     * 
     * 工作流：
     * 1. 全量诊断 - 使用完整数据集进行语义分布分析
     * 2. 分批优化 - 将低质量样本分批进行 COT 重写
     * 3. 分批生成 - 为稀缺聚类分批生成新样本
     * 4. 分批校验 - 将优化和生成的样本分批进行 RAG 校验
     * 5. 全量清洗 - PII 隐私信息清洗
     * 
     * @param dataset 原始数据集
     * @param knowledgeBase 知识库（用于RAG校验）
     * @return 任务ID和状态
     */
    public Mono<OptimizationResponse> optimizeDatasetAsync(
        List<Map<String, Object>> dataset,
        List<String> knowledgeBase
    ) {
        log.info("调用数据优化服务（异步）: dataset_size={}", dataset.size());
        
        OptimizationRequest request = OptimizationRequest.builder()
            .dataset(dataset)
            .knowledgeBase(knowledgeBase)
            .saveReports(true)
            .build();
        
        return webClient.post()
            .uri("/optimize")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(OptimizationResponse.class)
            .doOnSuccess(response -> 
                log.info("优化任务已启动: taskId={}, status={}, mode={}", 
                    response.getTaskId(), response.getStatus(), response.getMode()))
            .doOnError(error -> 
                log.error("启动优化任务失败", error));
    }
    
    /**
     * 查询优化结果（支持进度跟踪）
     * 
     * 返回信息包括：
     * - status: 任务状态（pending/processing/completed/failed）
     * - current_phase: 当前阶段（diagnostic/optimization/generation/verification/cleaning）
     * - progress: 进度百分比（0-100）
     * - optimized_dataset: 优化后的数据集（仅完成时）
     * 
     * @param taskId 任务ID
     * @return 优化结果（包含进度信息）
     */
    public Mono<OptimizationResult> getOptimizationResult(String taskId) {
        log.debug("查询优化结果: taskId={}", taskId);
        
        return webClient.get()
            .uri("/optimize/{taskId}", taskId)
            .retrieve()
            .bodyToMono(OptimizationResult.class)
            .doOnSuccess(result -> {
                if ("processing".equals(result.getStatus())) {
                    log.info("任务处理中: taskId={}, phase={}, progress={}%", 
                        taskId, result.getCurrentPhase(), result.getProgress());
                } else {
                    log.info("查询成功: taskId={}, status={}", taskId, result.getStatus());
                }
            })
            .doOnError(error -> 
                log.error("查询优化结果失败: taskId={}", taskId, error));
    }
    
    /**
     * 轮询任务直到完成
     * 
     * 每隔指定时间查询一次任务状态，直到完成或失败
     * 
     * @param taskId 任务ID
     * @param intervalMs 轮询间隔（毫秒）
     * @param maxAttempts 最大尝试次数
     * @return 最终结果
     */
    public Mono<OptimizationResult> pollUntilComplete(
        String taskId, 
        long intervalMs, 
        int maxAttempts
    ) {
        return Mono.defer(() -> getOptimizationResult(taskId))
            .flatMap(result -> {
                String status = result.getStatus();
                
                // 如果已完成或失败，直接返回
                if ("completed".equals(status) || "failed".equals(status)) {
                    return Mono.just(result);
                }
                
                // 否则等待后重试
                return Mono.delay(java.time.Duration.ofMillis(intervalMs))
                    .then(Mono.defer(() -> getOptimizationResult(taskId)));
            })
            .repeat(maxAttempts - 1)
            .filter(result -> 
                "completed".equals(result.getStatus()) || 
                "failed".equals(result.getStatus()))
            .next()
            .doOnSuccess(result -> 
                log.info("任务完成: taskId={}, status={}", taskId, result.getStatus()));
    }
    
    /**
     * 优化数据集（同步）
     * 
     * 适用于小数据集（< 100 样本）
     * 直接返回优化后的数据集
     * 
     * 注意：大数据集会返回 400 错误，请使用异步接口
     * 
     * @param dataset 原始数据集
     * @param knowledgeBase 知识库（可选）
     * @return 优化结果（包含优化后的数据集）
     */
    public Mono<OptimizationResult> optimizeDatasetSync(
        List<Map<String, Object>> dataset,
        List<String> knowledgeBase
    ) {
        log.info("调用数据优化服务（同步，auto模式）: dataset_size={}", dataset.size());
        
        if (dataset.size() > 100) {
            log.warn("数据集过大（{}），建议使用异步接口", dataset.size());
        }
        
        OptimizationRequest request = OptimizationRequest.builder()
            .dataset(dataset)
            .knowledgeBase(knowledgeBase)
            .saveReports(false)
            // 不提供 optimizationGuidance，使用 auto 模式
            .build();
        
        return webClient.post()
            .uri("/optimize/sync")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(OptimizationResult.class)
            .doOnSuccess(result -> 
                log.info("同步优化完成（{}模式）: input={}, output={}", 
                    result.getMode(),
                    result.getStatistics().get("input_size"),
                    result.getStatistics().get("output_size")))
            .doOnError(error -> 
                log.error("同步优化失败", error));
    }
    
    /**
     * 优化数据集（同步，带优化指导）
     * 
     * 使用 guided 模式，根据优化指导进行优化
     * 仅用于持续学习任务
     * 
     * @param dataset 原始数据集
     * @param knowledgeBase 知识库（可选）
     * @param optimizationGuidance 优化指导
     * @return 优化结果（包含优化后的数据集）
     */
    public Mono<OptimizationResult> optimizeDatasetWithGuidance(
        List<Map<String, Object>> dataset,
        List<String> knowledgeBase,
        Map<String, Object> optimizationGuidance
    ) {
        log.info("调用数据优化服务（同步，guided模式）: dataset_size={}, guidance={}", 
            dataset.size(), optimizationGuidance);
        
        OptimizationRequest request = OptimizationRequest.builder()
            .dataset(dataset)
            .knowledgeBase(knowledgeBase)
            .optimizationGuidance(optimizationGuidance)  // 提供优化指导，使用 guided 模式
            .saveReports(false)
            .build();
        
        return webClient.post()
            .uri("/optimize/sync")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(OptimizationResult.class)
            .doOnSuccess(result -> 
                log.info("同步优化完成（{}模式）: input={}, output={}", 
                    result.getMode(),
                    result.getStatistics().get("input_size"),
                    result.getStatistics().get("output_size")))
            .doOnError(error -> 
                log.error("同步优化失败", error));
    }
    
    /**
     * 恢复中断的任务
     * 
     * 如果任务因服务重启等原因中断，可以使用此方法恢复
     * 
     * @param taskId 任务ID
     * @return 恢复结果
     */
    public Mono<Map<String, Object>> resumeTask(String taskId) {
        log.info("恢复任务: taskId={}", taskId);
        
        return webClient.post()
            .uri("/tasks/{taskId}/resume", taskId)
            .retrieve()
            .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
            .doOnSuccess(response -> 
                log.info("任务已重新提交: {}", response.get("message")))
            .doOnError(error -> 
                log.error("恢复任务失败: taskId={}", taskId, error));
    }
    
    /**
     * 删除任务
     * 
     * 删除任务及其相关数据
     * 
     * @param taskId 任务ID
     * @return 删除结果
     */
    public Mono<Map<String, Object>> deleteTask(String taskId) {
        log.info("删除任务: taskId={}", taskId);
        
        return webClient.delete()
            .uri("/tasks/{taskId}", taskId)
            .retrieve()
            .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
            .doOnSuccess(response -> 
                log.info("任务已删除: {}", response.get("message")))
            .doOnError(error -> 
                log.error("删除任务失败: taskId={}", taskId, error));
    }
    
    /**
     * 列出所有任务
     * 
     * @return 任务列表
     */
    public Mono<Map<String, Object>> listTasks() {
        log.debug("列出所有任务");
        
        return webClient.get()
            .uri("/tasks")
            .retrieve()
            .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
            .doOnError(error -> 
                log.error("列出任务失败", error));
    }
    
    /**
     * 加载知识库
     * 
     * 注意：在分布式环境中，建议在优化请求中直接传递知识库
     * 
     * @param knowledge 知识列表
     * @return 加载结果
     */
    public Mono<Map<String, Object>> loadKnowledgeBase(List<String> knowledge) {
        log.info("加载知识库: size={}", knowledge.size());
        
        return webClient.post()
            .uri("/knowledge-base/load")
            .bodyValue(knowledge)
            .retrieve()
            .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
            .doOnSuccess(response -> 
                log.info("知识库加载成功: {}", response.get("message")))
            .doOnError(error -> 
                log.error("知识库加载失败", error));
    }
    
    /**
     * 健康检查
     * 
     * @return 健康检查响应
     */
    public Mono<HealthResponse> healthCheck() {
        log.debug("执行健康检查");
        
        return webClient.get()
            .uri("/health")
            .retrieve()
            .bodyToMono(HealthResponse.class)
            .doOnSuccess(response -> 
                log.info("健康检查成功: status={}, version={}, engine={}", 
                    response.getStatus(), response.getVersion(), response.getWorkflowEngine()))
            .doOnError(error -> 
                log.error("健康检查失败", error));
    }
    
    /**
     * 简单健康检查（仅返回是否健康）
     * 
     * @return 是否健康
     */
    public Mono<Boolean> isHealthy() {
        return healthCheck()
            .map(response -> "healthy".equals(response.getStatus()))
            .onErrorReturn(false);
    }
    
    /**
     * 获取系统统计
     * 
     * 返回信息包括：
     * - total_tasks: 总任务数
     * - pending_tasks: 待处理任务数
     * - processing_tasks: 处理中任务数
     * - completed_tasks: 已完成任务数
     * - failed_tasks: 失败任务数
     * - batch_size: 批次大小
     * - max_workers: 最大 Worker 数
     * 
     * @return 系统统计信息
     */
    public Mono<Map<String, Object>> getSystemStats() {
        log.debug("获取系统统计");
        
        return webClient.get()
            .uri("/stats")
            .retrieve()
            .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
            .doOnSuccess(stats -> 
                log.info("系统统计: total={}, processing={}, completed={}", 
                    stats.get("total_tasks"), 
                    stats.get("processing_tasks"), 
                    stats.get("completed_tasks")))
            .doOnError(error -> 
                log.error("获取系统统计失败", error));
    }
}
