"""
LangGraph 工作流图
使用 LangGraph 构建数据优化的多智能体工作流
"""
from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from loguru import logger

from agents.diagnostic_agent import DiagnosticAgent
from agents.optimization_agent import OptimizationAgent
from agents.verification_agent import VerificationAgent
from agents.cleaning_agent import CleaningAgent


class WorkflowState(TypedDict):
    """工作流状态"""
    # 输入
    dataset: List[Dict[str, Any]]
    knowledge_base: List[str]
    optimization_guidance: Dict[str, Any]  # 优化指导（可选）
    
    # 模式选择
    mode: Literal["auto", "guided"]  # auto=标注流程优化, guided=指定优化
    
    # 诊断结果
    sparse_clusters: List[Dict]
    low_quality_samples: List[Dict]
    diagnostic_report: Dict[str, Any]
    
    # 优化结果
    optimized_samples: List[Dict]
    generated_samples: List[Dict]
    optimization_stats: Dict[str, Any]
    
    # 校验结果
    verified_dataset: List[Dict]
    verification_stats: Dict[str, Any]
    
    # 最终输出
    final_dataset: List[Dict]
    pii_cleaned_count: int
    
    # 元数据
    iteration_id: int
    errors: List[str]


class DataOptimizationWorkflow:
    """数据优化工作流"""
    
    def __init__(
        self,
        llm_client,
        embedding_model,
        knowledge_base_manager
    ):
        """
        初始化工作流
        
        Args:
            llm_client: LLM 客户端
            embedding_model: Embedding 模型
            knowledge_base_manager: 知识库管理器
        """
        self.llm_client = llm_client
        self.embedding_model = embedding_model
        self.knowledge_base = knowledge_base_manager
        
        # 初始化智能体
        self.diagnostic_agent = DiagnosticAgent(embedding_model)
        self.optimization_agent = OptimizationAgent(llm_client)
        self.verification_agent = VerificationAgent(llm_client, knowledge_base_manager)
        self.cleaning_agent = CleaningAgent()
        
        # 构建工作流图
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 工作流图"""
        workflow = StateGraph(WorkflowState)
        
        # 添加节点
        workflow.add_node("mode_selector", self._select_mode)
        workflow.add_node("diagnostic", self._run_diagnostic)
        workflow.add_node("optimization", self._run_optimization)
        workflow.add_node("verification", self._run_verification)
        workflow.add_node("cleaning", self._run_cleaning)
        
        # 定义边
        workflow.set_entry_point("mode_selector")
        
        # 模式选择后进入诊断
        workflow.add_edge("mode_selector", "diagnostic")
        
        # 诊断后进入优化
        workflow.add_edge("diagnostic", "optimization")
        
        # 优化后进入校验
        workflow.add_edge("optimization", "verification")
        
        # 校验后进入清洗
        workflow.add_edge("verification", "cleaning")
        
        # 清洗后结束
        workflow.add_edge("cleaning", END)
        
        return workflow.compile()
    
    def _select_mode(self, state: WorkflowState) -> WorkflowState:
        """
        选择优化模式
        
        - auto: 标注流程优化（无优化指导）
        - guided: 指定优化（有优化指导）
        """
        has_guidance = state.get("optimization_guidance") is not None
        
        if has_guidance:
            state["mode"] = "guided"
            logger.info("🎯 模式: 指定优化（根据优化指导执行）")
        else:
            state["mode"] = "auto"
            logger.info("🤖 模式: 标注流程优化（自动诊断和优化）")
        
        return state
    
    def _run_diagnostic(self, state: WorkflowState) -> WorkflowState:
        """
        Module 1: 诊断
        
        - auto 模式: 全面诊断（语义分布 + 推理质量）
        - guided 模式: 根据指导诊断特定问题
        """
        logger.info("\n" + "="*60)
        logger.info("📊 Module 1: 诊断")
        logger.info("="*60)
        
        dataset = state["dataset"]
        mode = state["mode"]
        
        if mode == "auto":
            # 标注流程优化：全面诊断
            logger.info("执行全面诊断...")
            result = self.diagnostic_agent.diagnose_full(dataset)
        else:
            # 指定优化：根据指导诊断
            guidance = state["optimization_guidance"]
            logger.info(f"根据优化指导诊断: {guidance.get('focus_areas', [])}")
            result = self.diagnostic_agent.diagnose_guided(dataset, guidance)
        
        state["sparse_clusters"] = result["sparse_clusters"]
        state["low_quality_samples"] = result["low_quality_samples"]
        state["diagnostic_report"] = result["report"]
        
        logger.info(f"✅ 诊断完成:")
        logger.info(f"   - 稀缺聚类: {len(state['sparse_clusters'])} 个")
        logger.info(f"   - 低质量样本: {len(state['low_quality_samples'])} 个")
        
        return state
    
    def _run_optimization(self, state: WorkflowState) -> WorkflowState:
        """
        Module 2: 生成增强
        
        - COT 重写低质量样本
        - 合成生成稀缺样本
        """
        logger.info("\n" + "="*60)
        logger.info("🔧 Module 2: 生成增强")
        logger.info("="*60)
        
        dataset = state["dataset"]
        low_quality_samples = state["low_quality_samples"]
        sparse_clusters = state["sparse_clusters"]
        mode = state["mode"]
        
        # 优化低质量样本
        logger.info("优化低质量样本（COT 重写）...")
        optimized_result = self.optimization_agent.optimize_samples(
            dataset=dataset,
            low_quality_samples=low_quality_samples,
            mode=mode,
            guidance=state.get("optimization_guidance")
        )
        
        # 生成稀缺样本
        logger.info("生成稀缺样本...")
        generated_result = self.optimization_agent.generate_samples(
            sparse_clusters=sparse_clusters,
            mode=mode,
            guidance=state.get("optimization_guidance")
        )
        
        state["optimized_samples"] = optimized_result["samples"]
        state["generated_samples"] = generated_result["samples"]
        state["optimization_stats"] = {
            "optimized_count": optimized_result["count"],
            "generated_count": generated_result["count"],
            "high_quality_kept": optimized_result["high_quality_kept"]
        }
        
        logger.info(f"✅ 生成增强完成:")
        logger.info(f"   - 优化样本: {optimized_result['count']}")
        logger.info(f"   - 生成样本: {generated_result['count']}")
        logger.info(f"   - 保留高质量: {optimized_result['high_quality_kept']}")
        
        return state
    
    def _run_verification(self, state: WorkflowState) -> WorkflowState:
        """
        Module 3: RAG 校验
        
        校验所有优化和生成的样本
        """
        logger.info("\n" + "="*60)
        logger.info("✓ Module 3: RAG 校验")
        logger.info("="*60)
        
        optimized_samples = state["optimized_samples"]
        generated_samples = state["generated_samples"]
        
        # 合并需要校验的样本
        samples_to_verify = optimized_samples + generated_samples
        
        logger.info(f"需要校验的样本: {len(samples_to_verify)}")
        
        if samples_to_verify:
            result = self.verification_agent.verify_batch(samples_to_verify)
            
            state["verified_dataset"] = result["verified_samples"]
            state["verification_stats"] = result["stats"]
            
            logger.info(f"✅ RAG 校验完成:")
            logger.info(f"   - 通过: {result['stats']['passed']}")
            logger.info(f"   - 修正: {result['stats']['corrected']}")
            logger.info(f"   - 拒绝: {result['stats']['rejected']}")
        else:
            state["verified_dataset"] = []
            state["verification_stats"] = {
                "total": 0, "passed": 0, "corrected": 0, "rejected": 0
            }
        
        return state
    
    def _run_cleaning(self, state: WorkflowState) -> WorkflowState:
        """
        Module 4: PII 清洗
        
        清洗隐私信息
        """
        logger.info("\n" + "="*60)
        logger.info("🧹 Module 4: PII 清洗")
        logger.info("="*60)
        
        verified_dataset = state["verified_dataset"]
        
        result = self.cleaning_agent.clean_dataset(verified_dataset)
        
        state["final_dataset"] = result["cleaned_dataset"]
        state["pii_cleaned_count"] = result["cleaned_count"]
        
        logger.info(f"✅ PII 清洗完成: 清洗了 {result['cleaned_count']} 个样本")
        
        return state
    
    def run(
        self,
        dataset: List[Dict],
        knowledge_base: List[str] = None,
        optimization_guidance: Dict = None,
        iteration_id: int = 0
    ) -> Dict[str, Any]:
        """
        执行完整的数据优化工作流
        
        Args:
            dataset: 原始数据集
            knowledge_base: 知识库（可选）
            optimization_guidance: 优化指导（可选）
                - 如果提供，使用"指定优化"模式
                - 如果不提供，使用"标注流程优化"模式
            iteration_id: 迭代编号
            
        Returns:
            优化结果
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 开始数据优化工作流 - 迭代 {iteration_id}")
        logger.info(f"{'='*60}")
        logger.info(f"输入数据集大小: {len(dataset)}")
        
        # 加载知识库
        if knowledge_base:
            logger.info(f"加载知识库: {len(knowledge_base)} 条")
            self.knowledge_base.add_knowledge(knowledge_base)
        
        # 初始化状态
        initial_state: WorkflowState = {
            "dataset": dataset,
            "knowledge_base": knowledge_base or [],
            "optimization_guidance": optimization_guidance,
            "mode": "auto",
            "sparse_clusters": [],
            "low_quality_samples": [],
            "diagnostic_report": {},
            "optimized_samples": [],
            "generated_samples": [],
            "optimization_stats": {},
            "verified_dataset": [],
            "verification_stats": {},
            "final_dataset": [],
            "pii_cleaned_count": 0,
            "iteration_id": iteration_id,
            "errors": []
        }
        
        # 执行工作流
        final_state = self.graph.invoke(initial_state)
        
        # 构建结果
        result = {
            "optimized_dataset": final_state["final_dataset"],
            "statistics": {
                "input_size": len(dataset),
                "output_size": len(final_state["final_dataset"]),
                "mode": final_state["mode"],
                "optimization_stats": final_state["optimization_stats"],
                "verification_stats": final_state["verification_stats"],
                "pii_cleaned_count": final_state["pii_cleaned_count"]
            },
            "diagnostic_report": final_state["diagnostic_report"]
        }
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ 工作流完成!")
        logger.info(f"{'='*60}")
        logger.info(f"输入: {len(dataset)} 样本")
        logger.info(f"输出: {len(final_state['final_dataset'])} 样本")
        logger.info(f"模式: {final_state['mode']}")
        
        return result
