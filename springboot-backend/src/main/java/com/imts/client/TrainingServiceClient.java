package com.imts.client;

import com.imts.dto.training.*;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

/**
 * 训练服务客户端
 * 调用Python训练微服务
 */
@Slf4j
@Component
public class TrainingServiceClient {
    
    private final WebClient webClient;
    
    public TrainingServiceClient(@Value("${python-services.training.url}") String baseUrl) {
        this.webClient = WebClient.builder()
            .baseUrl(baseUrl)
            .build();
    }
    
    /**
     * 创建训练任务
     */
    public Mono<TrainingResponse> createTraining(TrainingRequest request) {
        log.info("调用训练服务: model={}, dataset={}", 
            request.getModelName(), request.getDataset());
        
        return webClient.post()
            .uri("/train")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(TrainingResponse.class)
            .doOnSuccess(response -> 
                log.info("训练任务已创建: jobId={}", response.getJobId()))
            .doOnError(error -> 
                log.error("创建训练任务失败", error));
    }
    
    /**
     * 查询任务状态
     */
    public Mono<JobStatus> getJobStatus(String jobId) {
        return webClient.get()
            .uri("/jobs/{jobId}", jobId)
            .retrieve()
            .bodyToMono(JobStatus.class);
    }
    
    /**
     * 停止训练任务
     */
    public Mono<Void> stopJob(String jobId) {
        log.info("停止训练任务: jobId={}", jobId);
        return webClient.post()
            .uri("/jobs/{jobId}/stop", jobId)
            .retrieve()
            .bodyToMono(Void.class);
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
