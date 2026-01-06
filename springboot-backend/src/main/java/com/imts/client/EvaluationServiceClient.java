package com.imts.client;

import com.imts.dto.evaluation.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

/**
 * 评测服务客户端
 * 调用Python评测智能体微服务
 */
@Slf4j
@Component
public class EvaluationServiceClient {
    
    private final WebClient webClient;
    
    public EvaluationServiceClient(@Value("${python-services.evaluation.url}") String baseUrl) {
        this.webClient = WebClient.builder()
            .baseUrl(baseUrl)
            .build();
    }
    
    /**
     * 评测模型
     */
    public Mono<EvaluateResponse> evaluateModel(EvaluateRequest request) {
        log.info("调用评测服务: model={}", request.getModelPath());
        
        return webClient.post()
            .uri("/evaluate")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(EvaluateResponse.class)
            .doOnSuccess(response -> 
                log.info("评测完成: evaluationId={}, score={}", 
                    response.getEvaluationId(), response.getOverallScore()))
            .doOnError(error -> 
                log.error("评测失败", error));
    }
    
    /**
     * 多智能体辩论评测
     */
    public Mono<DebateResponse> multiAgentDebate(DebateRequest request) {
        log.info("调用多智能体辩论评测");
        
        return webClient.post()
            .uri("/debate")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(DebateResponse.class);
    }
    
    /**
     * 对比模型
     */
    public Mono<CompareResponse> compareModels(CompareRequest request) {
        log.info("调用模型对比服务: baseline={}, new={}", 
            request.getBaselineModel(), request.getNewModel());
        
        return webClient.post()
            .uri("/compare")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(CompareResponse.class);
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
