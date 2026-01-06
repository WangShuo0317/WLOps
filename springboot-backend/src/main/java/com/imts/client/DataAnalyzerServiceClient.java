package com.imts.client;

import com.imts.dto.analyzer.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

/**
 * 数据分析服务客户端
 * 调用Python数据分析智能体微服务
 */
@Slf4j
@Component
public class DataAnalyzerServiceClient {
    
    private final WebClient webClient;
    
    public DataAnalyzerServiceClient(@Value("${python-services.data-analyzer.url}") String baseUrl) {
        this.webClient = WebClient.builder()
            .baseUrl(baseUrl)
            .build();
    }
    
    /**
     * 分析数据集
     */
    public Mono<AnalyzeResponse> analyzeDataset(AnalyzeRequest request) {
        log.info("调用数据分析服务: dataset={}", request.getDatasetPath());
        
        return webClient.post()
            .uri("/analyze")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(AnalyzeResponse.class)
            .doOnSuccess(response -> 
                log.info("数据分析完成: analysisId={}, score={}", 
                    response.getAnalysisId(), response.getHealthScore()))
            .doOnError(error -> 
                log.error("数据分析失败", error));
    }
    
    /**
     * 优化数据集
     */
    public Mono<OptimizeResponse> optimizeDataset(OptimizeRequest request) {
        log.info("调用数据优化服务: dataset={}", request.getDatasetPath());
        
        return webClient.post()
            .uri("/optimize")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(OptimizeResponse.class);
    }
    
    /**
     * 健康检查
     */
    public Mono<Boolean> healthCheck() {
        return webClient.get()
            .uri("/health")
            .retrieve()
            .bodyToMono(String.class)
            .map(response -> true)
            .onErrorReturn(false);
    }
}
