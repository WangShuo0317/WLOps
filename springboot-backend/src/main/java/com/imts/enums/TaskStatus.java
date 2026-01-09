package com.imts.enums;

/**
 * 任务状态枚举
 * 
 * 状态机流转：
 * PENDING -> OPTIMIZING -> TRAINING -> EVALUATING -> COMPLETED
 *                                                  -> LOOPING (持续学习模式)
 */
public enum TaskStatus {
    /**
     * 待处理 - 任务已创建，等待开始
     */
    PENDING("pending", "待处理"),
    
    /**
     * 数据优化中 - 正在执行数据清洗、增强、去重
     */
    OPTIMIZING("optimizing", "数据优化中"),
    
    /**
     * 训练中 - 正在执行模型训练
     */
    TRAINING("training", "训练中"),
    
    /**
     * 评估中 - 正在执行模型评估
     */
    EVALUATING("evaluating", "评估中"),
    
    /**
     * 已完成 - 任务成功完成
     */
    COMPLETED("completed", "已完成"),
    
    /**
     * 循环中 - 持续学习模式，准备下一轮迭代
     */
    LOOPING("looping", "循环中"),
    
    /**
     * 已失败 - 任务执行失败
     */
    FAILED("failed", "已失败"),
    
    /**
     * 已取消 - 任务被用户取消
     */
    CANCELLED("cancelled", "已取消"),
    
    /**
     * 已暂停 - 任务被暂停
     */
    SUSPENDED("suspended", "已暂停");
    
    private final String code;
    private final String description;
    
    TaskStatus(String code, String description) {
        this.code = code;
        this.description = description;
    }
    
    public String getCode() {
        return code;
    }
    
    public String getDescription() {
        return description;
    }
    
    /**
     * 检查是否可以转换到目标状态
     */
    public boolean canTransitionTo(TaskStatus target) {
        return switch (this) {
            case PENDING -> target == OPTIMIZING || target == CANCELLED;
            case OPTIMIZING -> target == TRAINING || target == FAILED || target == CANCELLED;
            case TRAINING -> target == EVALUATING || target == FAILED || target == CANCELLED;
            case EVALUATING -> target == COMPLETED || target == LOOPING || target == FAILED || target == CANCELLED;
            case LOOPING -> target == OPTIMIZING || target == COMPLETED || target == CANCELLED;
            case SUSPENDED -> target == OPTIMIZING || target == TRAINING || target == EVALUATING || target == CANCELLED;
            case COMPLETED, FAILED, CANCELLED -> false; // 终态不可转换
        };
    }
    
    /**
     * 是否为终态
     */
    public boolean isTerminal() {
        return this == COMPLETED || this == FAILED || this == CANCELLED;
    }
    
    /**
     * 是否为运行态
     */
    public boolean isRunning() {
        return this == OPTIMIZING || this == TRAINING || this == EVALUATING || this == LOOPING;
    }
}
