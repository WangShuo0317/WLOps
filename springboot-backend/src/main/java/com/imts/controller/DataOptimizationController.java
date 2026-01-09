package com.imts.controller;

import com.imts.client.DataAnalyzerServiceClient;
import com.imts.dto.analyzer.HealthResponse;
import com.imts.dto.analyzer.OptimizationRequest;
import com.imts.dto.analyzer.OptimizationResponse;
import com.imts.dto.analyzer.OptimizationResult;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;

/**
 * 数据优化控制器
 * 
 * 提供数据集优化的 REST API
 */
@Slf4j
@RestController
@RequestMapping("/api/data-optimization")
@RequiredArgsConstructor
public class DataOptimizationController {
    
    private final DataAnalyzerServiceClient dataAnalyzerClient;
    
    /**
     * 优化数据集（异步）
     * 
     * 适用于大数据集（> 100 样本）
     * 
     * POST /api/data-optimization/optimize
     */
    @PostMapping("/optimize")
    public Mono<ResponseEntity<OptimizationResponse>> optimizeDataset(
        @RequestBody OptimizationRequest request
    ) {
        log.info("收到数据优化请求: dataset_size={}", request.getDataset().size());
        
        return dataAnalyzerClient.optimizeDatasetAsync(
            request.getDataset(),
            request.getKnowledgeBase()
        ).map(ResponseEntity::ok)
         .onErrorResume(error -> {
             log.error("数据优化失败", error);
             return Mono.just(ResponseEntity.internalServerError().build());
         });
    }
    
    /**
     * 查询优化结果
     * 
     * GET /api/data-optimization/optimize/{taskId}
     */
    @GetMapping("/optimize/{taskId}")
    public Mono<ResponseEntity<OptimizationResult>> getOptimizationResult(
        @PathVariable String taskId
    ) {
        log.info("查询优化结果: taskId={}", taskId);
        
        return dataAnalyzerClient.getOptimizationResult(taskId)
            .map(ResponseEntity::ok)
            .onErrorResume(error -> {
                log.error("查询优化结果失败: taskId={}", taskId, error);
                return Mono.just(ResponseEntity.notFound().build());
            });
    }
    
    /**
     * 优化数据集（同步）
     * 
     * 适用于小数据集（< 100 样本）
     * 直接返回优化后的数据集
     * 
     * POST /api/data-optimization/optimize/sync
     */
    @PostMapping("/optimize/sync")
    public Mono<ResponseEntity<OptimizationResult>> optimizeDatasetSync(
        @RequestBody OptimizationRequest request
    ) {
        log.info("收到同步优化请求: dataset_size={}", request.getDataset().size());
        
        return dataAnalyzerClient.optimizeDatasetSync(
            request.getDataset(),
            request.getKnowledgeBase()
        ).map(result -> {
            log.info("同步优化完成: input={}, output={}, improvement={}%",
                result.getStatistics().get("input_size"),
                result.getStatistics().get("output_size"),
                result.getStatistics().get("quality_improvement"));
            return ResponseEntity.ok(result);
        }).onErrorResume(error -> {
            log.error("同步优化失败", error);
            return Mono.just(ResponseEntity.internalServerError().build());
        });
    }
    
    /**
     * 加载知识库
     * 
     * POST /api/data-optimization/knowledge-base
     */
    @PostMapping("/knowledge-base")
    public Mono<ResponseEntity<Map<String, Object>>> loadKnowledgeBase(
        @RequestBody List<String> knowledge
    ) {
        log.info("加载知识库: size={}", knowledge.size());
        
        return dataAnalyzerClient.loadKnowledgeBase(knowledge)
            .map(ResponseEntity::ok)
            .onErrorResume(error -> {
                log.error("加载知识库失败", error);
                return Mono.just(ResponseEntity.internalServerError().build());
            });
    }
    
    /**
     * 健康检查
     * 
     * GET /api/data-optimization/health
     */
    @GetMapping("/health")
    public Mono<ResponseEntity<HealthResponse>> healthCheck() {
        return dataAnalyzerClient.healthCheck()
            .map(ResponseEntity::ok)
            .onErrorResume(error -> {
                log.error("健康检查失败", error);
                return Mono.just(ResponseEntity.status(503).build());
            });
    }
    
    /**
     * 获取系统统计
     * 
     * GET /api/data-optimization/stats
     */
    @GetMapping("/stats")
    public Mono<ResponseEntity<Map<String, Object>>> getSystemStats() {
        return dataAnalyzerClient.getSystemStats()
            .map(ResponseEntity::ok)
            .onErrorResume(error -> {
                log.error("获取系统统计失败", error);
                return Mono.just(ResponseEntity.internalServerError().build());
            });
    }
}
