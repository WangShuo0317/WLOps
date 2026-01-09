package com.imts.enums;

/**
 * 任务模式枚举
 */
public enum TaskMode {
    /**
     * 标准训练流 - 单次执行：优化 -> 训练 -> 评估 -> 完成
     */
    STANDARD("standard", "标准训练流"),
    
    /**
     * 持续学习流 - 循环执行：优化 -> 训练 -> 评估 -> 反馈优化 -> ...
     */
    CONTINUOUS("continuous", "持续学习流");
    
    private final String code;
    private final String description;
    
    TaskMode(String code, String description) {
        this.code = code;
        this.description = description;
    }
    
    public String getCode() {
        return code;
    }
    
    public String getDescription() {
        return description;
    }
}
