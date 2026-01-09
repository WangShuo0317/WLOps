package com.imts.dto.analyzer;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * 数据优化请求
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OptimizationRequest {
    
    /**
     * 原始数据集
     */
    private List<Map<String, Object>> dataset;
    
    /**
     * 知识库（用于RAG校验）
     */
    @JsonProperty("knowledge_base")
    private List<String> knowledgeBase;
    
    /**
     * 任务ID（可选）
     */
    @JsonProperty("task_id")
    private String taskId;
    
    /**
     * 是否保存分析报告
     */
    @JsonProperty("save_reports")
    private Boolean saveReports;
}
