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
     * 任务状态
     */
    private String status;
    
    /**
     * 优化后的数据集（纯净的高质量数据）
     */
    @JsonProperty("optimized_dataset")
    private List<Map<String, Object>> optimizedDataset;
    
    /**
     * 统计信息
     */
    private Map<String, Object> statistics;
    
    /**
     * 错误信息（如果失败）
     */
    private String error;
}
