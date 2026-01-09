"""
意图-数据匹配度分析器
避免"数据与目标不符"的基础性错误
"""
from typing import Dict, List, Any
from loguru import logger
import json

class IntentMatcher:
    """意图匹配分析器"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    def analyze_match(self, dataset: List[Dict], user_intent: str, task_type: str = None) -> Dict[str, Any]:
        """
        分析数据集与用户意图的匹配度
        
        Args:
            dataset: 数据集
            user_intent: 用户意图描述
            task_type: 任务类型
            
        Returns:
            匹配度分析结果
        """
        logger.info(f"开始意图匹配分析，数据集大小: {len(dataset)}")
        
        # 1. 提取数据集特征
        dataset_features = self._extract_dataset_features(dataset)
        
        # 2. 解析用户意图
        intent_requirements = self._parse_intent(user_intent, task_type)
        
        # 3. 计算匹配度
        match_score = self._calculate_match_score(dataset_features, intent_requirements)
        
        # 4. 识别匹配和不匹配的方面
        matched, mismatched = self._identify_matches(dataset_features, intent_requirements)
        
        # 5. 生成改进建议
        suggestions = self._generate_suggestions(mismatched, intent_requirements)
        
        return {
            "score": match_score,
            "matched_aspects": matched,
            "mismatched_aspects": mismatched,
            "suggestions": suggestions,
            "dataset_features": dataset_features,
            "intent_requirements": intent_requirements
        }
    
    def _extract_dataset_features(self, dataset: List[Dict]) -> Dict[str, Any]:
        """提取数据集特征"""
        features = {
            "total_samples": len(dataset),
            "has_questions": False,
            "has_answers": False,
            "has_reasoning": False,
            "has_context": False,
            "avg_question_length": 0,
            "avg_answer_length": 0,
            "content_types": set(),
            "domains": set()
        }
        
        if not dataset:
            return features
        
        # 分析样本结构
        sample = dataset[0]
        features["has_questions"] = any(k in sample for k in ["question", "input", "prompt", "query"])
        features["has_answers"] = any(k in sample for k in ["answer", "output", "response", "label"])
        features["has_reasoning"] = any(k in sample for k in ["reasoning", "rationale", "explanation", "steps", "cot"])
        features["has_context"] = any(k in sample for k in ["context", "background", "passage"])
        
        # 统计长度
        question_lengths = []
        answer_lengths = []
        
        for item in dataset[:100]:  # 采样前100个
            q = self._get_field_value(item, ["question", "input", "prompt", "query"])
            a = self._get_field_value(item, ["answer", "output", "response"])
            
            if q:
                question_lengths.append(len(str(q)))
            if a:
                answer_lengths.append(len(str(a)))
        
        if question_lengths:
            features["avg_question_length"] = sum(question_lengths) / len(question_lengths)
        if answer_lengths:
            features["avg_answer_length"] = sum(answer_lengths) / len(answer_lengths)
        
        # 识别内容类型（简单启发式）
        sample_texts = [str(v) for item in dataset[:50] for v in item.values()]
        combined_text = " ".join(sample_texts).lower()
        
        if any(word in combined_text for word in ["数学", "计算", "加", "减", "乘", "除", "+", "-", "*", "/"]):
            features["content_types"].add("math")
        if any(word in combined_text for word in ["为什么", "如何", "解释", "原因"]):
            features["content_types"].add("reasoning")
        if any(word in combined_text for word in ["分类", "类别", "标签"]):
            features["content_types"].add("classification")
        
        features["content_types"] = list(features["content_types"])
        
        return features
    
    def _parse_intent(self, user_intent: str, task_type: str = None) -> Dict[str, Any]:
        """解析用户意图"""
        requirements = {
            "task_type": task_type,
            "requires_reasoning": False,
            "requires_context": False,
            "domain": None,
            "quality_expectations": []
        }
        
        if not user_intent:
            return requirements
        
        intent_lower = user_intent.lower()
        
        # 识别是否需要推理
        if any(word in intent_lower for word in ["推理", "思考", "解释", "步骤", "过程", "cot"]):
            requirements["requires_reasoning"] = True
            requirements["quality_expectations"].append("需要详细的推理过程")
        
        # 识别领域
        if any(word in intent_lower for word in ["数学", "算术", "计算"]):
            requirements["domain"] = "math"
        elif any(word in intent_lower for word in ["阅读", "理解", "文本"]):
            requirements["domain"] = "reading_comprehension"
        elif any(word in intent_lower for word in ["对话", "聊天", "问答"]):
            requirements["domain"] = "conversation"
        
        # 识别质量期望
        if "高质量" in intent_lower or "准确" in intent_lower:
            requirements["quality_expectations"].append("需要高质量标注")
        if "多样" in intent_lower:
            requirements["quality_expectations"].append("需要样本多样性")
        
        return requirements
    
    def _calculate_match_score(self, features: Dict, requirements: Dict) -> float:
        """计算匹配度分数"""
        score = 100.0
        
        # 基础结构检查
        if not features["has_questions"]:
            score -= 30
        if not features["has_answers"]:
            score -= 30
        
        # 推理需求检查
        if requirements["requires_reasoning"] and not features["has_reasoning"]:
            score -= 20
        
        # 领域匹配检查
        if requirements["domain"]:
            if requirements["domain"] not in features["content_types"]:
                score -= 15
        
        # 样本数量检查
        if features["total_samples"] < 100:
            score -= 10
        
        return max(0.0, min(100.0, score))
    
    def _identify_matches(self, features: Dict, requirements: Dict) -> tuple:
        """识别匹配和不匹配的方面"""
        matched = []
        mismatched = []
        
        if features["has_questions"] and features["has_answers"]:
            matched.append("数据集包含问答对结构")
        else:
            mismatched.append("数据集缺少完整的问答对结构")
        
        if requirements["requires_reasoning"]:
            if features["has_reasoning"]:
                matched.append("包含推理过程")
            else:
                mismatched.append("缺少推理过程（COT）")
        
        if requirements["domain"]:
            if requirements["domain"] in features["content_types"]:
                matched.append(f"内容领域匹配: {requirements['domain']}")
            else:
                mismatched.append(f"内容领域不匹配，期望: {requirements['domain']}")
        
        if features["total_samples"] >= 100:
            matched.append(f"样本数量充足: {features['total_samples']}")
        else:
            mismatched.append(f"样本数量不足: {features['total_samples']} < 100")
        
        return matched, mismatched
    
    def _generate_suggestions(self, mismatched: List[str], requirements: Dict) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        for issue in mismatched:
            if "缺少推理过程" in issue:
                suggestions.append("建议使用COT重写功能为样本补充推理链")
            elif "样本数量不足" in issue:
                suggestions.append("建议使用生成式增强功能扩充数据集")
            elif "领域不匹配" in issue:
                suggestions.append(f"建议调整数据集内容以匹配目标领域: {requirements['domain']}")
            elif "缺少完整的问答对" in issue:
                suggestions.append("建议检查数据格式，确保每个样本包含问题和答案字段")
        
        return suggestions
    
    def _get_field_value(self, item: Dict, field_names: List[str]) -> Any:
        """获取字段值（支持多个可能的字段名）"""
        for field in field_names:
            if field in item:
                return item[field]
        return None
