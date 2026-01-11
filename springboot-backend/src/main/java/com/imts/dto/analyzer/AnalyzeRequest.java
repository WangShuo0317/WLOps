package com.imts.dto.analyzer;

import lombok.Data;

@Data
public class AnalyzeRequest {
    private String datasetPath;
    private String userIntent;
    private String taskType;
}
