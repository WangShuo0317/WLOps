"""
生成式数据增强器
针对稀缺样本自动合成新数据
"""
from typing import Dict, List, Any
from loguru import logger
import json

class DataAugmenter:
    """数据增强器"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def augment(self, dataset: List[Dict], analysis_result: Dict, strategy: str = "auto") -> List[Dict]:
        """
        增强数据集
        
        Args:
            dataset: 原始数据集
            analysis_result: 分析结果
            strategy: 增强策略
            
        Returns:
            增强后的样本列表
        """
        logger.info(f"开始数据增强，策略: {strategy}")
        
        augmented_samples = []
        
        # 根据策略选择增强方法
        if strategy == "auto":
            augmented_samples = self._auto_augment(dataset, analysis_result)
        elif strategy == "balance":
            augmented_samples = self._balance_augment(dataset, analysis_result)
        elif strategy == "expand":
            augmented_samples = self._expand_augment(dataset, analysis_result)
        elif strategy == "diversify":
            augmented_samples = self._diversify_augment(dataset, analysis_result)
        
        logger.info(f"生成了 {len(augmented_samples)} 个增强样本")
        return augmented_samples
    
    def _auto_augment(self, dataset: List[Dict], analysis: Dict) -> List[Dict]:
        """自动增强策略"""
        augmented = []
        
        # 1. 识别稀缺类别
        distribution = analysis.get("distribution_analysis", {})
        class_dist = distribution.get("class_distribution", {})
        
        if not class_dist:
            return augmented
        
        total = sum(class_dist.values())
        avg_count = total / len(class_dist)
        
        # 2. 为稀缺类别生成样本
        for label, count in class_dist.items():
            if count < avg_count * 0.5:  # 少于平均值的50%
                target_count = int(avg_count - count)
                logger.info(f"为类别 '{label}' 生成 {target_count} 个样本")
                
                # 找到该类别的示例
                examples = [item for item in dataset if self._get_label(item) == label]
                if examples:
                    new_samples = self._generate_similar_samples(examples[:3], target_count, label)
                    augmented.extend(new_samples)
        
        return augmented
    
    def _balance_augment(self, dataset: List[Dict], analysis: Dict) -> List[Dict]:
        """平衡类别分布"""
        augmented = []
        
        distribution = analysis.get("distribution_analysis", {})
        class_dist = distribution.get("class_distribution", {})
        
        if not class_dist:
            return augmented
        
        max_count = max(class_dist.values())
        
        # 将所有类别补充到最大类别的数量
        for label, count in class_dist.items():
            if count < max_count:
                target_count = max_count - count
                examples = [item for item in dataset if self._get_label(item) == label]
                if examples:
                    new_samples = self._generate_similar_samples(examples[:5], target_count, label)
                    augmented.extend(new_samples)
        
        return augmented
    
    def _expand_augment(self, dataset: List[Dict], analysis: Dict) -> List[Dict]:
        """扩展稀缺样本"""
        # 识别语义断层
        semantic_gaps = analysis.get("semantic_gaps", [])
        augmented = []
        
        for gap in semantic_gaps:
            if gap.get("gap_type") == "concept_missing":
                # 为缺失的概念生成样本
                concept = gap.get("description", "")
                new_samples = self._generate_concept_samples(concept, 10)
                augmented.extend(new_samples)
        
        return augmented
    
    def _diversify_augment(self, dataset: List[Dict], analysis: Dict) -> List[Dict]:
        """增加多样性"""
        augmented = []
        
        # 随机选择样本进行变换
        import random
        sample_indices = random.sample(range(len(dataset)), min(50, len(dataset)))
        
        for idx in sample_indices:
            original = dataset[idx]
            variants = self._generate_variants(original, 2)
            augmented.extend(variants)
        
        return augmented
    
    def _generate_similar_samples(self, examples: List[Dict], count: int, label: str) -> List[Dict]:
        """生成相似样本"""
        if not self.llm_client:
            logger.warning("LLM客户端未配置，跳过生成")
            return []
        
        generated = []
        
        # 构建提示词
        examples_text = "\n".join([
            f"问题: {self._get_field_value(ex, ['question', 'input', 'prompt'])}\n"
            f"答案: {self._get_field_value(ex, ['answer', 'output', 'response'])}"
            for ex in examples[:3]
        ])
        
        prompt = f"""请根据以下示例，生成{count}个类似的{label}类型的问答对。
保持相同的风格、难度和格式。

示例:
{examples_text}

请以JSON格式输出，每个样本包含question和answer字段:
[{{"question": "...", "answer": "..."}}, ...]
"""
        
        try:
            response = self.llm_client.generate(prompt, temperature=0.8)
            # 解析JSON响应
            generated = json.loads(response)
            
            # 添加标签
            for item in generated:
                item["label"] = label
                item["_augmented"] = True
                
        except Exception as e:
            logger.error(f"生成样本失败: {e}")
        
        return generated[:count]
    
    def _generate_concept_samples(self, concept: str, count: int) -> List[Dict]:
        """为特定概念生成样本"""
        if not self.llm_client:
            return []
        
        prompt = f"""请生成{count}个关于"{concept}"的问答对。
要求:
1. 问题清晰明确
2. 答案准确完整
3. 适合用于模型训练

以JSON格式输出:
[{{"question": "...", "answer": "..."}}, ...]
"""
        
        try:
            response = self.llm_client.generate(prompt, temperature=0.8)
            generated = json.loads(response)
            
            for item in generated:
                item["_augmented"] = True
                item["_concept"] = concept
                
            return generated[:count]
        except Exception as e:
            logger.error(f"生成概念样本失败: {e}")
            return []
    
    def _generate_variants(self, original: Dict, count: int) -> List[Dict]:
        """生成变体"""
        if not self.llm_client:
            return []
        
        question = self._get_field_value(original, ["question", "input", "prompt"])
        answer = self._get_field_value(original, ["answer", "output", "response"])
        
        prompt = f"""请对以下问答对进行改写，生成{count}个语义相同但表达不同的变体。

原始:
问题: {question}
答案: {answer}

以JSON格式输出:
[{{"question": "...", "answer": "..."}}, ...]
"""
        
        try:
            response = self.llm_client.generate(prompt, temperature=0.7)
            variants = json.loads(response)
            
            for item in variants:
                item["_augmented"] = True
                item["_variant_of"] = str(original)
                
            return variants[:count]
        except Exception as e:
            logger.error(f"生成变体失败: {e}")
            return []
    
    def _get_label(self, item: Dict) -> str:
        """获取样本标签"""
        return self._get_field_value(item, ["label", "category", "type", "class"]) or "unknown"
    
    def _get_field_value(self, item: Dict, field_names: List[str]) -> Any:
        """获取字段值"""
        for field in field_names:
            if field in item:
                return item[field]
        return None
