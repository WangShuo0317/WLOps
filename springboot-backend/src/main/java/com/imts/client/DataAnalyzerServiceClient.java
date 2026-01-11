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
 * 调用 Python 自进化数据优化智能体服务（LangGraph 版本）
 * 
 * 核心功能：将原始数据集转换为纯净的高质量数据集
 * 
 * 支持双模式：
 * - auto（标注流程优化）：无需优化指导，自动诊断和优化
 * - guided（指定优化）：提供优化指导，按需优化
 * 
 * @version 4.0.0
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
                log.info("优化任务已启动: taskId={}, status={}", 
                    response.getTaskId(), response.getStatus()))
            .doOnError(error -> 
                log.error("启动优化任务失败", error));
    }
    
    /**
     * 查询优化结果
     * 
     * @param taskId 任务ID
     * @return 优化结果
     */
    public Mono<OptimizationResult> getOptimizationResult(String taskId) {
        log.info("查询优化结果: taskId={}", taskId);
        
        return webClient.get()
            .uri("/optimize/{taskId}", taskId)
            .retrieve()
            .bodyToMono(OptimizationResult.class)
            .doOnSuccess(result -> 
                log.info("查询成功: taskId={}, status={}", taskId, result.getStatus()))
            .doOnError(error -> 
                log.error("查询优化结果失败: taskId={}", taskId, error));
    }
    
    /**
     * 优化数据集（同步）
     * 
     * 适用于小数据集（< 100 样本）
     * 直接返回优化后的数据集
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
                log.info("同步优化完成（{}模式）: input={}, output={}, quality_improvement={}%", 
                    result.getMode(),
                    result.getStatistics().get("input_size"),
                    result.getStatistics().get("output_size"),
                    result.getStatistics().get("quality_improvement")))
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
                log.info("同步优化完成（{}模式）: input={}, output={}, quality_improvement={}%", 
                    result.getMode(),
                    result.getStatistics().get("input_size"),
                    result.getStatistics().get("output_size"),
                    result.getStatistics().get("quality_improvement")))
            .doOnError(error -> 
                log.error("同步优化失败", error));
    }
    
    /**
     * 加载知识库
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
                log.info("健康检查成功: status={}, llm_available={}", 
                    response.getStatus(), response.getLlmAvailable()))
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
     */
    public Mono<Map<String, Object>> getSystemStats() {
        return webClient.get()
            .uri("/stats")
            .retrieve()
            .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {});
    }
}
