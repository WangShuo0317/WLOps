"""
自进化数据优化智能体系统集成
完整的 Multi-Agent 系统实现
"""
from typing import Dict, List, Any, Optional
from loguru import logger
from pathlib import Path
import json
from datetime import datetime

from config import config
from llm_client import LLMClient
from core.vector_store import VectorStore, KnowledgeBase
from agents.rag_verifier import RAGVerifierPipeline
from agents.evolution_engine import EvolutionEngine
from analyzers.semantic_distribution_analyzer import SemanticDistributionAnalyzer
from analyzers.reasoning_analyzer import ReasoningAnalyzer
from enhancers.pii_cleaner import PIICleaner

class SelfEvolvingDataOptimizer:
    """自进化数据优化智能体系统"""
    
    def __init__(
        self,
        llm_client: LLMClient,
        embedding_model,
        knowledge_base_path: str = None
    ):
        """
        初始化系统
        
        Args:
            llm_client: LLM 客户端
            embedding_model: Embedding 模型
            knowledge_base_path: 知识库路径
        """
        logger.info("初始化自进化数据优化智能体系统...")
        
        self.llm_client = llm_client
        self.embedding_model = embedding_model
        
        # 初始化向量数据库
        vector_store = VectorStore(
            store_type=config.VECTOR_DB_TYPE,
            persist_path=knowledge_base_path or config.VECTOR_DB_PATH
        )
        
        # 初始化知识库
        self.knowledge_base = KnowledgeBase(vector_store, embedding_model)
        
        # 初始化各模块
        self._init_modules()
        
        # 迭代历史
        self.iteration_history = []
        
        logger.info("系统初始化完成")
    
    def _init_modules(self):
        """初始化各个模块"""
        # Module 1: 诊断智能体
        self.semantic_analyzer = SemanticDistributionAnalyzer(
            embedding_model_name=config.EMBEDDING_MODEL,
            min_cluster_size=config.MIN_CLUSTER_SIZE,
            min_samples=config.MIN_SAMPLES
        )
        
        self.reasoning_analyzer = ReasoningAnalyzer(self.llm_client)
        
        # Module 2: 生成增强智能体
        self.evolution_engine = EvolutionEngine(self.llm_client)
        
        # Module 3: RAG 校验智能体
        self.rag_verifier = RAGVerifierPipeline(
            llm_client=self.llm_client,
            knowledge_base=self.knowledge_base,
            confidence_threshold=config.RAG_CONFIDENCE_THRESHOLD,
            enable_self_correction=config.RAG_ENABLE_SELF_CORRECTION,
            retrieval_top_k=config.RAG_RETRIEVAL_TOP_K
        )
        
        # Module 4: 隐私清洗智能体
        self.pii_cleaner = PIICleaner()
        
        logger.info("所有模块初始化完成")
    
    def run_iteration(
        self,
        dataset: List[Dict],
        iteration_id: int = 0,
        save_reports: bool = True
    ) -> Dict[str, Any]:
        """
        执行一轮完整的数据优化迭代
        
        Args:
            dataset: 输入数据集（原始数据）
            iteration_id: 迭代编号
            save_reports: 是否保存报告
            
        Returns:
            纯净的高质量数据集和统计信息
        """
        logger.info(f"=" * 60)
        logger.info(f"开始第 {iteration_id} 轮迭代")
        logger.info(f"=" * 60)
        
        iteration_start = datetime.now()
        
        # ==================== Module 1: 诊断 ====================
        logger.info("\n[Module 1] 执行数据诊断...")
        
        # 1.1 意图匹配分析
        logger.info("  1.1 意图匹配分析...")
        # TODO: 如果需要意图匹配，可以在这里添加
        
        # 1.2 语义分布分析 - 识别稀缺样本
        logger.info("  1.2 语义分布分析...")
        semantic_report = self.semantic_analyzer.analyze(
            dataset,
            save_report=save_reports,
            report_path=f"reports/iteration_{iteration_id}_semantic.json"
        )
        
        # 1.3 推理质量分析 - 识别低质量样本
        logger.info("  1.3 推理质量分析...")
        reasoning_report = self.reasoning_analyzer.analyze(
            dataset,
            sample_size=min(50, len(dataset)),
            save_report=save_reports,
            report_path=f"reports/iteration_{iteration_id}_reasoning.json"
        )
        
        # 构建诊断报告
        diagnostic_report = {
            "iteration": iteration_id,
            "dataset_size": len(dataset),
            "semantic_analysis": semantic_report,
            "reasoning_analysis": reasoning_report,
            "sparse_clusters": self._extract_sparse_clusters(semantic_report),
            "low_quality_samples": self._extract_low_quality_samples(dataset, reasoning_report)
        }
        
        logger.info(f"  诊断完成:")
        logger.info(f"    - 稀缺聚类: {len(diagnostic_report['sparse_clusters'])} 个")
        logger.info(f"    - 低质量样本: {len(diagnostic_report['low_quality_samples'])} 个")
        
        # ==================== Module 2: 生成增强 ====================
        logger.info("\n[Module 2] 执行生成增强...")
        
        # 2.1 优化原始数据中的低质量样本
        logger.info("  2.1 优化低质量样本（COT 重写）...")
        optimized_samples, optimization_stats = self._optimize_low_quality_samples(
            dataset,
            diagnostic_report["low_quality_samples"]
        )
        
        # 2.2 针对稀缺特征生成新样本
        logger.info("  2.2 生成稀缺样本...")
        generated_samples, generation_stats = self._generate_sparse_samples(
            diagnostic_report["sparse_clusters"]
        )
        
        # 2.3 合并：优化后的数据 + 新生成的数据
        enhanced_dataset = optimized_samples + generated_samples
        
        logger.info(f"  生成增强完成:")
        logger.info(f"    - 优化样本: {optimization_stats['optimized_count']}")
        logger.info(f"    - 生成样本: {generation_stats['generated_count']}")
        logger.info(f"    - 总计: {len(enhanced_dataset)}")
        
        # ==================== Module 3: RAG 校验 ====================
        logger.info("\n[Module 3] 执行 RAG 校验...")
        
        # 3.1 识别需要校验的样本（所有优化和生成的样本）
        samples_to_verify = []
        
        # 标记优化的样本
        for sample in optimized_samples:
            if sample.get("_optimized"):
                samples_to_verify.append(sample)
        
        # 标记生成的样本
        for sample in generated_samples:
            sample["_generated"] = True
            samples_to_verify.append(sample)
        
        logger.info(f"  需要校验的样本: {len(samples_to_verify)}")
        
        # 3.2 执行 RAG 校验
        if samples_to_verify:
            verification_result = self.rag_verifier.verify_batch(samples_to_verify)
            
            # 3.3 构建最终数据集：未优化的原始数据 + 校验通过的数据
            unoptimized_original = [
                s for s in dataset 
                if not any(low_q["index"] == dataset.index(s) for low_q in diagnostic_report["low_quality_samples"])
            ]
            
            verified_dataset = (
                unoptimized_original + 
                verification_result["passed"] + 
                verification_result["corrected"]
            )
            
            verification_stats = verification_result["stats"]
            logger.info(f"  RAG 校验完成:")
            logger.info(f"    - 通过: {verification_stats['passed']} ({verification_stats['pass_rate']:.1%})")
            logger.info(f"    - 修正: {verification_stats['corrected']} ({verification_stats['correction_rate']:.1%})")
            logger.info(f"    - 拒绝: {verification_stats['rejected']} ({verification_stats['rejection_rate']:.1%})")
        else:
            verified_dataset = enhanced_dataset
            verification_stats = {"total": 0, "passed": 0, "corrected": 0, "rejected": 0}
        
        # ==================== Module 4: 隐私清洗 ====================
        logger.info("\n[Module 4] 执行隐私清洗...")
        
        cleaned_dataset, pii_cleaned_count = self.pii_cleaner.clean_dataset(verified_dataset)
        
        logger.info(f"  隐私清洗完成: 清洗了 {pii_cleaned_count} 个样本")
        
        # ==================== 迭代总结 ====================
        iteration_end = datetime.now()
        iteration_duration = (iteration_end - iteration_start).total_seconds()
        
        iteration_summary = {
            "iteration_id": iteration_id,
            "timestamp": iteration_start.isoformat(),
            "duration_seconds": iteration_duration,
            "input_size": len(dataset),
            "output_size": len(cleaned_dataset),
            "diagnostic_report": diagnostic_report,
            "optimization_stats": optimization_stats,
            "generation_stats": generation_stats,
            "verification_stats": verification_stats,
            "pii_cleaned_count": pii_cleaned_count,
            "quality_improvement": self._calculate_quality_improvement(
                diagnostic_report,
                optimization_stats,
                generation_stats
            )
        }
        
        # 保存迭代历史
        self.iteration_history.append(iteration_summary)
        
        if save_reports:
            self._save_iteration_summary(iteration_summary)
        
        logger.info(f"\n第 {iteration_id} 轮迭代完成!")
        logger.info(f"  输入数据集: {len(dataset)} 样本")
        logger.info(f"  输出数据集: {len(cleaned_dataset)} 样本（纯净高质量）")
        logger.info(f"  优化样本: {optimization_stats['optimized_count']}")
        logger.info(f"  生成样本: {generation_stats['generated_count']}")
        logger.info(f"  质量提升: {iteration_summary['quality_improvement']:.1f}%")
        logger.info(f"  耗时: {iteration_duration:.1f} 秒")
        
        return {
            "optimized_dataset": cleaned_dataset,
            "iteration_summary": iteration_summary
        }
    
    def run_multi_iterations(
        self,
        initial_dataset: List[Dict],
        max_iterations: int = 3,
        convergence_threshold: float = 0.05
    ) -> Dict[str, Any]:
        """
        执行多轮迭代直到收敛
        
        Args:
            initial_dataset: 初始数据集
            max_iterations: 最大迭代次数
            convergence_threshold: 收敛阈值
            
        Returns:
            最终数据集和迭代历史
        """
        logger.info(f"开始多轮迭代优化，最大迭代次数: {max_iterations}")
        
        current_dataset = initial_dataset
        
        for iteration in range(max_iterations):
            result = self.run_iteration(
                dataset=current_dataset,
                iteration_id=iteration,
                save_reports=True
            )
            
            current_dataset = result["optimized_dataset"]
            quality_improvement = result["iteration_summary"]["quality_improvement"]
            
            # 检查收敛
            if quality_improvement < convergence_threshold:
                logger.info(f"质量提升 {quality_improvement:.2%} < 阈值 {convergence_threshold:.2%}，停止迭代")
                break
        
        logger.info(f"多轮迭代完成，共执行 {len(self.iteration_history)} 轮")
        
        return {
            "final_dataset": current_dataset,
            "iteration_history": self.iteration_history,
            "total_iterations": len(self.iteration_history)
        }
    
    def load_knowledge_base(self, knowledge_texts: List[str], metadata: List[Dict] = None):
        """
        加载外部知识库
        
        Args:
            knowledge_texts: 知识文本列表
            metadata: 元数据列表
        """
        logger.info(f"加载知识库，共 {len(knowledge_texts)} 条知识")
        self.knowledge_base.add_knowledge(knowledge_texts, metadata)
        logger.info("知识库加载完成")
    
    def save_knowledge_base(self, name: str = "default"):
        """保存知识库"""
        self.knowledge_base.save(name)
    
    def load_saved_knowledge_base(self, name: str = "default"):
        """加载已保存的知识库"""
        self.knowledge_base.load(name)
    
    def _extract_sparse_clusters(self, semantic_report: Dict) -> List[Dict]:
        """从语义报告中提取稀缺聚类"""
        sparse_clusters = []
        
        cluster_analysis = semantic_report.get("cluster_analysis", [])
        
        for cluster in cluster_analysis:
            if cluster["cluster_id"] == -1:  # 跳过噪声
                continue
            
            # 判断是否稀缺（样本数 < 20）
            if cluster["size"] < 20:
                sparse_clusters.append({
                    "cluster_id": cluster["cluster_id"],
                    "size": cluster["size"],
                    "characteristics": ", ".join(cluster["characteristics"]["keywords"]),
                    "sample_questions": [
                        {"question": q, "answer": ""} 
                        for q in cluster["sample_questions"][:3]
                    ]
                })
        
        return sparse_clusters
    
    def _extract_low_quality_samples(self, dataset: List[Dict], reasoning_report: Dict) -> List[Dict]:
        """从推理报告中提取低质量样本"""
        low_quality_samples = []
        
        basic_stats = reasoning_report.get("basic_statistics", {})
        samples_without_cot = basic_stats.get("samples_without_cot", 0)
        
        # 识别缺少推理过程的样本
        for idx, sample in enumerate(dataset):
            has_reasoning = any(k in sample for k in [
                "reasoning", "rationale", "explanation", "steps", "cot", "chain_of_thought"
            ])
            
            if not has_reasoning:
                low_quality_samples.append({
                    "index": idx,
                    "sample": sample,
                    "issue": "missing_cot"
                })
        
        logger.info(f"  识别到 {len(low_quality_samples)} 个低质量样本（缺少推理过程）")
        
        return low_quality_samples
    
    def _optimize_low_quality_samples(
        self, 
        dataset: List[Dict], 
        low_quality_samples: List[Dict]
    ) -> tuple[List[Dict], Dict]:
        """优化低质量样本"""
        optimized_samples = []
        optimized_count = 0
        
        # 保留高质量的原始样本
        high_quality_indices = set(range(len(dataset))) - set(lq["index"] for lq in low_quality_samples)
        for idx in high_quality_indices:
            optimized_samples.append(dataset[idx])
        
        # 优化低质量样本
        if low_quality_samples:
            samples_to_optimize = [lq["sample"] for lq in low_quality_samples]
            
            # 使用 COT 重写器
            rewrite_result = self.evolution_engine.cot_rewriter.run(samples_to_optimize)
            
            # 标记为已优化
            for sample in rewrite_result["rewritten_samples"]:
                sample["_optimized"] = True
                optimized_samples.append(sample)
            
            optimized_count = rewrite_result["success_count"]
        
        stats = {
            "total_original": len(dataset),
            "low_quality_count": len(low_quality_samples),
            "optimized_count": optimized_count,
            "high_quality_kept": len(high_quality_indices)
        }
        
        return optimized_samples, stats
    
    def _generate_sparse_samples(self, sparse_clusters: List[Dict]) -> tuple[List[Dict], Dict]:
        """生成稀缺样本"""
        generated_samples = []
        generated_count = 0
        
        for cluster in sparse_clusters:
            # 计算需要生成的数量（补充到至少 50 个）
            target_count = max(10, 50 - cluster["size"])
            
            generation_input = {
                "sparse_characteristics": cluster["characteristics"],
                "seed_samples": cluster["sample_questions"],
                "target_count": target_count
            }
            
            gen_result = self.evolution_engine.synthetic_generator.run(generation_input)
            new_samples = gen_result["generated_samples"]
            
            generated_samples.extend(new_samples)
            generated_count += len(new_samples)
        
        stats = {
            "sparse_clusters_count": len(sparse_clusters),
            "generated_count": generated_count
        }
        
        return generated_samples, stats
    
    def _extract_quality_issues(self, reasoning_report: Dict) -> List[str]:
        """从推理报告中提取质量问题"""
        return reasoning_report.get("issues", [])
    
    def _calculate_quality_improvement(
        self, 
        diagnostic_report: Dict, 
        optimization_stats: Dict,
        generation_stats: Dict
    ) -> float:
        """计算质量提升百分比"""
        original_size = diagnostic_report["dataset_size"]
        
        if original_size == 0:
            return 0.0
        
        # 优化样本的贡献
        optimization_boost = (optimization_stats["optimized_count"] / original_size) * 30
        
        # 新生成样本的贡献
        generation_boost = (generation_stats["generated_count"] / original_size) * 20
        
        # 基于推理质量的提升
        reasoning_quality = diagnostic_report["reasoning_analysis"].get("overall_assessment", {}).get("quality_score", 50)
        quality_boost = (reasoning_quality / 100) * 10
        
        return min(100.0, optimization_boost + generation_boost + quality_boost)
    
    def _save_iteration_summary(self, summary: Dict):
        """保存迭代总结"""
        Path("reports").mkdir(exist_ok=True)
        
        filename = f"reports/iteration_{summary['iteration_id']}_summary.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"迭代总结已保存: {filename}")
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        return {
            "total_iterations": len(self.iteration_history),
            "knowledge_base_stats": self.knowledge_base.get_stats(),
            "iteration_history": self.iteration_history
        }
