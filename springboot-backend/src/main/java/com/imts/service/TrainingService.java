package com.imts.service;

import com.imts.client.TrainingServiceClient;
import com.imts.dto.training.*;
import com.imts.entity.TrainingJob;
import com.imts.repository.TrainingJobRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.LocalDateTime;

/**
 * 训练服务
 * 管理训练任务的完整生命周期
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class TrainingService {
    
    private final TrainingServiceClient trainingClient;
    private final TrainingJobRepository jobRepository;
    
    /**
     * 创建训练任务
     */
    public Mono<TrainingResponse> createTrainingJob(TrainingRequest request) {
        log.info("创建训练任务: model={}, dataset={}", 
            request.getModelName(), request.getDataset());
        
        return trainingClient.createTraining(request)
            .doOnSuccess(response -> {
                // 保存任务记录到数据库
                TrainingJob job = new TrainingJob();
                job.setJobId(response.getJobId());
                job.setModelName(request.getModelName());
                job.setDataset(request.getDataset());
                job.setStatus(response.getStatus());
                job.setCreatedAt(LocalDateTime.now());
                jobRepository.save(job);
                
                log.info("训练任务已保存到数据库: {}", response.getJobId());
            });
    }
    
    /**
     * 查询任务状态
     */
    public Mono<JobStatus> getJobStatus(String jobId) {
        return trainingClient.getJobStatus(jobId)
            .doOnSuccess(status -> {
                // 更新数据库中的状态
                jobRepository.findByJobId(jobId).ifPresent(job -> {
                    job.setStatus(status.getStatus());
                    job.setUpdatedAt(LocalDateTime.now());
                    jobRepository.save(job);
                });
            });
    }
    
    /**
     * 停止训练任务
     */
    public Mono<Void> stopTrainingJob(String jobId) {
        log.info("停止训练任务: {}", jobId);
        
        return trainingClient.stopJob(jobId)
            .doOnSuccess(v -> {
                jobRepository.findByJobId(jobId).ifPresent(job -> {
                    job.setStatus("stopped");
                    job.setUpdatedAt(LocalDateTime.now());
                    jobRepository.save(job);
                });
            });
    }
}
