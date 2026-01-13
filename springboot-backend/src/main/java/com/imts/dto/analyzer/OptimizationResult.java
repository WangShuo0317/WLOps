package com.imts.dto.analyzer;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * 优化结果
 * 
 * @version 5.0.0 - 新增进度跟踪和阶段信息
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OptimizationResult {
    
    /**
     * 任务ID
     */
    @JsonProperty("task_id")
    private String taskId;
    
    /**
     * 任务状态: pending/processing/completed/failed
     */
    private String status;
    
    /**
     * 优化模式: auto（标注流程优化）或 guided（指定优化）
     */
    private String mode;
    
    /**
     * 当前处理阶段
     * diagnostic: 全量诊断
     * optimization: 分批优化
     * generation: 分批生成
     * verification: 分批校验
     * cleaning: 全量清洗
     */
    @JsonProperty("current_phase")
    private String currentPhase;
    
    /**
     * 进度百分比 (0-100)
     */
    private Double progress;
    
    /**
     * 已完成批次数（优化/生成/校验阶段）
     */
    @JsonProperty("completed_batches")
    private Integer completedBatches;
    
    /**
     * 总批次数（优化/生成/校验阶段）
     */
    @JsonProperty("total_batches")
    private Integer totalBatches;
    
    /**
     * 优化后的数据集（纯净的高质量数据）
     * 仅在任务完成时返回
     */
    @JsonProperty("optimized_dataset")
    private List<Map<String, Object>> optimizedDataset;
    
    /**
     * 统计信息
     * 包含：
     * - input_size: 输入样本数
     * - output_size: 输出样本数
     * - optimization_stats: 优化统计
     * - verification_stats: 校验统计
     * - pii_cleaned_count: PII 清洗数量
     */
    private Map<String, Object> statistics;
    
    /**
     * 错误信息（如果失败）
     */
    private String error;
}
