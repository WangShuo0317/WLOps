"""
数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from enum import Enum

class TaskType(str, Enum):
    """任务类型"""
    CLASSIFICATION = "classification"
    QA = "qa"
    REASONING = "reasoning"
    GENERATION = "generation"
    MATH = "math"

class AnalyzeRequest(BaseModel):
    """分析请求"""
    dataset_path: str = Field(..., description="数据集路径或JSON数据")
    user_intent: Optional[str] = Field(None, description="用户意图描述，如'训练小学数学解题模型'")
    task_type: Optional[TaskType] = Field(None, description="任务类型")
    is_json_data: bool = Field(False, description="是否直接传入JSON数据")

class IntentMatchScore(BaseModel):
    """意图匹配评分"""
    score: float = Field(..., ge=0, le=100, description="匹配度分数")
    matched_aspects: List[str] = Field(default_factory=list, description="匹配的方面")
    mismatched_aspects: List[str] = Field(default_factory=list, description="不匹配的方面")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")

class DistributionAnalysis(BaseModel):
    """分布分析"""
    class_distribution: Dict[str, int] = Field(default_factory=dict, description="类别分布")
    bias_detected: List[str] = Field(default_factory=list, description="检测到的偏差")
    imbalance_ratio: float = Field(0.0, description="不平衡比率")

class SemanticGap(BaseModel):
    """语义断层"""
    gap_type: str = Field(..., description="断层类型")
    description: str = Field(..., description="描述")
    severity: str = Field(..., description="严重程度: low/medium/high")
    examples: List[str] = Field(default_factory=list, description="示例")

class ReasoningDepthAnalysis(BaseModel):
    """推理深度分析"""
    avg_reasoning_steps: float = Field(0.0, description="平均推理步数")
    samples_without_cot: int = Field(0, description="缺少推理链的样本数")
    reasoning_quality_score: float = Field(0.0, ge=0, le=100, description="推理质量分数")

class AnalyzeResponse(BaseModel):
    """分析响应"""
    analysis_id: str
    health_score: float = Field(..., ge=0, le=100, description="数据健康度评分")
    intent_match: IntentMatchScore
    distribution_analysis: DistributionAnalysis
    semantic_gaps: List[SemanticGap]
    reasoning_depth: ReasoningDepthAnalysis
    recommendations: List[str]
    detailed_report: Dict[str, Any] = Field(default_factory=dict)

class AugmentationStrategy(str, Enum):
    """增强策略"""
    AUTO = "auto"
    BALANCE = "balance"  # 平衡类别分布
    EXPAND = "expand"  # 扩展稀缺样本
    DIVERSIFY = "diversify"  # 增加多样性

class OptimizeRequest(BaseModel):
    """优化请求"""
    dataset_path: str
    analysis_result: Optional[Dict[str, Any]] = None
    augmentation_strategy: AugmentationStrategy = AugmentationStrategy.AUTO
    enable_cot_rewriting: bool = Field(True, description="是否启用COT推理链补全")
    enable_pii_cleaning: bool = Field(True, description="是否启用PII清洗")
    target_sample_count: Optional[int] = Field(None, description="目标样本数量")

class OptimizeResponse(BaseModel):
    """优化响应"""
    optimized_dataset_path: str
    improvements: Dict[str, Any]
    augmented_samples: int = 0
    cot_completed_samples: int = 0
    pii_cleaned_samples: int = 0
    quality_improvement: float = 0.0

class PIICleanRequest(BaseModel):
    """PII清洗请求"""
    text: str = Field(..., description="待清洗文本")
    preserve_semantics: bool = Field(True, description="是否保留语义")
    language: str = Field("zh", description="语言代码")

class PIICleanResponse(BaseModel):
    """PII清洗响应"""
    cleaned_text: str
    detected_entities: List[Dict[str, Any]]
    replacements: Dict[str, str]

class COTRewriteRequest(BaseModel):
    """COT重写请求"""
    question: str
    answer: str
    context: Optional[str] = None

class COTRewriteResponse(BaseModel):
    """COT重写响应"""
    question: str
    rationale: str
    answer: str
    reasoning_steps: int
