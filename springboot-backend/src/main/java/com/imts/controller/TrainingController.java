package com.imts.controller;

import com.imts.dto.training.*;
import com.imts.service.TrainingService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

/**
 * 训练控制器
 * 提供训练任务管理的REST API
 */
@RestController
@RequestMapping("/api/training")
@RequiredArgsConstructor
public class TrainingController {
    
    private final TrainingService trainingService;
    
    /**
     * 创建训练任务
     */
    @PostMapping("/jobs")
    public Mono<TrainingResponse> createJob(@Valid @RequestBody TrainingRequest request) {
        return trainingService.createTrainingJob(request);
    }
    
    /**
     * 查询任务状态
     */
    @GetMapping("/jobs/{jobId}")
    public Mono<JobStatus> getJobStatus(@PathVariable String jobId) {
        return trainingService.getJobStatus(jobId);
    }
    
    /**
     * 停止训练任务
     */
    @PostMapping("/jobs/{jobId}/stop")
    public Mono<Void> stopJob(@PathVariable String jobId) {
        return trainingService.stopTrainingJob(jobId);
    }
}
