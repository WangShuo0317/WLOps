package com.imts.dto.evaluation;

import lombok.Data;
import java.util.List;
import java.util.Map;

@Data
public class DebateResponse {
    private Double finalScore;
    private Boolean consensus;
    private List<Map<String, Object>> debateHistory;
    private String feedback;
}
