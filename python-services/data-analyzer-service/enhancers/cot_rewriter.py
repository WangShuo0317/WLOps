"""
COT推理链补全器
将Q->A格式的数据丰富为Q->Rationale->A
"""
from typing import Dict, List, Any
from loguru import logger
import json

class COTRewriter:
    """COT推理链重写器"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    def rewrite_dataset(self, dataset: List[Dict]) -> tuple[List[Dict], int]:
        """
        为数据集补全COT推理链
        
        Args:
            dataset: 数据集
            
        Returns:
            (重写后的数据集, 重写的样本数)
        """
        logger.info(f"开始COT重写，数据集大小: {len(dataset)}")
        
        rewritten_dataset = []
        rewritten_count = 0
        
        for item in dataset:
            # 检查是否已有推理过程
            has_reasoning = any(k in item for k in [
                "reasoning", "rationale", "explanation", "steps", "cot", "chain_of_thought"
            ])
            
            if has_reasoning:
                rewritten_dataset.append(item)
            else:
                # 补全推理链
                rewritten_item = self.rewrite_single(item)
                if rewritten_item:
                    rewritten_dataset.append(rewritten_item)
                    rewritten_count += 1
                else:
                    rewritten_dataset.append(item)
        
        logger.info(f"完成COT重写，重写了 {rewritten_count} 个样本")
        return rewritten_dataset, rewritten_count
    
    def rewrite_single(self, item: Dict) -> Dict:
        """
        为单个样本补全COT
        
        Args:
            item: 原始样本
            
        Returns:
            补全后的样本
        """
        question = self._get_field_value(item, ["question", "input", "prompt", "query"])
        answer = self._get_field_value(item, ["answer", "output", "response"])
        context = self._get_field_value(item, ["context", "background", "passage"])
        
        if not question or not answer:
            logger.warning("样本缺少问题或答案，跳过")
            return None
        
        # 生成推理过程
        rationale = self._generate_rationale(question, answer, context)
        
        if rationale:
            # 创建新样本
            new_item = item.copy()
            new_item["rationale"] = rationale
            new_item["_cot_rewritten"] = True
            return new_item
        
        return None
    
    def _generate_rationale(self, question: str, answer: str, context: str = None) -> str:
        """
        生成推理过程
        
        Args:
            question: 问题
            answer: 答案
            context: 上下文
            
        Returns:
            推理过程
        """
        if not self.llm_client:
            logger.warning("LLM客户端未配置，无法生成推理过程")
            return None
        
        # 构建提示词
        prompt = self._build_cot_prompt(question, answer, context)
        
        try:
            rationale = self.llm_client.generate(prompt, temperature=0.7, max_tokens=500)
            return rationale.strip()
        except Exception as e:
            logger.error(f"生成推理过程失败: {e}")
            return None
    
    def _build_cot_prompt(self, question: str, answer: str, context: str = None) -> str:
        """构建COT提示词"""
        
        if context:
            prompt = f"""请为以下问答对补充详细的推理过程（Chain of Thought）。

上下文: {context}

问题: {question}

答案: {answer}

请提供从问题到答案的完整推理步骤，包括:
1. 理解问题的关键信息
2. 分析解题思路
3. 逐步推导过程
4. 得出最终答案

推理过程:"""
        else:
            prompt = f"""请为以下问答对补充详细的推理过程（Chain of Thought）。

问题: {question}

答案: {answer}

请提供从问题到答案的完整推理步骤，要求:
1. 清晰的逻辑链条
2. 分步骤说明
3. 解释每一步的原因
4. 自然流畅的表达

推理过程:"""
        
        return prompt
    
    def batch_rewrite(self, items: List[Dict], batch_size: int = 10) -> List[Dict]:
        """
        批量重写（提高效率）
        
        Args:
            items: 样本列表
            batch_size: 批次大小
            
        Returns:
            重写后的样本列表
        """
        rewritten = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            batch_results = self._batch_generate_rationales(batch)
            rewritten.extend(batch_results)
        
        return rewritten
    
    def _batch_generate_rationales(self, batch: List[Dict]) -> List[Dict]:
        """批量生成推理过程"""
        if not self.llm_client:
            return batch
        
        # 构建批量提示词
        qa_pairs = []
        for idx, item in enumerate(batch):
            question = self._get_field_value(item, ["question", "input", "prompt"])
            answer = self._get_field_value(item, ["answer", "output", "response"])
            if question and answer:
                qa_pairs.append(f"{idx+1}. 问题: {question}\n   答案: {answer}")
        
        prompt = f"""请为以下{len(qa_pairs)}个问答对分别补充推理过程。

{chr(10).join(qa_pairs)}

请以JSON数组格式输出，每个元素包含rationale字段:
[{{"rationale": "..."}}, {{"rationale": "..."}}, ...]
"""
        
        try:
            response = self.llm_client.generate(prompt, temperature=0.7, max_tokens=2000)
            rationales = json.loads(response)
            
            # 合并结果
            results = []
            for item, rationale_obj in zip(batch, rationales):
                new_item = item.copy()
                new_item["rationale"] = rationale_obj.get("rationale", "")
                new_item["_cot_rewritten"] = True
                results.append(new_item)
            
            return results
        except Exception as e:
            logger.error(f"批量生成推理过程失败: {e}")
            return batch
    
    def _get_field_value(self, item: Dict, field_names: List[str]) -> Any:
        """获取字段值"""
        for field in field_names:
            if field in item:
                return item[field]
        return None
