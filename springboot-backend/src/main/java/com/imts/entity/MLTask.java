package com.imts.entity;

import com.imts.enums.TaskMode;
import com.imts.enums.TaskStatus;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 机器学习任务实体
 * 
 * 管理完整的训练任务生命周期
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "ml_tasks")
public class MLTask {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    /**
     * 任务唯一标识
     */
    @Column(unique = true, nullable = false)
    private String taskId;
    
    /**
     * 任务名称
     */
    @Column(nullable = false)
    private String taskName;
    
    /**
     * 任务模式：STANDARD（标准流） 或 CONTINUOUS（持续学习流）
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private TaskMode taskMode;
    
    /**
     * 任务状态
     */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private TaskStatus status;
    
    /**
     * 模型名称
     */
    @Column(nullable = false)
    private String modelName;
    
    /**
     * 原始数据集ID
     */
    @Column(nullable = false)
    private String datasetId;
    
    /**
     * 当前使用的数据集ID（可能是优化后的）
     */
    private String currentDatasetId;
    
    /**
     * 所属用户ID
     */
    @Column(nullable = false)
    private Long userId;
    
    /**
     * 当前迭代轮次（持续学习模式）
     */
    @Builder.Default
    private Integer currentIteration = 0;
    
    /**
     * 最大迭代次数（持续学习模式）
     */
    private Integer maxIterations;
    
    /**
     * 性能阈值（持续学习模式终止条件）
     */
    private Double performanceThreshold;
    
    /**
     * 训练超参数（JSON格式）
     */
    @Column(length = 2000)
    private String hyperparameters;
    
    /**
     * 最新模型路径
     */
    private String latestModelPath;
    
    /**
     * 最新评估报告路径
     */
    private String latestEvaluationPath;
    
    /**
     * 最新评估分数
     */
    private Double latestScore;
    
    /**
     * 错误信息
     */
    @Column(length = 2000)
    private String errorMessage;
    
    /**
     * 创建时间
     */
    @Column(nullable = false)
    private LocalDateTime createdAt;
    
    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
    
    /**
     * 开始时间
     */
    private LocalDateTime startedAt;
    
    /**
     * 完成时间
     */
    private LocalDateTime completedAt;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }
    
    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
    
    /**
     * 更新任务状态
     */
    public void updateStatus(TaskStatus newStatus) {
        if (!this.status.canTransitionTo(newStatus)) {
            throw new IllegalStateException(
                String.format("无法从状态 %s 转换到 %s", this.status, newStatus)
            );
        }
        this.status = newStatus;
        this.updatedAt = LocalDateTime.now();
        
        if (newStatus == TaskStatus.OPTIMIZING && this.startedAt == null) {
            this.startedAt = LocalDateTime.now();
        }
        
        if (newStatus.isTerminal()) {
            this.completedAt = LocalDateTime.now();
        }
    }
    
    /**
     * 增加迭代次数
     */
    public void incrementIteration() {
        this.currentIteration++;
    }
    
    /**
     * 检查是否应该继续迭代
     */
    public boolean shouldContinueIteration() {
        if (taskMode != TaskMode.CONTINUOUS) {
            return false;
        }
        
        // 检查最大迭代次数
        if (maxIterations != null && currentIteration >= maxIterations) {
            return false;
        }
        
        // 检查性能阈值
        if (performanceThreshold != null && latestScore != null 
            && latestScore >= performanceThreshold) {
            return false;
        }
        
        return true;
    }
}
