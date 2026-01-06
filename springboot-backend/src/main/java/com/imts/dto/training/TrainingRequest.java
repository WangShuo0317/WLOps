package com.imts.dto.training;

import lombok.Data;
import jakarta.validation.constraints.*;

@Data
public class TrainingRequest {
    
    @NotBlank(message = "模型名称不能为空")
    private String modelName;
    
    @NotBlank(message = "数据集不能为空")
    private String dataset;
    
    private String stage = "sft";
    
    private String finetuningType = "lora";
    
    @Min(value = 1, message = "批次大小至少为1")
    private Integer batchSize = 2;
    
    @Positive(message = "学习率必须为正数")
    private Double learningRate = 5e-5;
    
    @Positive(message = "训练轮数必须为正数")
    private Double epochs = 3.0;
    
    private Integer maxSteps = -1;
    
    @Min(value = 1, message = "LoRA秩至少为1")
    private Integer loraRank = 8;
    
    @Min(value = 1, message = "LoRA alpha至少为1")
    private Integer loraAlpha = 16;
    
    private String outputDir;
}
