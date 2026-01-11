package com.imts.dto.analyzer;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 健康检查响应
 * 
 * @version 4.0.0 - 新增 workflow_engine 字段
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class HealthResponse {
    
    /**
     * 服务状态
     */
    private String status;
    
    /**
     * 服务名称
     */
    private String service;
    
    /**
     * 版本号
     */
    private String version;
    
    /**
     * LLM 是否可用
     */
    @JsonProperty("llm_available")
    private Boolean llmAvailable;
    
    /**
     * Embedding 模型名称
     */
    @JsonProperty("embedding_model")
    private String embeddingModel;
    
    /**
     * 工作流引擎（LangGraph）
     */
    @JsonProperty("workflow_engine")
    private String workflowEngine;
}
