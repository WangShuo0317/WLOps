"""
RAG 校验智能体 (The RAG Verifier)
Module 3: 事实一致性校验的核心实现
"""
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger
import json
import re
from agents.base_agent import BaseAgent, AgentPipeline
from core.vector_store import KnowledgeBase

# ==================== Prompt 模板 ====================

FACT_EXTRACTION_PROMPT = """你是一个专业的事实提取专家。请从以下推理过程中提取所有原子化的事实宣称 (Claims)。

推理过程:
{chain_of_thought}

要求:
1. 每个 Claim 必须是独立的、可验证的陈述
2. 提取数学计算、逻辑推理、知识引用等关键事实
3. 忽略主观判断和修辞性表达
4. 每个 Claim 标注类型: calculation (计算), knowledge (知识), logic (逻辑推理)

输出格式 (严格 JSON):
{{
  "claims": [
    {{
      "claim_id": 1,
      "statement": "具体的事实陈述",
      "type": "calculation|knowledge|logic",
      "verifiable": true
    }}
  ]
}}

请直接输出 JSON，不要包含其他文字。
"""

VERIFICATION_PROMPT = """你是一个专业的事实校验专家。请执行自然语言推理 (NLI) 任务，判断 Claim 与 Evidence 的关系。

Claim (待验证的陈述):
{claim}

Evidence (检索到的证据):
{evidence}

判断标准:
- ENTAILMENT: Evidence 明确支持 Claim，事实一致 → 保留原答案
- CONTRADICTION: Evidence 与 Claim 矛盾，事实不一致 → 需要修正
- NEUTRAL: Evidence 与 Claim 无关或无法判断 → 需要人工审核

如果判断为 CONTRADICTION，请基于 Evidence 重写正确的答案或推理过程。

输出格式 (严格 JSON):
{{
  "relation": "ENTAILMENT|CONTRADICTION|NEUTRAL",
  "confidence": 0.95,
  "explanation": "判断理由",
  "corrected_statement": "修正后的陈述 (仅在 CONTRADICTION 时提供)"
}}

请直接输出 JSON，不要包含其他文字。
"""

SELF_CORRECTION_PROMPT = """基于以下检索到的证据，重写正确的答案。

原始问题:
{question}

原始推理过程:
{original_cot}

原始答案:
{original_answer}

检索到的证据:
{evidence}

矛盾的事实:
{contradictions}

要求:
1. 基于证据修正错误的推理过程
2. 保持推理的完整性和逻辑性
3. 给出正确的最终答案

输出格式 (严格 JSON):
{{
  "corrected_chain_of_thought": "修正后的推理过程",
  "corrected_answer": "修正后的答案",
  "correction_summary": "修正说明"
}}

请直接输出 JSON，不要包含其他文字。
"""


# ==================== Agent 实现 ====================

class FactExtractorAgent(BaseAgent):
    """事实提取智能体 - Step A"""
    
    def __init__(self, llm_client):
        super().__init__(name="FactExtractor", llm_client=llm_client)
    
    def run(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        从推理过程中提取事实宣称
        
        Args:
            input_data: {
                "question": "...",
                "chain_of_thought": "...",
                "answer": "..."
            }
            
        Returns:
            {
                "claims": [...],
                "output": input_data (传递给下一个 Agent)
            }
        """
        if not self.validate_input(input_data, dict):
            return {"error": "输入数据格式错误"}
        
        chain_of_thought = input_data.get("chain_of_thought", "")
        
        if not chain_of_thought:
            logger.warning(f"[{self.name}] 推理过程为空，跳过事实提取")
            return {
                "claims": [],
                "output": input_data
            }
        
        logger.info(f"[{self.name}] 开始提取事实宣称")
        
        try:
            # 调用 LLM 提取事实
            prompt = FACT_EXTRACTION_PROMPT.format(chain_of_thought=chain_of_thought)
            response = self.llm_client.generate(
                prompt,
                temperature=0.3,
                max_tokens=1000
            )
            
            # 解析 JSON 响应
            claims_data = self._parse_json_response(response)
            claims = claims_data.get("claims", [])
            
            logger.info(f"[{self.name}] 提取到 {len(claims)} 个事实宣称")
            
            # 记录执行
            self.log_execution(input_data, claims, {"claims_count": len(claims)})
            
            return {
                "claims": claims,
                "output": {**input_data, "extracted_claims": claims}
            }
            
        except Exception as e:
            logger.error(f"[{self.name}] 事实提取失败: {e}")
            return {
                "claims": [],
                "error": str(e),
                "output": input_data
            }
    
    def _parse_json_response(self, response: str) -> Dict:
        """解析 JSON 响应"""
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取 JSON 块
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                logger.error(f"[{self.name}] 无法解析 JSON 响应")
                return {"claims": []}


class RetrievalAgent(BaseAgent):
    """检索智能体 - Step B"""
    
    def __init__(self, knowledge_base: KnowledgeBase, top_k: int = 5):
        super().__init__(name="Retriever", embedding_model=knowledge_base.embedding_model)
        self.knowledge_base = knowledge_base
        self.top_k = top_k
    
    def run(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        检索相关证据
        
        Args:
            input_data: {
                "extracted_claims": [...],
                ...
            }
            
        Returns:
            {
                "evidence_map": {claim_id: [evidence_list]},
                "output": input_data (传递给下一个 Agent)
            }
        """
        if not self.validate_input(input_data, dict):
            return {"error": "输入数据格式错误"}
        
        claims = input_data.get("extracted_claims", [])
        
        if not claims:
            logger.warning(f"[{self.name}] 没有需要检索的事实宣称")
            return {
                "evidence_map": {},
                "output": input_data
            }
        
        logger.info(f"[{self.name}] 开始检索 {len(claims)} 个事实的证据")
        
        evidence_map = {}
        
        try:
            # 批量检索
            queries = [claim["statement"] for claim in claims]
            all_results = self.knowledge_base.batch_retrieve(queries, self.top_k)
            
            # 构建证据映射
            for claim, results in zip(claims, all_results):
                claim_id = claim["claim_id"]
                evidence_map[claim_id] = [
                    {
                        "document": r["document"],
                        "score": r["score"],
                        "metadata": r.get("metadata", {})
                    }
                    for r in results
                ]
            
            logger.info(f"[{self.name}] 检索完成，平均每个 Claim 检索到 {sum(len(v) for v in evidence_map.values()) / len(evidence_map):.1f} 条证据")
            
            # 记录执行
            self.log_execution(input_data, evidence_map, {"claims_count": len(claims)})
            
            return {
                "evidence_map": evidence_map,
                "output": {**input_data, "evidence_map": evidence_map}
            }
            
        except Exception as e:
            logger.error(f"[{self.name}] 检索失败: {e}")
            return {
                "evidence_map": {},
                "error": str(e),
                "output": input_data
            }


class VerificationAgent(BaseAgent):
    """校验与修正智能体 - Step C"""
    
    def __init__(self, llm_client, confidence_threshold: float = 0.8, enable_self_correction: bool = True):
        super().__init__(name="Verifier", llm_client=llm_client)
        self.confidence_threshold = confidence_threshold
        self.enable_self_correction = enable_self_correction
    
    def run(self, input_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        校验事实并执行自修正
        
        Args:
            input_data: {
                "question": "...",
                "chain_of_thought": "...",
                "answer": "...",
                "extracted_claims": [...],
                "evidence_map": {...}
            }
            
        Returns:
            {
                "decision": "PASS|SELF_CORRECT|REJECT",
                "verification_results": [...],
                "corrected_data": {...} (仅在 SELF_CORRECT 时),
                "output": final_data
            }
        """
        if not self.validate_input(input_data, dict):
            return {"error": "输入数据格式错误"}
        
        claims = input_data.get("extracted_claims", [])
        evidence_map = input_data.get("evidence_map", {})
        
        if not claims:
            logger.info(f"[{self.name}] 没有事实宣称，直接通过")
            return {
                "decision": "PASS",
                "verification_results": [],
                "output": input_data
            }
        
        logger.info(f"[{self.name}] 开始校验 {len(claims)} 个事实宣称")
        
        verification_results = []
        contradictions = []
        
        try:
            # 逐个校验 Claim
            for claim in claims:
                claim_id = claim["claim_id"]
                claim_statement = claim["statement"]
                evidence_list = evidence_map.get(claim_id, [])
                
                if not evidence_list:
                    logger.warning(f"[{self.name}] Claim {claim_id} 没有检索到证据")
                    verification_results.append({
                        "claim_id": claim_id,
                        "relation": "NEUTRAL",
                        "confidence": 0.0,
                        "explanation": "未检索到相关证据"
                    })
                    continue
                
                # 使用最相关的证据进行校验
                top_evidence = evidence_list[0]["document"]
                
                # 调用 LLM 进行 NLI
                verification = self._verify_claim(claim_statement, top_evidence)
                verification["claim_id"] = claim_id
                verification_results.append(verification)
                
                # 收集矛盾的事实
                if verification["relation"] == "CONTRADICTION" and verification["confidence"] > self.confidence_threshold:
                    contradictions.append({
                        "claim": claim_statement,
                        "evidence": top_evidence,
                        "corrected_statement": verification.get("corrected_statement", "")
                    })
            
            # 决策逻辑
            decision, corrected_data = self._make_decision(
                input_data,
                verification_results,
                contradictions
            )
            
            logger.info(f"[{self.name}] 校验完成，决策: {decision}")
            
            # 记录执行
            self.log_execution(input_data, verification_results, {
                "decision": decision,
                "contradictions_count": len(contradictions)
            })
            
            # 构建输出
            output_data = corrected_data if decision == "SELF_CORRECT" else input_data
            
            return {
                "decision": decision,
                "verification_results": verification_results,
                "contradictions": contradictions,
                "corrected_data": corrected_data,
                "output": output_data
            }
            
        except Exception as e:
            logger.error(f"[{self.name}] 校验失败: {e}")
            return {
                "decision": "REJECT",
                "error": str(e),
                "output": input_data
            }
    
    def _verify_claim(self, claim: str, evidence: str) -> Dict[str, Any]:
        """使用 LLM 校验单个 Claim"""
        try:
            prompt = VERIFICATION_PROMPT.format(claim=claim, evidence=evidence)
            response = self.llm_client.generate(
                prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            # 解析响应
            result = self._parse_json_response(response)
            return result
            
        except Exception as e:
            logger.error(f"[{self.name}] Claim 校验失败: {e}")
            return {
                "relation": "NEUTRAL",
                "confidence": 0.0,
                "explanation": f"校验失败: {str(e)}"
            }
    
    def _make_decision(
        self,
        input_data: Dict,
        verification_results: List[Dict],
        contradictions: List[Dict]
    ) -> Tuple[str, Optional[Dict]]:
        """
        基于校验结果做出决策
        
        Returns:
            (decision, corrected_data)
        """
        # 统计各类关系
        entailment_count = sum(1 for v in verification_results if v["relation"] == "ENTAILMENT" and v["confidence"] > self.confidence_threshold)
        contradiction_count = len(contradictions)
        neutral_count = sum(1 for v in verification_results if v["relation"] == "NEUTRAL")
        
        total_claims = len(verification_results)
        
        logger.debug(f"[{self.name}] 校验统计: ENTAILMENT={entailment_count}, CONTRADICTION={contradiction_count}, NEUTRAL={neutral_count}")
        
        # 决策规则
        if contradiction_count == 0 and entailment_count >= total_claims * 0.8:
            # 大部分事实一致 → PASS
            return "PASS", None
        
        elif contradiction_count > 0 and contradiction_count <= total_claims * 0.3 and self.enable_self_correction:
            # 少量矛盾且启用自修正 → SELF_CORRECT
            corrected_data = self._self_correct(input_data, contradictions)
            return "SELF_CORRECT", corrected_data
        
        else:
            # 矛盾过多或无法修正 → REJECT
            return "REJECT", None
    
    def _self_correct(self, input_data: Dict, contradictions: List[Dict]) -> Dict:
        """执行自修正"""
        logger.info(f"[{self.name}] 执行自修正，修正 {len(contradictions)} 个矛盾")
        
        try:
            # 构建证据文本
            evidence_text = "\n\n".join([
                f"矛盾 {i+1}:\n原陈述: {c['claim']}\n证据: {c['evidence']}\n建议修正: {c['corrected_statement']}"
                for i, c in enumerate(contradictions)
            ])
            
            # 调用 LLM 重写
            prompt = SELF_CORRECTION_PROMPT.format(
                question=input_data.get("question", ""),
                original_cot=input_data.get("chain_of_thought", ""),
                original_answer=input_data.get("answer", ""),
                evidence=evidence_text,
                contradictions=json.dumps(contradictions, ensure_ascii=False, indent=2)
            )
            
            response = self.llm_client.generate(
                prompt,
                temperature=0.5,
                max_tokens=1000
            )
            
            # 解析响应
            corrected = self._parse_json_response(response)
            
            # 构建修正后的数据
            corrected_data = input_data.copy()
            corrected_data["chain_of_thought"] = corrected.get("corrected_chain_of_thought", input_data.get("chain_of_thought"))
            corrected_data["answer"] = corrected.get("corrected_answer", input_data.get("answer"))
            corrected_data["_self_corrected"] = True
            corrected_data["_correction_summary"] = corrected.get("correction_summary", "")
            
            logger.info(f"[{self.name}] 自修正完成")
            return corrected_data
            
        except Exception as e:
            logger.error(f"[{self.name}] 自修正失败: {e}")
            return input_data
    
    def _parse_json_response(self, response: str) -> Dict:
        """解析 JSON 响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {}


# ==================== RAG 校验流水线 ====================

class RAGVerifierPipeline(AgentPipeline):
    """RAG 校验流水线"""
    
    def __init__(
        self,
        llm_client,
        knowledge_base: KnowledgeBase,
        confidence_threshold: float = 0.8,
        enable_self_correction: bool = True,
        retrieval_top_k: int = 5
    ):
        """
        初始化 RAG 校验流水线
        
        Args:
            llm_client: LLM 客户端
            knowledge_base: 知识库
            confidence_threshold: 置信度阈值
            enable_self_correction: 是否启用自修正
            retrieval_top_k: 检索 Top-K
        """
        super().__init__(name="RAGVerifier")
        
        # 创建三个 Agent
        fact_extractor = FactExtractorAgent(llm_client)
        retriever = RetrievalAgent(knowledge_base, top_k=retrieval_top_k)
        verifier = VerificationAgent(llm_client, confidence_threshold, enable_self_correction)
        
        # 添加到流水线
        self.add_agent(fact_extractor)
        self.add_agent(retriever)
        self.add_agent(verifier)
        
        logger.info("RAG 校验流水线初始化完成")
    
    def verify_batch(self, samples: List[Dict]) -> Dict[str, Any]:
        """
        批量校验样本
        
        Args:
            samples: 样本列表，每个样本包含 {question, chain_of_thought, answer}
            
        Returns:
            {
                "passed": [...],
                "corrected": [...],
                "rejected": [...],
                "stats": {...}
            }
        """
        logger.info(f"[{self.name}] 开始批量校验 {len(samples)} 个样本")
        
        passed = []
        corrected = []
        rejected = []
        
        for i, sample in enumerate(samples, 1):
            logger.info(f"[{self.name}] 校验样本 {i}/{len(samples)}")
            
            try:
                result = self.run(sample)
                
                decision = result["results"]["Verifier"]["decision"]
                output_data = result["final_output"]
                
                if decision == "PASS":
                    passed.append(output_data)
                elif decision == "SELF_CORRECT":
                    corrected.append(output_data)
                else:  # REJECT
                    rejected.append(sample)
                    
            except Exception as e:
                logger.error(f"[{self.name}] 样本 {i} 校验失败: {e}")
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
        
        logger.info(f"[{self.name}] 批量校验完成: {stats}")
        
        return {
            "passed": passed,
            "corrected": corrected,
            "rejected": rejected,
            "stats": stats
        }
