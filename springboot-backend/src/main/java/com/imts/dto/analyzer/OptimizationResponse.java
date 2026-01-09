package com.imts.dto.analyzer;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 数据优化响应
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OptimizationResponse {
    
    /**
     * 任务ID
     */
    @JsonProperty("task_id")
    private String taskId;
    
    /**
     * 任务状态: processing/completed/failed
     */
    private String status;
    
    /**
     * 状态消息
     */
    private String message;
}
