package com.imts.dto.evaluation;

import lombok.Data;

@Data
public class DebateRequest {
    private String question;
    private String modelResponse;
    private String groundTruth;
    private Integer debateRounds = 3;
}
