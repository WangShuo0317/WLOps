"""
优化智能体
负责优化低质量样本和生成稀缺样本
"""
from typing import Dict, List, Any, Literal
from loguru import logger
import json


class OptimizationAgent:
    """优化智能体"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def optimize_samples(
        self,
        dataset: List[Dict],
        low_quality_samples: List[Dict],
        mode: Literal["auto", "guided"],
        guidance: Dict = None
    ) -> Dict[str, Any]:
        """
        优化低质量样本（COT 重写）
        
        仅当数据集包含 think 字段时才进行 COT 重写
        
        Args:
            dataset: 原始数据集
            low_quality_samples: 低质量样本列表
            mode: 优化模式
            guidance: 优化指导（guided 模式使用）
        """
        logger.info(f"  优化 {len(low_quality_samples)} 个低质量样本...")
        
        # 检查数据集是否包含 think 字段
        has_think_field = self._check_has_think_field(dataset)
        
        if not has_think_field:
            logger.info("  未检测到 think 字段，跳过 COT 重写，保留所有原始样本")
            # 不进行优化，直接返回原始数据集
            return {
                "samples": dataset.copy(),
                "count": 0,
                "high_quality_kept": len(dataset)
            }
        
        logger.info("  检测到 think 字段，执行 COT 重写...")
        
        optimized_samples = []
        high_quality_indices = set(range(len(dataset))) - set(
            lq["index"] for lq in low_quality_samples
        )
        
        # 保留高质量样本
        for idx in high_quality_indices:
            optimized_samples.append(dataset[idx])
        
        # 优化低质量样本
        success_count = 0
        for lq_item in low_quality_samples:
            sample = lq_item["sample"]
            
            try:
                if mode == "auto":
                    # 自动优化：添加 COT
                    optimized = self._add_cot_reasoning(sample)
                else:
                    # 指导优化：根据指导优化
                    optimized = self._optimize_with_guidance(sample, guidance)
                
                optimized["_optimized"] = True
                optimized_samples.append(optimized)
                success_count += 1
                
            except Exception as e:
                logger.warning(f"  优化样本失败: {e}")
                # 保留原样本
                optimized_samples.append(sample)
        
        return {
            "samples": optimized_samples,
            "count": success_count,
            "high_quality_kept": len(high_quality_indices)
        }
    
    def generate_samples(
        self,
        sparse_clusters: List[Dict],
        mode: Literal["auto", "guided"],
        guidance: Dict = None
    ) -> Dict[str, Any]:
        """
        生成稀缺样本
        
        Args:
            sparse_clusters: 稀缺聚类列表
            mode: 生成模式
            guidance: 生成指导（guided 模式使用）
        """
        logger.info(f"  为 {len(sparse_clusters)} 个稀缺聚类生成样本...")
        
        generated_samples = []
        
        for cluster in sparse_clusters:
            # 计算需要生成的数量
            target_count = max(5, 50 - cluster["size"])
            
            try:
                if mode == "auto":
                    # 自动生成
                    new_samples = self._generate_similar_samples(
                        cluster["sample_questions"],
                        target_count
                    )
                else:
                    # 指导生成
                    new_samples = self._generate_with_guidance(
                        cluster,
                        guidance,
                        target_count
                    )
                
                # 标记为生成样本
                for sample in new_samples:
                    sample["_generated"] = True
                
                generated_samples.extend(new_samples)
                
            except Exception as e:
                logger.warning(f"  生成样本失败: {e}")
        
        return {
            "samples": generated_samples,
            "count": len(generated_samples)
        }
    
    def _add_cot_reasoning(self, sample: Dict) -> Dict:
        """为样本添加 COT 推理过程"""
        question = sample.get("question", sample.get("instruction", ""))
        answer = sample.get("answer", sample.get("output", ""))
        
        prompt = f"""请为以下问答对添加详细的推理过程（Chain of Thought）。

问题: {question}
答案: {answer}

请生成一个包含详细推理步骤的完整回答，格式如下：
{{
    "question": "原问题",
    "reasoning": "详细的推理过程，包含多个步骤",
    "answer": "最终答案"
}}

只返回 JSON，不要其他内容。"""
        
        response = self.llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        
        try:
            result = json.loads(response)
            return {
                **sample,
                "reasoning": result.get("reasoning", ""),
                "answer": result.get("answer", answer)
            }
        except:
            # 解析失败，返回原样本加简单推理
            return {
                **sample,
                "reasoning": response
            }
    
    def _optimize_with_guidance(self, sample: Dict, guidance: Dict) -> Dict:
        """根据优化指导优化样本"""
        optimization_instructions = guidance.get("optimization_instructions", "")
        
        question = sample.get("question", sample.get("instruction", ""))
        answer = sample.get("answer", sample.get("output", ""))
        
        prompt = f"""根据以下优化指导，改进这个样本：

优化指导: {optimization_instructions}

原始样本:
问题: {question}
答案: {answer}

请生成优化后的样本，格式如下：
{{
    "question": "优化后的问题",
    "reasoning": "详细的推理过程",
    "answer": "优化后的答案"
}}

只返回 JSON，不要其他内容。"""
        
        response = self.llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        
        try:
            result = json.loads(response)
            return {
                **sample,
                "question": result.get("question", question),
                "reasoning": result.get("reasoning", ""),
                "answer": result.get("answer", answer)
            }
        except:
            return {
                **sample,
                "reasoning": response
            }
    
    def _generate_similar_samples(
        self, 
        seed_questions: List[str], 
        count: int
    ) -> List[Dict]:
        """基于种子问题生成相似样本"""
        prompt = f"""基于以下种子问题，生成 {count} 个相似但不重复的问答对。

种子问题:
{chr(10).join(f"- {q}" for q in seed_questions)}

要求：
1. 保持相似的主题和风格
2. 每个问答对都要包含详细的推理过程
3. 确保多样性，不要重复

请生成 JSON 数组格式：
[
    {{
        "question": "问题1",
        "reasoning": "推理过程1",
        "answer": "答案1"
    }},
    ...
]

只返回 JSON 数组，不要其他内容。"""
        
        response = self.llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=2000
        )
        
        try:
            samples = json.loads(response)
            return samples[:count]
        except:
            logger.warning("  生成样本解析失败，返回空列表")
            return []
    
    def _generate_with_guidance(
        self,
        cluster: Dict,
        guidance: Dict,
        count: int
    ) -> List[Dict]:
        """根据指导生成样本"""
        generation_instructions = guidance.get("generation_instructions", "")
        
        prompt = f"""根据以下指导，生成 {count} 个新样本。

生成指导: {generation_instructions}

参考样本:
{chr(10).join(f"- {q}" for q in cluster["sample_questions"])}

请生成 JSON 数组格式：
[
    {{
        "question": "问题1",
        "reasoning": "推理过程1",
        "answer": "答案1"
    }},
    ...
]

只返回 JSON 数组，不要其他内容。"""
        
        response = self.llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=2000
        )
        
        try:
            samples = json.loads(response)
            return samples[:count]
        except:
            logger.warning("  生成样本解析失败，返回空列表")
            return []

    
    def _check_has_think_field(self, dataset: List[Dict]) -> bool:
        """
        检查数据集是否包含 think 字段（不区分大小写）
        
        只要有一个样本包含 think 字段，就认为整个数据集需要 COT 重写
        """
        if not dataset:
            return False
        
        # 检查前几个样本（最多检查10个）
        sample_size = min(10, len(dataset))
        
        for sample in dataset[:sample_size]:
            # 检查所有键（不区分大小写）
            for key in sample.keys():
                if key.lower() == 'think':
                    return True
        
        return False
