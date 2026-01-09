package com.imts.controller;

import com.imts.entity.MLTask;
import com.imts.entity.TaskExecution;
import com.imts.service.TaskManagementService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;

/**
 * 任务管理控制器
 * 
 * 提供任务生命周期管理的REST API
 */
@Slf4j
@RestController
@RequestMapping("/api/tasks")
@RequiredArgsConstructor
public class TaskController {
    
    private final TaskManagementService taskService;
    
    /**
     * 创建标准训练任务
     * 
     * POST /api/tasks/standard
     */
    @PostMapping("/standard")
    public Mono<ResponseEntity<MLTask>> createStandardTask(
        @RequestBody Map<String, Object> request
    ) {
        log.info("创建标准训练任务: {}", request);
        
        return taskService.createStandardTask(
            (String) request.get("taskName"),
            (String) request.get("modelName"),
            (String) request.get("datasetId"),
            Long.valueOf(request.get("userId").toString()),
            (String) request.get("hyperparameters")
        ).map(ResponseEntity::ok);
    }
    
    /**
     * 创建持续学习任务
     * 
     * POST /api/tasks/continuous
     */
    @PostMapping("/continuous")
    public Mono<ResponseEntity<MLTask>> createContinuousTask(
        @RequestBody Map<String, Object> request
    ) {
        log.info("创建持续学习任务: {}", request);
        
        Integer maxIterations = request.get("maxIterations") != null 
            ? Integer.valueOf(request.get("maxIterations").toString()) 
            : null;
        
        Double performanceThreshold = request.get("performanceThreshold") != null 
            ? Double.valueOf(request.get("performanceThreshold").toString()) 
            : null;
        
        return taskService.createContinuousTask(
            (String) request.get("taskName"),
            (String) request.get("modelName"),
            (String) request.get("datasetId"),
            Long.valueOf(request.get("userId").toString()),
            (String) request.get("hyperparameters"),
            maxIterations,
            performanceThreshold
        ).map(ResponseEntity::ok);
    }
    
    /**
     * 启动任务
     * 
     * POST /api/tasks/{taskId}/start
     */
    @PostMapping("/{taskId}/start")
    public Mono<ResponseEntity<Map<String, String>>> startTask(
        @PathVariable String taskId
    ) {
        log.info("启动任务: {}", taskId);
        
        return taskService.startTask(taskId)
            .then(Mono.just(ResponseEntity.ok(Map.of(
                "message", "任务已启动",
                "taskId", taskId
            ))))
            .onErrorResume(error -> 
                Mono.just(ResponseEntity.badRequest().body(Map.of(
                    "error", error.getMessage()
                )))
            );
    }
    
    /**
     * 暂停任务
     * 
     * POST /api/tasks/{taskId}/suspend
     */
    @PostMapping("/{taskId}/suspend")
    public Mono<ResponseEntity<Map<String, String>>> suspendTask(
        @PathVariable String taskId
    ) {
        log.info("暂停任务: {}", taskId);
        
        return taskService.suspendTask(taskId)
            .then(Mono.just(ResponseEntity.ok(Map.of(
                "message", "任务已暂停",
                "taskId", taskId
            ))));
    }
    
    /**
     * 取消任务
     * 
     * POST /api/tasks/{taskId}/cancel
     */
    @PostMapping("/{taskId}/cancel")
    public Mono<ResponseEntity<Map<String, String>>> cancelTask(
        @PathVariable String taskId
    ) {
        log.info("取消任务: {}", taskId);
        
        return taskService.cancelTask(taskId)
            .then(Mono.just(ResponseEntity.ok(Map.of(
                "message", "任务已取消",
                "taskId", taskId
            ))));
    }
    
    /**
     * 查询任务详情
     * 
     * GET /api/tasks/{taskId}
     */
    @GetMapping("/{taskId}")
    public Mono<ResponseEntity<MLTask>> getTask(
        @PathVariable String taskId
    ) {
        return taskService.getTask(taskId)
            .map(ResponseEntity::ok)
            .onErrorResume(error -> 
                Mono.just(ResponseEntity.notFound().build())
            );
    }
    
    /**
     * 查询用户的所有任务
     * 
     * GET /api/tasks/user/{userId}
     */
    @GetMapping("/user/{userId}")
    public Mono<ResponseEntity<List<MLTask>>> getUserTasks(
        @PathVariable Long userId
    ) {
        return taskService.getUserTasks(userId)
            .map(ResponseEntity::ok);
    }
    
    /**
     * 查询任务执行历史
     * 
     * GET /api/tasks/{taskId}/executions
     */
    @GetMapping("/{taskId}/executions")
    public Mono<ResponseEntity<List<TaskExecution>>> getTaskExecutions(
        @PathVariable String taskId
    ) {
        return taskService.getTaskExecutions(taskId)
            .map(ResponseEntity::ok);
    }
    
    /**
     * 查询任务当前迭代的执行记录
     * 
     * GET /api/tasks/{taskId}/executions/current
     */
    @GetMapping("/{taskId}/executions/current")
    public Mono<ResponseEntity<List<TaskExecution>>> getCurrentIterationExecutions(
        @PathVariable String taskId
    ) {
        return taskService.getCurrentIterationExecutions(taskId)
            .map(ResponseEntity::ok);
    }
    
    /**
     * 删除任务
     * 
     * DELETE /api/tasks/{taskId}
     */
    @DeleteMapping("/{taskId}")
    public Mono<ResponseEntity<Map<String, String>>> deleteTask(
        @PathVariable String taskId
    ) {
        log.info("删除任务: {}", taskId);
        
        return taskService.deleteTask(taskId)
            .then(Mono.just(ResponseEntity.ok(Map.of(
                "message", "任务已删除",
                "taskId", taskId
            ))))
            .onErrorResume(error -> 
                Mono.just(ResponseEntity.badRequest().body(Map.of(
                    "error", error.getMessage()
                )))
            );
    }
}
