"""
生成增强智能体 (The Evolution Engine)
Module 2: 基于诊断报告生成高质量数据
"""
from typing import Dict, List, Any, Optional
from loguru import logger
import json
import re
from agents.base_agent import BaseAgent

# ==================== Prompt 模板 ====================

COT_REWRITING_PROMPT = """你是一个专业的教育内容创作专家。请将以下简单的问答对重写为包含详细推理过程的格式。

原始问题:
{question}

原始答案:
{answer}

要求:
1. 保持问题和答案不变
2. 在问题和答案之间插入详细的推理过程 (Chain of Thought)
3. 推理过程应包含:
   - 问题分析
   - 解题思路
   - 逐步推导
   - 得出结论
4. 推理过程要清晰、逻辑严密、易于理解

输出格式 (严格 JSON):
{{
  "question": "原始问题",
  "chain_of_thought": "详细的推理过程",
  "answer": "原始答案"
}}

请直接输出 JSON，不要包含其他文字。
"""

SYNTHETIC_GENERATION_PROMPT = """你是一个专业的数据生成专家。基于以下稀缺样本特征，生成 {n} 个高质量的训练样本。

稀缺特征描述:
{sparse_characteristics}

种子样本示例:
{seed_samples}

要求:
1. 生成的问题必须符合稀缺特征的描述
2. 必须包含详细的推理过程 (Chain of Thought)
3. 答案必须准确且可验证
4. 保持与种子样本相似的风格和难度
5. 确保多样性，避免重复

输出格式 (严格 JSON):
[
  {{
    "question": "生成的问题",
    "chain_of_thought": "详细的推理过程",
    "answer": "准确的答案"
  }}
]

请直接输出 JSON 数组，不要包含其他文字。
"""

TARGETED_GENERATION_PROMPT = """你是一个专业的{domain}领域内容创作专家。请生成 {n} 个关于"{topic}"的高质量问答样本。

主题要求:
{requirements}

难度级别: {difficulty}

要求:
1. 问题必须与主题紧密相关
2. 包含完整的推理过程
3. 答案准确无误
4. 适合用于模型训练

输出格式 (严格 JSON):
[
  {{
    "question": "...",
    "chain_of_thought": "...",
    "answer": "..."
  }}
]

请直接输出 JSON 数组，不要包含其他文字。
"""


# ==================== Agent 实现 ====================

class COTRewriterAgent(BaseAgent):
    """CoT 重写智能体"""
    
    def __init__(self, llm_client):
        super().__init__(name="COTRewriter", llm_client=llm_client)
    
    def run(self, input_data: Any, **kwargs) -> Dict[str, Any]:
        """
        将 Q->A 格式重写为 Q->Rationale->A
        
        Args:
            input_data: 单个样本或样本列表
            
        Returns:
            {
                "rewritten_samples": [...],
                "success_count": int,
                "output": rewritten_samples
            }
        """
        # 处理单个样本或批量样本
        if isinstance(input_data, dict):
            samples = [input_data]
        elif isinstance(input_data, list):
            samples = input_data
        else:
            return {"error": "输入数据格式错误"}
        
        logger.info(f"[{self.name}] 开始重写 {len(samples)} 个样本")
        
        rewritten_samples = []
        success_count = 0
        
        for i, sample in enumerate(samples, 1):
            # 检查是否已有推理过程
            if "chain_of_thought" in sample and sample["chain_of_thought"]:
                logger.debug(f"[{self.name}] 样本 {i} 已有推理过程，跳过")
                rewritten_samples.append(sample)
                success_count += 1
                continue
            
            # 重写样本
            rewritten = self._rewrite_single(sample)
            
            if rewritten:
                rewritten_samples.append(rewritten)
                success_count += 1
            else:
                rewritten_samples.append(sample)  # 保留原样本
        
        logger.info(f"[{self.name}] 重写完成，成功 {success_count}/{len(samples)}")
        
        # 记录执行
        self.log_execution(input_data, rewritten_samples, {
            "success_count": success_count,
            "total": len(samples)
        })
        
        return {
            "rewritten_samples": rewritten_samples,
            "success_count": success_count,
            "total": len(samples),
            "output": rewritten_samples
        }
    
    def _rewrite_single(self, sample: Dict) -> Optional[Dict]:
        """重写单个样本"""
        question = sample.get("question", "")
        answer = sample.get("answer", "")
        
        if not question or not answer:
            logger.warning(f"[{self.name}] 样本缺少问题或答案，跳过")
            return None
        
        try:
            # 调用 LLM 重写
            prompt = COT_REWRITING_PROMPT.format(
                question=question,
                answer=answer
            )
            
            response = self.llm_client.generate(
                prompt,
                temperature=0.7,
                max_tokens=500
            )
            
            # 解析响应
            rewritten = self._parse_json_response(response)
            
            if rewritten and "chain_of_thought" in rewritten:
                return rewritten
            else:
                logger.warning(f"[{self.name}] 重写结果格式错误")
                return None
                
        except Exception as e:
            logger.error(f"[{self.name}] 重写失败: {e}")
            return None
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """解析 JSON 响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return None


class SyntheticGeneratorAgent(BaseAgent):
    """合成生成智能体"""
    
    def __init__(self, llm_client):
        super().__init__(name="SyntheticGenerator", llm_client=llm_client)
    
    def run(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        基于稀缺特征生成新样本
        
        Args:
            input_data: {
                "sparse_characteristics": "稀缺特征描述",
                "seed_samples": [...],
                "target_count": int
            }
            
        Returns:
            {
                "generated_samples": [...],
                "output": generated_samples
            }
        """
        if not self.validate_input(input_data, dict):
            return {"error": "输入数据格式错误"}
        
        sparse_characteristics = input_data.get("sparse_characteristics", "")
        seed_samples = input_data.get("seed_samples", [])
        target_count = input_data.get("target_count", 10)
        
        if not sparse_characteristics:
            logger.error(f"[{self.name}] 缺少稀缺特征描述")
            return {"error": "缺少稀缺特征描述"}
        
        logger.info(f"[{self.name}] 开始生成 {target_count} 个样本")
        
        try:
            # 准备种子样本文本
            seed_text = self._format_seed_samples(seed_samples[:3])  # 最多使用3个种子
            
            # 调用 LLM 生成
            prompt = SYNTHETIC_GENERATION_PROMPT.format(
                n=target_count,
                sparse_characteristics=sparse_characteristics,
                seed_samples=seed_text
            )
            
            response = self.llm_client.generate(
                prompt,
                temperature=0.8,
                max_tokens=2000
            )
            
            # 解析响应
            generated_samples = self._parse_json_array_response(response)
            
            logger.info(f"[{self.name}] 生成完成，成功生成 {len(generated_samples)} 个样本")
            
            # 记录执行
            self.log_execution(input_data, generated_samples, {
                "target_count": target_count,
                "actual_count": len(generated_samples)
            })
            
            return {
                "generated_samples": generated_samples,
                "target_count": target_count,
                "actual_count": len(generated_samples),
                "output": generated_samples
            }
            
        except Exception as e:
            logger.error(f"[{self.name}] 生成失败: {e}")
            return {
                "generated_samples": [],
                "error": str(e),
                "output": []
            }
    
    def _format_seed_samples(self, seed_samples: List[Dict]) -> str:
        """格式化种子样本"""
        if not seed_samples:
            return "无种子样本"
        
        formatted = []
        for i, sample in enumerate(seed_samples, 1):
            formatted.append(f"示例 {i}:")
            formatted.append(f"问题: {sample.get('question', '')}")
            if "chain_of_thought" in sample:
                formatted.append(f"推理: {sample['chain_of_thought']}")
            formatted.append(f"答案: {sample.get('answer', '')}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _parse_json_array_response(self, response: str) -> List[Dict]:
        """解析 JSON 数组响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取 JSON 数组
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                logger.error(f"[{self.name}] 无法解析 JSON 数组响应")
                return []


class TargetedGeneratorAgent(BaseAgent):
    """定向生成智能体"""
    
    def __init__(self, llm_client):
        super().__init__(name="TargetedGenerator", llm_client=llm_client)
    
    def run(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        针对特定主题生成样本
        
        Args:
            input_data: {
                "domain": "领域",
                "topic": "主题",
                "requirements": "要求",
                "difficulty": "难度",
                "count": int
            }
            
        Returns:
            {
                "generated_samples": [...],
                "output": generated_samples
            }
        """
        if not self.validate_input(input_data, dict):
            return {"error": "输入数据格式错误"}
        
        domain = input_data.get("domain", "通用")
        topic = input_data.get("topic", "")
        requirements = input_data.get("requirements", "")
        difficulty = input_data.get("difficulty", "中等")
        count = input_data.get("count", 10)
        
        if not topic:
            logger.error(f"[{self.name}] 缺少主题")
            return {"error": "缺少主题"}
        
        logger.info(f"[{self.name}] 开始生成 {count} 个关于'{topic}'的样本")
        
        try:
            # 调用 LLM 生成
            prompt = TARGETED_GENERATION_PROMPT.format(
                domain=domain,
                n=count,
                topic=topic,
                requirements=requirements,
                difficulty=difficulty
            )
            
            response = self.llm_client.generate(
                prompt,
                temperature=0.8,
                max_tokens=2000
            )
            
            # 解析响应
            generated_samples = self._parse_json_array_response(response)
            
            logger.info(f"[{self.name}] 生成完成，成功生成 {len(generated_samples)} 个样本")
            
            # 记录执行
            self.log_execution(input_data, generated_samples, {
                "topic": topic,
                "count": len(generated_samples)
            })
            
            return {
                "generated_samples": generated_samples,
                "output": generated_samples
            }
            
        except Exception as e:
            logger.error(f"[{self.name}] 生成失败: {e}")
            return {
                "generated_samples": [],
                "error": str(e),
                "output": []
            }
    
    def _parse_json_array_response(self, response: str) -> List[Dict]:
        """解析 JSON 数组响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return []


# ==================== 生成增强引擎 ====================

class EvolutionEngine:
    """生成增强引擎"""
    
    def __init__(self, llm_client):
        """
        初始化生成增强引擎
        
        Args:
            llm_client: LLM 客户端
        """
        self.llm_client = llm_client
        self.cot_rewriter = COTRewriterAgent(llm_client)
        self.synthetic_generator = SyntheticGeneratorAgent(llm_client)
        self.targeted_generator = TargetedGeneratorAgent(llm_client)
        
        logger.info("生成增强引擎初始化完成")
    
    def evolve_dataset(
        self,
        original_dataset: List[Dict],
        diagnostic_report: Dict[str, Any],
        strategy: str = "auto"
    ) -> Dict[str, Any]:
        """
        进化数据集
        
        Args:
            original_dataset: 原始数据集
            diagnostic_report: 诊断报告
            strategy: 进化策略 (auto/rewrite/generate/both)
            
        Returns:
            {
                "evolved_dataset": [...],
                "stats": {...}
            }
        """
        logger.info(f"开始数据集进化，策略: {strategy}")
        
        evolved_dataset = []
        stats = {
            "original_count": len(original_dataset),
            "rewritten_count": 0,
            "generated_count": 0,
            "final_count": 0
        }
        
        # Step 1: CoT 重写
        if strategy in ["auto", "rewrite", "both"]:
            logger.info("执行 CoT 重写...")
            rewrite_result = self.cot_rewriter.run(original_dataset)
            evolved_dataset = rewrite_result["rewritten_samples"]
            stats["rewritten_count"] = rewrite_result["success_count"]
        else:
            evolved_dataset = original_dataset.copy()
        
        # Step 2: 合成生成
        if strategy in ["auto", "generate", "both"]:
            logger.info("执行合成生成...")
            
            # 从诊断报告中提取稀缺特征
            sparse_clusters = diagnostic_report.get("sparse_clusters", [])
            
            for cluster in sparse_clusters:
                # 生成样本
                generation_input = {
                    "sparse_characteristics": cluster.get("characteristics", ""),
                    "seed_samples": cluster.get("sample_questions", []),
                    "target_count": max(10, 50 - cluster.get("size", 0))  # 补充到至少50个
                }
                
                gen_result = self.synthetic_generator.run(generation_input)
                generated_samples = gen_result["generated_samples"]
                
                evolved_dataset.extend(generated_samples)
                stats["generated_count"] += len(generated_samples)
        
        stats["final_count"] = len(evolved_dataset)
        
        logger.info(f"数据集进化完成: {stats}")
        
        return {
            "evolved_dataset": evolved_dataset,
            "stats": stats
        }
    
    def generate_for_topic(
        self,
        domain: str,
        topic: str,
        count: int = 10,
        difficulty: str = "中等"
    ) -> List[Dict]:
        """
        为特定主题生成样本
        
        Args:
            domain: 领域
            topic: 主题
            count: 数量
            difficulty: 难度
            
        Returns:
            生成的样本列表
        """
        logger.info(f"为主题'{topic}'生成 {count} 个样本")
        
        generation_input = {
            "domain": domain,
            "topic": topic,
            "requirements": f"生成{count}个高质量的{difficulty}难度样本",
            "difficulty": difficulty,
            "count": count
        }
        
        result = self.targeted_generator.run(generation_input)
        return result["generated_samples"]
