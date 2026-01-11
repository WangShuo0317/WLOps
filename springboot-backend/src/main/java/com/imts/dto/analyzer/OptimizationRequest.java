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
 * 
 * @version 4.0.0 - 支持双模式（auto/guided）
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
     * 优化指导（可选）
     * 如果提供，使用"指定优化"模式；否则使用"标注流程优化"模式
     * 
     * 示例：
     * {
     *   "focus_areas": ["reasoning_quality"],
     *   "problem_indices": [0, 5, 10],
     *   "optimization_instructions": "为每个样本添加详细的推理步骤",
     *   "generation_instructions": "生成更多关于深度学习的样本"
     * }
     */
    @JsonProperty("optimization_guidance")
    private Map<String, Object> optimizationGuidance;
    
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
