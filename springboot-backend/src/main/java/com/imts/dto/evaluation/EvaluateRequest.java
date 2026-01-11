package com.imts.dto.evaluation;

import lombok.Data;

@Data
public class EvaluateRequest {
    private String modelPath;
    private String testDataset;
    private Boolean enableDebate = true;
    private Integer debateRounds = 3;
}
