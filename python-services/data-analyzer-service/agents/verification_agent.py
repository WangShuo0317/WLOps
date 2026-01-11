"""
校验智能体
负责使用 RAG 校验优化和生成的样本
"""
from typing import Dict, List, Any
from loguru import logger
import json

from config import config


class VerificationAgent:
    """校验智能体"""
    
    def __init__(self, llm_client, knowledge_base_manager):
        self.llm_client = llm_client
        self.knowledge_base = knowledge_base_manager
    
    def verify_batch(self, samples: List[Dict]) -> Dict[str, Any]:
        """
        批量校验样本
        
        使用 RAG 从知识库检索相关信息，校验样本的事实性
        """
        logger.info(f"  校验 {len(samples)} 个样本...")
        
        passed = []
        corrected = []
        rejected = []
        
        for sample in samples:
            try:
                result = self._verify_single(sample)
                
                if result["status"] == "passed":
                    passed.append(sample)
                elif result["status"] == "corrected":
                    corrected.append(result["corrected_sample"])
                else:
                    rejected.append(sample)
                    
            except Exception as e:
                logger.warning(f"  校验失败: {e}")
                # 默认拒绝
                rejected.append(sample)
        
        stats = {
            "total": len(samples),
            "passed": len(passed),
            "corrected": len(corrected),
            "rejected": len(rejected),
            "pass_rate": len(passed) / len(samples) if samples else 0,
            "correction_rate": len(corrected) / len(samples) if samples else 0,
            "rejection_rate": len(rejected) / len(samples) if samples else 0
        }
        
        return {
            "verified_samples": passed + corrected,
            "passed": passed,
            "corrected": corrected,
            "rejected": rejected,
            "stats": stats
        }
    
    def _verify_single(self, sample: Dict) -> Dict[str, Any]:
        """
        校验单个样本
        
        Returns:
            {
                "status": "passed" | "corrected" | "rejected",
                "corrected_sample": Dict (if corrected)
            }
        """
        question = sample.get("question", sample.get("instruction", ""))
        answer = sample.get("answer", sample.get("output", ""))
        reasoning = sample.get("reasoning", "")
        
        # 从知识库检索相关信息
        retrieved_docs = self.knowledge_base.search(
            query=question,
            top_k=config.RAG_RETRIEVAL_TOP_K
        )
        
        if not retrieved_docs:
            # 没有相关知识，无法校验，默认通过
            return {"status": "passed"}
        
        # 构建校验提示
        context = "\n".join([doc["text"] for doc in retrieved_docs])
        
        prompt = f"""请根据以下知识库内容，校验这个问答对的准确性。

知识库内容:
{context}

问答对:
问题: {question}
推理: {reasoning}
答案: {answer}

请判断：
1. 答案是否与知识库内容一致？
2. 推理过程是否合理？
3. 如果有错误，应该如何修正？

请返回 JSON 格式：
{{
    "is_correct": true/false,
    "confidence": 0.0-1.0,
    "issues": ["问题1", "问题2"],
    "corrected_answer": "修正后的答案（如果需要修正）",
    "corrected_reasoning": "修正后的推理（如果需要修正）"
}}

只返回 JSON，不要其他内容。"""
        
        response = self.llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        
        try:
            verification = json.loads(response)
            
            is_correct = verification.get("is_correct", False)
            confidence = verification.get("confidence", 0.0)
            
            if is_correct and confidence >= config.RAG_CONFIDENCE_THRESHOLD:
                # 通过
                return {"status": "passed"}
            
            elif config.RAG_ENABLE_SELF_CORRECTION and verification.get("corrected_answer"):
                # 自动修正
                corrected_sample = {
                    **sample,
                    "answer": verification.get("corrected_answer", answer),
                    "reasoning": verification.get("corrected_reasoning", reasoning),
                    "_corrected": True
                }
                return {
                    "status": "corrected",
                    "corrected_sample": corrected_sample
                }
            
            else:
                # 拒绝
                return {"status": "rejected"}
                
        except Exception as e:
            logger.warning(f"  校验解析失败: {e}")
            # 解析失败，默认通过
            return {"status": "passed"}
