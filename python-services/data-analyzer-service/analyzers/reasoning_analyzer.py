"""
推理深度分析器（重构版）
调用大模型进行深度推理分析，生成详细的 JSON 报告
"""
from typing import Dict, List, Any, Optional
from loguru import logger
import json
import re
from datetime import datetime
import random

class ReasoningAnalyzer:
    """推理深度分析器"""
    
    def __init__(self, llm_client=None):
        """
        初始化分析器
        
        Args:
            llm_client: LLM 客户端
        """
        self.llm_client = llm_client
        
        # 推理标记词
        self.reasoning_markers = [
            "因为", "所以", "首先", "然后", "接着", "最后", "因此",
            "步骤", "第一步", "第二步", "第三步",
            "therefore", "because", "first", "second", "step", "thus"
        ]
    
    def analyze(
        self, 
        dataset: List[Dict], 
        sample_size: int = 50,
        save_report: bool = True,
        report_path: str = None
    ) -> Dict[str, Any]:
        """
        分析数据集的推理深度
        
        Args:
            dataset: 数据集
            sample_size: 采样分析的样本数量
            save_report: 是否保存报告
            report_path: 报告保存路径
            
        Returns:
            推理分析报告
        """
        logger.info(f"开始推理深度分析，数据集大小: {len(dataset)}")
        
        # 1. 基础统计分析
        basic_stats = self._basic_reasoning_analysis(dataset)
        
        # 2. 采样进行深度分析
        sampled_items = self._sample_dataset(dataset, sample_size)
        
        # 3. 使用 LLM 进行深度分析
        if self.llm_client and self.llm_client.is_available():
            deep_analysis = self._llm_deep_analysis(sampled_items)
        else:
            logger.warning("LLM 不可用，跳过深度分析")
            deep_analysis = self._fallback_analysis(sampled_items)
        
        # 4. 综合评估
        overall_assessment = self._comprehensive_assessment(basic_stats, deep_analysis)
        
        # 5. 识别问题和建议
        issues, recommendations = self._identify_issues(basic_stats, deep_analysis, overall_assessment)
        
        # 6. 生成完整报告
        report = self._generate_report(
            dataset_size=len(dataset),
            sample_size=len(sampled_items),
            basic_stats=basic_stats,
            deep_analysis=deep_analysis,
            overall_assessment=overall_assessment,
            issues=issues,
            recommendations=recommendations
        )
        
        # 7. 保存报告
        if save_report:
            report_path = report_path or f"reasoning_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self._save_report(report, report_path)
        
        logger.info(f"推理深度分析完成，整体质量评分: {overall_assessment['quality_score']:.1f}/100")
        
        return report
    
    def _basic_reasoning_analysis(self, dataset: List[Dict]) -> Dict[str, Any]:
        """基础推理分析（规则基础）"""
        logger.info("执行基础推理分析...")
        
        total_samples = len(dataset)
        samples_with_reasoning = 0
        samples_with_explicit_cot = 0
        reasoning_lengths = []
        reasoning_steps_list = []
        
        for item in dataset:
            # 检查是否有显式推理字段
            reasoning = self._get_field_value(item, [
                "reasoning", "rationale", "explanation", 
                "steps", "cot", "chain_of_thought", "思考过程", "解题过程"
            ])
            
            has_reasoning = False
            reasoning_text = ""
            
            if reasoning:
                has_reasoning = True
                samples_with_explicit_cot += 1
                reasoning_text = str(reasoning)
            else:
                # 检查答案中是否包含推理过程
                answer = self._get_field_value(item, ["answer", "output", "response"])
                if answer:
                    answer_text = str(answer)
                    if self._has_implicit_reasoning(answer_text):
                        has_reasoning = True
                        reasoning_text = answer_text
            
            if has_reasoning:
                samples_with_reasoning += 1
                reasoning_lengths.append(len(reasoning_text))
                steps = self._count_reasoning_steps(reasoning_text)
                reasoning_steps_list.append(steps)
        
        # 计算统计指标
        avg_reasoning_length = sum(reasoning_lengths) / len(reasoning_lengths) if reasoning_lengths else 0
        avg_reasoning_steps = sum(reasoning_steps_list) / len(reasoning_steps_list) if reasoning_steps_list else 0
        
        cot_coverage = samples_with_reasoning / total_samples if total_samples > 0 else 0
        explicit_cot_coverage = samples_with_explicit_cot / total_samples if total_samples > 0 else 0
        
        return {
            "total_samples": total_samples,
            "samples_with_reasoning": samples_with_reasoning,
            "samples_with_explicit_cot": samples_with_explicit_cot,
            "samples_without_reasoning": total_samples - samples_with_reasoning,
            "cot_coverage": float(cot_coverage),
            "explicit_cot_coverage": float(explicit_cot_coverage),
            "avg_reasoning_length": float(avg_reasoning_length),
            "avg_reasoning_steps": float(avg_reasoning_steps),
            "reasoning_length_distribution": {
                "min": int(min(reasoning_lengths)) if reasoning_lengths else 0,
                "max": int(max(reasoning_lengths)) if reasoning_lengths else 0,
                "median": float(sorted(reasoning_lengths)[len(reasoning_lengths)//2]) if reasoning_lengths else 0
            }
        }
    
    def _sample_dataset(self, dataset: List[Dict], sample_size: int) -> List[Dict]:
        """采样数据集"""
        if len(dataset) <= sample_size:
            return dataset
        
        # 分层采样：有推理和无推理各一半
        with_reasoning = []
        without_reasoning = []
        
        for item in dataset:
            has_reasoning = any(k in item for k in [
                "reasoning", "rationale", "explanation", "steps", "cot"
            ])
            
            if has_reasoning:
                with_reasoning.append(item)
            else:
                without_reasoning.append(item)
        
        # 采样
        n_with = min(len(with_reasoning), sample_size // 2)
        n_without = min(len(without_reasoning), sample_size - n_with)
        
        sampled = (
            random.sample(with_reasoning, n_with) if with_reasoning else []
        ) + (
            random.sample(without_reasoning, n_without) if without_reasoning else []
        )
        
        random.shuffle(sampled)
        
        logger.info(f"采样 {len(sampled)} 个样本进行深度分析")
        return sampled
    
    def _llm_deep_analysis(self, samples: List[Dict]) -> Dict[str, Any]:
        """使用 LLM 进行深度推理分析"""
        logger.info("使用 LLM 进行深度推理分析...")
        
        # 分批分析
        batch_size = 10
        all_evaluations = []
        
        for i in range(0, len(samples), batch_size):
            batch = samples[i:i+batch_size]
            batch_eval = self._analyze_batch_with_llm(batch)
            all_evaluations.extend(batch_eval)
        
        # 汇总分析结果
        summary = self._summarize_llm_analysis(all_evaluations)
        
        return {
            "method": "llm_analysis",
            "samples_analyzed": len(samples),
            "individual_evaluations": all_evaluations[:10],  # 只保留前10个详细评估
            "summary": summary
        }
    
    def _analyze_batch_with_llm(self, batch: List[Dict]) -> List[Dict[str, Any]]:
        """使用 LLM 分析一批样本"""
        evaluations = []
        
        for item in batch:
            try:
                evaluation = self._evaluate_single_sample_with_llm(item)
                evaluations.append(evaluation)
            except Exception as e:
                logger.error(f"LLM 分析失败: {e}")
                evaluations.append(self._fallback_evaluation(item))
        
        return evaluations
    
    def _evaluate_single_sample_with_llm(self, item: Dict) -> Dict[str, Any]:
        """使用 LLM 评估单个样本的推理质量"""
        question = self._get_field_value(item, ["question", "input", "prompt", "query"])
        answer = self._get_field_value(item, ["answer", "output", "response"])
        reasoning = self._get_field_value(item, [
            "reasoning", "rationale", "explanation", "steps", "cot"
        ])
        
        # 构建评估提示词
        prompt = self._build_evaluation_prompt(question, answer, reasoning)
        
        # 调用 LLM
        response = self.llm_client.generate(prompt, temperature=0.3, max_tokens=500)
        
        # 解析 LLM 响应
        evaluation = self._parse_llm_evaluation(response)
        
        # 添加原始数据引用
        evaluation["question_preview"] = str(question)[:100] if question else ""
        evaluation["has_explicit_reasoning"] = reasoning is not None
        
        return evaluation
    
    def _build_evaluation_prompt(self, question: str, answer: str, reasoning: str = None) -> str:
        """构建 LLM 评估提示词"""
        if reasoning:
            prompt = f"""请评估以下问答对的推理质量。

问题: {question}

推理过程: {reasoning}

答案: {answer}

请从以下维度评估（1-10分）：
1. 逻辑连贯性：推理步骤是否逻辑清晰、前后连贯
2. 完整性：是否包含从问题到答案的完整推理链
3. 准确性：推理过程是否正确，结论是否准确
4. 清晰度：表达是否清晰易懂
5. 深度：推理是否深入，是否有足够的分析

请以JSON格式返回评估结果：
{{
  "logic_score": <1-10>,
  "completeness_score": <1-10>,
  "accuracy_score": <1-10>,
  "clarity_score": <1-10>,
  "depth_score": <1-10>,
  "overall_score": <1-10>,
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["不足1", "不足2"],
  "suggestions": ["改进建议1", "改进建议2"]
}}"""
        else:
            prompt = f"""请评估以下问答对，并判断是否需要补充推理过程。

问题: {question}

答案: {answer}

请评估：
1. 这个问答对是否需要推理过程？（简单事实性问题可能不需要）
2. 如果需要，缺少推理过程会对理解造成多大影响？
3. 推理过程应该包含哪些关键步骤？

请以JSON格式返回评估结果：
{{
  "needs_reasoning": <true/false>,
  "reasoning_necessity_score": <1-10>,
  "impact_of_missing_reasoning": "high/medium/low",
  "suggested_reasoning_steps": ["步骤1", "步骤2"],
  "question_complexity": "simple/medium/complex"
}}"""
        
        return prompt
    
    def _parse_llm_evaluation(self, response: str) -> Dict[str, Any]:
        """解析 LLM 评估响应"""
        try:
            # 尝试提取 JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                evaluation = json.loads(json_match.group())
                return evaluation
            else:
                logger.warning("无法从 LLM 响应中提取 JSON")
                return {"raw_response": response, "parse_error": True}
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            return {"raw_response": response, "parse_error": True}
    
    def _summarize_llm_analysis(self, evaluations: List[Dict]) -> Dict[str, Any]:
        """汇总 LLM 分析结果"""
        # 过滤掉解析失败的评估
        valid_evals = [e for e in evaluations if not e.get("parse_error")]
        
        if not valid_evals:
            return {
                "error": "所有评估都解析失败",
                "total_evaluated": len(evaluations)
            }
        
        # 区分有推理和无推理的样本
        with_reasoning = [e for e in valid_evals if e.get("has_explicit_reasoning")]
        without_reasoning = [e for e in valid_evals if not e.get("has_explicit_reasoning")]
        
        summary = {
            "total_evaluated": len(valid_evals),
            "with_reasoning_count": len(with_reasoning),
            "without_reasoning_count": len(without_reasoning)
        }
        
        # 汇总有推理的样本评分
        if with_reasoning:
            summary["reasoning_quality"] = {
                "avg_logic_score": self._avg_score(with_reasoning, "logic_score"),
                "avg_completeness_score": self._avg_score(with_reasoning, "completeness_score"),
                "avg_accuracy_score": self._avg_score(with_reasoning, "accuracy_score"),
                "avg_clarity_score": self._avg_score(with_reasoning, "clarity_score"),
                "avg_depth_score": self._avg_score(with_reasoning, "depth_score"),
                "avg_overall_score": self._avg_score(with_reasoning, "overall_score")
            }
            
            # 汇总优缺点
            all_strengths = []
            all_weaknesses = []
            for e in with_reasoning:
                all_strengths.extend(e.get("strengths", []))
                all_weaknesses.extend(e.get("weaknesses", []))
            
            summary["common_strengths"] = self._top_items(all_strengths, 5)
            summary["common_weaknesses"] = self._top_items(all_weaknesses, 5)
        
        # 汇总无推理的样本
        if without_reasoning:
            needs_reasoning_count = sum(1 for e in without_reasoning if e.get("needs_reasoning"))
            
            summary["missing_reasoning_analysis"] = {
                "needs_reasoning_count": needs_reasoning_count,
                "needs_reasoning_ratio": needs_reasoning_count / len(without_reasoning),
                "avg_necessity_score": self._avg_score(without_reasoning, "reasoning_necessity_score"),
                "high_impact_count": sum(1 for e in without_reasoning if e.get("impact_of_missing_reasoning") == "high")
            }
        
        return summary
    
    def _fallback_analysis(self, samples: List[Dict]) -> Dict[str, Any]:
        """降级分析方案（不使用 LLM）"""
        logger.info("使用降级分析方案...")
        
        evaluations = []
        for item in samples:
            evaluation = self._fallback_evaluation(item)
            evaluations.append(evaluation)
        
        return {
            "method": "rule_based_analysis",
            "samples_analyzed": len(samples),
            "summary": {
                "note": "LLM 不可用，使用规则基础分析",
                "avg_reasoning_quality": self._calculate_rule_based_quality(evaluations)
            }
        }
    
    def _fallback_evaluation(self, item: Dict) -> Dict[str, Any]:
        """降级评估（规则基础）"""
        reasoning = self._get_field_value(item, [
            "reasoning", "rationale", "explanation", "steps", "cot"
        ])
        
        if reasoning:
            reasoning_text = str(reasoning)
            quality = self._assess_reasoning_quality(reasoning_text)
            
            return {
                "has_explicit_reasoning": True,
                "reasoning_length": len(reasoning_text),
                "reasoning_steps": self._count_reasoning_steps(reasoning_text),
                "quality_score": quality * 10,
                "method": "rule_based"
            }
        else:
            return {
                "has_explicit_reasoning": False,
                "needs_reasoning": True,
                "method": "rule_based"
            }
    
    def _calculate_rule_based_quality(self, evaluations: List[Dict]) -> float:
        """计算规则基础的质量评分"""
        scores = [e.get("quality_score", 0) for e in evaluations if e.get("has_explicit_reasoning")]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _comprehensive_assessment(self, basic_stats: Dict, deep_analysis: Dict) -> Dict[str, Any]:
        """综合评估"""
        # 计算整体质量评分
        quality_score = self._calculate_quality_score(basic_stats, deep_analysis)
        
        # 评估等级
        if quality_score >= 80:
            grade = "优秀"
            level = "excellent"
        elif quality_score >= 60:
            grade = "良好"
            level = "good"
        elif quality_score >= 40:
            grade = "中等"
            level = "medium"
        else:
            grade = "较差"
            level = "poor"
        
        return {
            "quality_score": float(quality_score),
            "grade": grade,
            "level": level,
            "cot_coverage_assessment": self._assess_cot_coverage(basic_stats["cot_coverage"]),
            "reasoning_depth_assessment": self._assess_reasoning_depth(basic_stats["avg_reasoning_steps"]),
            "overall_recommendation": self._get_overall_recommendation(quality_score, basic_stats)
        }
    
    def _calculate_quality_score(self, basic_stats: Dict, deep_analysis: Dict) -> float:
        """计算质量评分"""
        score = 0.0
        
        # COT 覆盖率 (40%)
        cot_coverage = basic_stats["cot_coverage"]
        score += cot_coverage * 40
        
        # 推理步数 (20%)
        avg_steps = basic_stats["avg_reasoning_steps"]
        steps_score = min(avg_steps / 5, 1.0) * 20  # 5步为满分
        score += steps_score
        
        # LLM 深度分析评分 (40%)
        if deep_analysis.get("method") == "llm_analysis":
            summary = deep_analysis.get("summary", {})
            reasoning_quality = summary.get("reasoning_quality", {})
            avg_overall = reasoning_quality.get("avg_overall_score", 5)
            score += (avg_overall / 10) * 40
        else:
            # 降级方案：使用推理长度作为代理指标
            avg_length = basic_stats["avg_reasoning_length"]
            length_score = min(avg_length / 200, 1.0) * 40
            score += length_score
        
        return min(100.0, max(0.0, score))
    
    def _assess_cot_coverage(self, coverage: float) -> str:
        """评估 COT 覆盖率"""
        if coverage >= 0.8:
            return "覆盖率高，大部分样本包含推理过程"
        elif coverage >= 0.5:
            return "覆盖率中等，建议补充更多推理过程"
        elif coverage >= 0.2:
            return "覆盖率较低，强烈建议使用 COT 重写功能"
        else:
            return "覆盖率极低，数据集缺少推理过程，需要全面补充"
    
    def _assess_reasoning_depth(self, avg_steps: float) -> str:
        """评估推理深度"""
        if avg_steps >= 5:
            return "推理深度充分，步骤详细"
        elif avg_steps >= 3:
            return "推理深度适中"
        elif avg_steps >= 1:
            return "推理深度较浅，建议增加推理步骤"
        else:
            return "缺少推理步骤"
    
    def _get_overall_recommendation(self, quality_score: float, basic_stats: Dict) -> str:
        """获取总体建议"""
        if quality_score >= 80:
            return "数据集推理质量优秀，可以直接用于训练"
        elif quality_score >= 60:
            return "数据集推理质量良好，建议对部分样本进行优化"
        elif quality_score >= 40:
            return "数据集推理质量中等，建议使用 COT 重写功能全面提升"
        else:
            samples_without = basic_stats["samples_without_reasoning"]
            return f"数据集推理质量较差，{samples_without} 个样本缺少推理过程，强烈建议进行 COT 补全"
    
    def _identify_issues(
        self, 
        basic_stats: Dict, 
        deep_analysis: Dict, 
        overall_assessment: Dict
    ) -> tuple[List[str], List[str]]:
        """识别问题和生成建议"""
        issues = []
        recommendations = []
        
        # 检查 COT 覆盖率
        if basic_stats["cot_coverage"] < 0.5:
            issues.append(f"COT 覆盖率低: {basic_stats['cot_coverage']*100:.1f}%")
            recommendations.append("使用 COT 重写功能为缺少推理过程的样本补充推理链")
        
        # 检查推理深度
        if basic_stats["avg_reasoning_steps"] < 2:
            issues.append(f"平均推理步数不足: {basic_stats['avg_reasoning_steps']:.1f}")
            recommendations.append("增加推理步骤的详细程度，确保每个推理链至少包含3-5个步骤")
        
        # 检查 LLM 分析结果
        if deep_analysis.get("method") == "llm_analysis":
            summary = deep_analysis.get("summary", {})
            reasoning_quality = summary.get("reasoning_quality", {})
            
            if reasoning_quality.get("avg_logic_score", 10) < 6:
                issues.append("推理逻辑连贯性不足")
                recommendations.append("改进推理过程的逻辑性，确保步骤之间有清晰的因果关系")
            
            if reasoning_quality.get("avg_completeness_score", 10) < 6:
                issues.append("推理完整性不足")
                recommendations.append("补充完整的推理链，从问题分析到最终答案")
            
            # 常见弱点
            common_weaknesses = summary.get("common_weaknesses", [])
            if common_weaknesses:
                issues.append(f"常见问题: {', '.join(common_weaknesses[:3])}")
        
        # 整体质量建议
        if overall_assessment["quality_score"] < 60:
            recommendations.append("建议进行全面的推理质量提升，包括 COT 补全和人工审核")
        
        return issues, recommendations
    
    def _generate_report(
        self,
        dataset_size: int,
        sample_size: int,
        basic_stats: Dict,
        deep_analysis: Dict,
        overall_assessment: Dict,
        issues: List[str],
        recommendations: List[str]
    ) -> Dict[str, Any]:
        """生成完整报告"""
        report = {
            "report_metadata": {
                "report_type": "reasoning_depth_analysis",
                "generated_at": datetime.now().isoformat(),
                "analyzer_version": "2.0.0",
                "llm_enabled": deep_analysis.get("method") == "llm_analysis"
            },
            "dataset_summary": {
                "total_samples": dataset_size,
                "analyzed_samples": sample_size,
                "sampling_ratio": sample_size / dataset_size if dataset_size > 0 else 0
            },
            "basic_statistics": basic_stats,
            "deep_analysis": deep_analysis,
            "overall_assessment": overall_assessment,
            "issues": issues,
            "recommendations": recommendations,
            "summary": {
                "quality_score": overall_assessment["quality_score"],
                "grade": overall_assessment["grade"],
                "cot_coverage": basic_stats["cot_coverage"],
                "avg_reasoning_steps": basic_stats["avg_reasoning_steps"],
                "needs_improvement": overall_assessment["quality_score"] < 70
            }
        }
        
        return report
    
    def _save_report(self, report: Dict, path: str):
        """保存报告为 JSON"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"报告已保存至: {path}")
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
    
    # ==================== 辅助方法 ====================
    
    def _count_reasoning_steps(self, text: str) -> int:
        """计算推理步数"""
        steps = 0
        
        # 方法1: 计数步骤标记
        step_patterns = [
            r'第[一二三四五六七八九十\d]+步',
            r'步骤\s*\d+',
            r'step\s*\d+',
            r'\d+\.',
            r'\d+\)'
        ]
        
        for pattern in step_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            steps = max(steps, len(matches))
        
        # 方法2: 计数推理标记词
        marker_count = sum(1 for marker in self.reasoning_markers if marker in text.lower())
        steps = max(steps, marker_count // 2)
        
        # 方法3: 按句子分割
        sentences = re.split(r'[。！？\n]', text)
        meaningful_sentences = [s for s in sentences if len(s.strip()) > 10]
        steps = max(steps, len(meaningful_sentences))
        
        return max(1, steps)
    
    def _has_implicit_reasoning(self, text: str) -> bool:
        """检查是否包含隐式推理"""
        marker_count = sum(1 for marker in self.reasoning_markers if marker in text.lower())
        is_long = len(text) > 100
        sentences = re.split(r'[。！？\n]', text)
        has_multiple_sentences = len([s for s in sentences if len(s.strip()) > 10]) >= 2
        
        return marker_count >= 2 or (is_long and has_multiple_sentences)
    
    def _assess_reasoning_quality(self, text: str) -> float:
        """评估推理质量 (0-1)"""
        score = 0.0
        
        # 长度评分
        length_score = min(len(text) / 500, 1.0) * 0.3
        score += length_score
        
        # 结构评分
        steps = self._count_reasoning_steps(text)
        structure_score = min(steps / 5, 1.0) * 0.3
        score += structure_score
        
        # 逻辑连接词评分
        marker_count = sum(1 for marker in self.reasoning_markers if marker in text.lower())
        logic_score = min(marker_count / 4, 1.0) * 0.2
        score += logic_score
        
        # 完整性评分
        has_conclusion = any(word in text for word in ["因此", "所以", "综上", "总结", "答案是"])
        completeness_score = 0.2 if has_conclusion else 0.1
        score += completeness_score
        
        return min(score, 1.0)
    
    def _get_field_value(self, item: Dict, field_names: List[str]) -> Any:
        """获取字段值"""
        for field in field_names:
            if field in item:
                return item[field]
        return None
    
    def _avg_score(self, evaluations: List[Dict], score_key: str) -> float:
        """计算平均分"""
        scores = [e.get(score_key, 0) for e in evaluations if score_key in e]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _top_items(self, items: List[str], n: int = 5) -> List[Dict[str, Any]]:
        """统计最常见的项"""
        from collections import Counter
        counter = Counter(items)
        return [{"item": item, "count": count} for item, count in counter.most_common(n)]
