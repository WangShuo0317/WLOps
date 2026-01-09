package com.imts.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 数据集实体
 * 
 * 职责：仅负责元数据管理，不涉及数据处理逻辑
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "datasets")
public class Dataset {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    /**
     * 数据集唯一标识
     */
    @Column(unique = true, nullable = false)
    private String datasetId;
    
    /**
     * 数据集名称
     */
    @Column(nullable = false)
    private String name;
    
    /**
     * 数据集描述
     */
    @Column(length = 1000)
    private String description;
    
    /**
     * 存储路径（对象存储路径，如 s3://bucket/path/to/dataset.json）
     */
    @Column(nullable = false)
    private String storagePath;
    
    /**
     * 文件大小（字节）
     */
    private Long fileSize;
    
    /**
     * 样本数量
     */
    private Integer sampleCount;
    
    /**
     * 数据集类型（如：training, validation, test）
     */
    private String datasetType;
    
    /**
     * 领域（如：math, language, general）
     */
    private String domain;
    
    /**
     * 所属用户ID
     */
    @Column(nullable = false)
    private Long userId;
    
    /**
     * 是否为优化后的数据集
     */
    @Builder.Default
    private Boolean isOptimized = false;
    
    /**
     * 源数据集ID（如果是优化后的数据集）
     */
    private String sourceDatasetId;
    
    /**
     * 创建时间
     */
    @Column(nullable = false)
    private LocalDateTime createdAt;
    
    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }
    
    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
