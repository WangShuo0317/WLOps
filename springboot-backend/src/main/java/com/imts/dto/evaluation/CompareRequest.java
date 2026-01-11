package com.imts.dto.evaluation;

import lombok.Data;

@Data
public class CompareRequest {
    private String baselineModel;
    private String newModel;
    private String testDataset;
}
