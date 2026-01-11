package com.imts.dto.evaluation;

import lombok.Data;
import java.util.Map;

@Data
public class CompareResponse {
    private Double baselineScore;
    private Double newModelScore;
    private Double improvement;
    private Double winRate;
    private Map<String, Object> radarChartData;
}
