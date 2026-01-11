"""
清洗智能体
负责清洗 PII（个人身份信息）
"""
from typing import Dict, List, Any, Tuple
from loguru import logger
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from config import config


class CleaningAgent:
    """清洗智能体"""
    
    def __init__(self):
        """初始化 PII 检测和清洗引擎"""
        try:
            self.analyzer = AnalyzerEngine()
            self.anonymizer = AnonymizerEngine()
            logger.info("PII 清洗引擎初始化成功")
        except Exception as e:
            logger.warning(f"PII 清洗引擎初始化失败: {e}")
            self.analyzer = None
            self.anonymizer = None
    
    def clean_dataset(self, dataset: List[Dict]) -> Dict[str, Any]:
        """
        清洗数据集中的 PII
        
        Args:
            dataset: 待清洗的数据集
            
        Returns:
            {
                "cleaned_dataset": 清洗后的数据集,
                "cleaned_count": 清洗的样本数量
            }
        """
        if not self.analyzer or not self.anonymizer:
            logger.warning("PII 清洗引擎未初始化，跳过清洗")
            return {
                "cleaned_dataset": dataset,
                "cleaned_count": 0
            }
        
        logger.info(f"  清洗 {len(dataset)} 个样本的 PII...")
        
        cleaned_dataset = []
        cleaned_count = 0
        
        for sample in dataset:
            cleaned_sample, was_cleaned = self._clean_sample(sample)
            cleaned_dataset.append(cleaned_sample)
            if was_cleaned:
                cleaned_count += 1
        
        return {
            "cleaned_dataset": cleaned_dataset,
            "cleaned_count": cleaned_count
        }
    
    def _clean_sample(self, sample: Dict) -> Tuple[Dict, bool]:
        """
        清洗单个样本
        
        Returns:
            (cleaned_sample, was_cleaned)
        """
        was_cleaned = False
        cleaned_sample = {}
        
        for key, value in sample.items():
            if isinstance(value, str):
                cleaned_value, cleaned = self._clean_text(value)
                cleaned_sample[key] = cleaned_value
                if cleaned:
                    was_cleaned = True
            else:
                cleaned_sample[key] = value
        
        return cleaned_sample, was_cleaned
    
    def _clean_text(self, text: str) -> Tuple[str, bool]:
        """
        清洗文本中的 PII
        
        Returns:
            (cleaned_text, was_cleaned)
        """
        if not text or len(text) < 3:
            return text, False
        
        try:
            # 分析 PII
            results = self.analyzer.analyze(
                text=text,
                entities=config.PII_ENTITIES,
                language=config.PII_LANGUAGE
            )
            
            if not results:
                return text, False
            
            # 匿名化
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators={
                    "DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"}),
                    "PERSON": OperatorConfig("replace", {"new_value": "[姓名]"}),
                    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[电话]"}),
                    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[邮箱]"}),
                    "LOCATION": OperatorConfig("replace", {"new_value": "[地址]"}),
                }
            )
            
            return anonymized_result.text, True
            
        except Exception as e:
            logger.warning(f"  清洗文本失败: {e}")
            return text, False
