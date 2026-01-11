package com.imts.dto.analyzer;

import lombok.Data;
import java.util.List;

@Data
public class AnalyzeResponse {
    private String analysisId;
    private Double healthScore;
    private List<String> distributionBias;
    private List<String> semanticGaps;
    private List<String> recommendations;
}
