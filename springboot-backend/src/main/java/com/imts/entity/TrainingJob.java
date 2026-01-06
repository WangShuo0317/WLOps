package com.imts.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

/**
 * 训练任务实体
 */
@Data
@Entity
@Table(name = "training_jobs")
public class TrainingJob {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(unique = true, nullable = false)
    private String jobId;
    
    @Column(nullable = false)
    private String modelName;
    
    @Column(nullable = false)
    private String dataset;
    
    @Column(nullable = false)
    private String status;
    
    private String outputDir;
    
    @Column(nullable = false)
    private LocalDateTime createdAt;
    
    private LocalDateTime updatedAt;
    
    private LocalDateTime completedAt;
}
