package com.imts.dto.evaluation;

import lombok.Data;
import java.util.Map;

@Data
public class EvaluateResponse {
    private String evaluationId;
    private Double overallScore;
    private Map<String, Double> metrics;
    private Integer badCasesCount;
}
