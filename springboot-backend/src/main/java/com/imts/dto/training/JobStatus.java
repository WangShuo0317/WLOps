package com.imts.dto.training;

import lombok.Data;

@Data
public class JobStatus {
    private String jobId;
    private String status;
    private Integer pid;
    private Double progress;
    private Double currentLoss;
}
