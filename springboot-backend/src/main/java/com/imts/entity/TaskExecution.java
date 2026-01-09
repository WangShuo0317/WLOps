package com.imts.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 任务执行记录
 * 
 * 记录每个阶段的执行详情
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "task_executions")
public class TaskExecution {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    /**
     * 所属任务ID
     */
    @Column(nullable = false)
    private String taskId;
    
    /**
     * 迭代轮次
     */
    @Column(nullable = false)
    private Integer iteration;
    
    /**
     * 执行阶段：optimization, training, evaluation
     */
    @Column(nullable = false)
    private String phase;
    
    /**
     * 执行状态：running, completed, failed
     */
    @Column(nullable = false)
    private String status;
    
    /**
     * 输入数据集ID
     */
    private String inputDatasetId;
    
    /**
     * 输出数据集ID（优化阶段）
     */
    private String outputDatasetId;
    
    /**
     * 模型路径（训练阶段）
     */
    private String modelPath;
    
    /**
     * 评估报告路径（评估阶段）
     */
    private String evaluationPath;
    
    /**
     * 评估分数
     */
    private Double score;
    
    /**
     * 执行日志路径
     */
    private String logPath;
    
    /**
     * 执行详情（JSON格式）
     */
    @Column(length = 5000)
    private String details;
    
    /**
     * 错误信息
     */
    @Column(length = 2000)
    private String errorMessage;
    
    /**
     * 开始时间
     */
    @Column(nullable = false)
    private LocalDateTime startedAt;
    
    /**
     * 完成时间
     */
    private LocalDateTime completedAt;
    
    /**
     * 执行耗时（秒）
     */
    private Long durationSeconds;
    
    @PrePersist
    protected void onCreate() {
        if (startedAt == null) {
            startedAt = LocalDateTime.now();
        }
    }
    
    /**
     * 标记完成
     */
    public void markCompleted() {
        this.status = "completed";
        this.completedAt = LocalDateTime.now();
        this.durationSeconds = java.time.Duration.between(startedAt, completedAt).getSeconds();
    }
    
    /**
     * 标记失败
     */
    public void markFailed(String error) {
        this.status = "failed";
        this.errorMessage = error;
        this.completedAt = LocalDateTime.now();
        this.durationSeconds = java.time.Duration.between(startedAt, completedAt).getSeconds();
    }
}
