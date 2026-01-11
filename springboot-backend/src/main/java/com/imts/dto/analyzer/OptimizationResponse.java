package com.imts.dto.analyzer;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 数据优化响应
 * 
 * @version 4.0.0 - 新增 mode 字段
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
     * 优化模式: auto（标注流程优化）或 guided（指定优化）
     */
    private String mode;
    
    /**
     * 状态消息
     */
    private String message;
}
