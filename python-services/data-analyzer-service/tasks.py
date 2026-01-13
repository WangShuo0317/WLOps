"""
Celery 异步任务
"""
from typing import Dict, List, Any, Optional
from loguru import logger
import time

from celery_app import celery_app
from config import config
from task_manager import TaskManager
from llm_client import LLMClient
from sentence_transformers import SentenceTransformer
from knowledge_base_manager import KnowledgeBaseManager
from workflow_graph import DataOptimizationWorkflow
from storage_manager import StorageManager


# 全局变量（每个 Worker 进程初始化一次）
workflow = None
storage_manager = None
task_manager = None


def init_worker():
    """初始化 Worker"""
    global workflow, storage_manager, task_manager
    
    if workflow is None:
        logger.info("初始化 Celery Worker...")
        
        # 初始化 LLM 客户端
        llm_client = LLMClient()
        
        # 初始化 Embedding 模型
        embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        
        # 初始化知识库管理器
        knowledge_base_manager = KnowledgeBaseManager(embedding_model)
        
        # 初始化工作流
        workflow = DataOptimizationWorkflow(
            llm_client=llm_client,
            embedding_model=embedding_model,
            knowledge_base_manager=knowledge_base_manager
        )
        
        # 初始化存储管理器
        if config.SAVE_DATASETS or config.SAVE_REPORTS:
            storage_manager = StorageManager(output_dir=config.OUTPUT_DIR)
        
        # 初始化任务管理器
        task_manager = TaskManager()
        
        logger.info("✅ Celery Worker 初始化完成")


@celery_app.task(bind=True, name="tasks.optimize_dataset_async")
def optimize_dataset_async(
    self,
    task_id: str,
    dataset: List[Dict],
    knowledge_base: Optional[List[str]] = None,
    optimization_guidance: Optional[Dict] = None,
    save_reports: bool = True
):
    """
    异步优化数据集（智能分批处理）
    
    工作流：
    1. 全量诊断 - 使用完整数据集进行语义分布分析
    2. 分批优化 - 将需要优化的样本分批调用 LLM
    3. 分批校验 - 将优化后的样本分批进行 RAG 校验
    4. 全量清洗 - 对最终结果进行 PII 清洗
    
    Args:
        task_id: 任务ID
        dataset: 原始数据集（全量）
        knowledge_base: 知识库
        optimization_guidance: 优化指导
        save_reports: 是否保存报告
    """
    init_worker()
    
    try:
        logger.info(f"[{task_id}] 开始异步优化任务")
        logger.info(f"  数据集大小: {len(dataset)}")
        logger.info(f"  优化批次大小: {config.BATCH_SIZE}")
        
        mode = "guided" if optimization_guidance else "auto"
        
        # 更新任务状态为处理中
        task_manager.update_task_status(task_id, "processing", current_phase="diagnostic")
        
        # 加载知识库
        if knowledge_base:
            logger.info(f"加载知识库: {len(knowledge_base)} 条")
            workflow.knowledge_base.add_knowledge(knowledge_base)
        
        # ==================== 阶段 1: 全量诊断 ====================
        logger.info(f"\n{'='*60}")
        logger.info(f"阶段 1: 全量诊断（需要完整数据集）")
        logger.info(f"{'='*60}")
        
        task_manager.update_task_status(task_id, "processing", current_phase="diagnostic")
        
        # 执行全量诊断
        diagnostic_result = workflow.diagnostic_agent.diagnose_full(dataset) if mode == "auto" else \
                           workflow.diagnostic_agent.diagnose_guided(dataset, optimization_guidance)
        
        sparse_clusters = diagnostic_result["sparse_clusters"]
        low_quality_samples = diagnostic_result["low_quality_samples"]
        diagnostic_report = diagnostic_result["report"]
        
        logger.info(f"✅ 诊断完成:")
        logger.info(f"   - 稀缺聚类: {len(sparse_clusters)} 个")
        logger.info(f"   - 低质量样本: {len(low_quality_samples)} 个")
        
        # ==================== 阶段 2: 分批优化（调用 LLM）====================
        logger.info(f"\n{'='*60}")
        logger.info(f"阶段 2: 分批优化（COT 重写 + 样本生成）")
        logger.info(f"{'='*60}")
        
        task_manager.update_task_status(task_id, "processing", current_phase="optimization")
        
        # 2.1 优化低质量样本（分批）
        optimized_samples = []
        if low_quality_samples:
            batch_size = config.BATCH_SIZE
            total_batches = (len(low_quality_samples) + batch_size - 1) // batch_size
            
            logger.info(f"优化低质量样本: {len(low_quality_samples)} 个，分 {total_batches} 批")
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(low_quality_samples))
                batch_samples = low_quality_samples[start_idx:end_idx]
                
                logger.info(f"  批次 {batch_idx + 1}/{total_batches}: 优化 {len(batch_samples)} 个样本")
                
                # 优化当前批次
                batch_result = workflow.optimization_agent.optimize_samples(
                    dataset=dataset,
                    low_quality_samples=batch_samples,
                    mode=mode,
                    guidance=optimization_guidance
                )
                
                optimized_samples.extend(batch_result["samples"])
                
                # 更新进度
                progress = ((batch_idx + 1) / (total_batches + 1)) * 50  # 优化阶段占 50%
                task_manager.update_task_status(
                    task_id, 
                    "processing",
                    progress=progress,
                    completed_batches=batch_idx + 1,
                    total_batches=total_batches + 1,
                    current_phase="optimization"
                )
        
        # 2.2 生成稀缺样本（分批）
        generated_samples = []
        if sparse_clusters:
            # 计算需要生成的样本数
            total_to_generate = sum(cluster.get("samples_to_generate", 0) for cluster in sparse_clusters)
            
            if total_to_generate > 0:
                batch_size = config.BATCH_SIZE
                total_batches = (total_to_generate + batch_size - 1) // batch_size
                
                logger.info(f"生成稀缺样本: {total_to_generate} 个，分 {total_batches} 批")
                
                # 按批次生成
                for batch_idx in range(total_batches):
                    samples_in_batch = min(batch_size, total_to_generate - len(generated_samples))
                    
                    logger.info(f"  批次 {batch_idx + 1}/{total_batches}: 生成 {samples_in_batch} 个样本")
                    
                    # 生成当前批次
                    batch_result = workflow.optimization_agent.generate_samples(
                        sparse_clusters=sparse_clusters,
                        mode=mode,
                        guidance=optimization_guidance,
                        max_samples=samples_in_batch
                    )
                    
                    generated_samples.extend(batch_result["samples"])
                    
                    # 更新进度
                    progress = 50 + ((batch_idx + 1) / total_batches) * 25  # 生成阶段占 25%
                    task_manager.update_task_status(
                        task_id,
                        "processing",
                        progress=progress,
                        current_phase="generation"
                    )
        
        logger.info(f"✅ 优化完成:")
        logger.info(f"   - 优化样本: {len(optimized_samples)}")
        logger.info(f"   - 生成样本: {len(generated_samples)}")
        
        # ==================== 阶段 3: 分批校验（调用 LLM）====================
        logger.info(f"\n{'='*60}")
        logger.info(f"阶段 3: 分批 RAG 校验")
        logger.info(f"{'='*60}")
        
        task_manager.update_task_status(task_id, "processing", current_phase="verification")
        
        samples_to_verify = optimized_samples + generated_samples
        verified_samples = []
        
        if samples_to_verify:
            batch_size = config.BATCH_SIZE
            total_batches = (len(samples_to_verify) + batch_size - 1) // batch_size
            
            logger.info(f"校验样本: {len(samples_to_verify)} 个，分 {total_batches} 批")
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(samples_to_verify))
                batch_samples = samples_to_verify[start_idx:end_idx]
                
                logger.info(f"  批次 {batch_idx + 1}/{total_batches}: 校验 {len(batch_samples)} 个样本")
                
                # 校验当前批次
                batch_result = workflow.verification_agent.verify_batch(batch_samples)
                verified_samples.extend(batch_result["verified_samples"])
                
                # 更新进度
                progress = 75 + ((batch_idx + 1) / total_batches) * 20  # 校验阶段占 20%
                task_manager.update_task_status(
                    task_id,
                    "processing",
                    progress=progress,
                    current_phase="verification"
                )
        
        logger.info(f"✅ 校验完成: {len(verified_samples)} 个样本")
        
        # ==================== 阶段 4: 全量清洗 ====================
        logger.info(f"\n{'='*60}")
        logger.info(f"阶段 4: PII 清洗")
        logger.info(f"{'='*60}")
        
        task_manager.update_task_status(task_id, "processing", current_phase="cleaning", progress=95)
        
        cleaning_result = workflow.cleaning_agent.clean_dataset(verified_samples)
        final_dataset = cleaning_result["cleaned_dataset"]
        
        logger.info(f"✅ 清洗完成: {cleaning_result['cleaned_count']} 个样本")
        
        # ==================== 汇总统计 ====================
        all_statistics = {
            "input_size": len(dataset),
            "output_size": len(final_dataset),
            "mode": mode,
            "diagnostic_report": diagnostic_report,
            "optimization_stats": {
                "optimized_count": len(optimized_samples),
                "generated_count": len(generated_samples),
                "sparse_clusters": len(sparse_clusters),
                "low_quality_samples": len(low_quality_samples)
            },
            "verification_stats": {
                "total": len(samples_to_verify),
                "verified": len(verified_samples)
            },
            "pii_cleaned_count": cleaning_result["cleaned_count"]
        }
        
        # 保存最终结果
        if storage_manager and save_reports:
            if config.SAVE_DATASETS:
                storage_manager.save_optimized_dataset(
                    task_id=task_id,
                    dataset=final_dataset,
                    statistics=all_statistics,
                    mode=mode
                )
            
            if config.SAVE_REPORTS:
                storage_manager.save_analysis_report(
                    task_id=task_id,
                    diagnostic_report=diagnostic_report,
                    statistics=all_statistics,
                    mode=mode
                )
        
        # 标记任务完成
        task_manager.complete_task(task_id, all_statistics)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ 任务完成!")
        logger.info(f"{'='*60}")
        logger.info(f"输入: {len(dataset)} 样本")
        logger.info(f"输出: {len(final_dataset)} 样本")
        
        return {
            "task_id": task_id,
            "status": "completed",
            "optimized_dataset": final_dataset,
            "statistics": all_statistics
        }
        
    except Exception as e:
        logger.error(f"[{task_id}] ❌ 任务失败: {e}")
        task_manager.fail_task(task_id, str(e))
        raise


@celery_app.task(name="tasks.resume_task")
def resume_task(task_id: str):
    """
    恢复中断的任务
    
    Args:
        task_id: 任务ID
    """
    init_worker()
    
    try:
        logger.info(f"[{task_id}] 尝试恢复任务...")
        
        # 获取任务信息
        task = task_manager.get_task(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return
        
        if task["status"] in ["completed", "failed"]:
            logger.info(f"任务已完成或失败，无需恢复: {task_id}")
            return
        
        # 获取下一个要处理的批次
        next_batch = task_manager.resume_task(task_id)
        if next_batch is None:
            logger.info(f"任务无法恢复: {task_id}")
            return
        
        logger.info(f"[{task_id}] 从批次 {next_batch} 恢复任务")
        
        # TODO: 实现断点续传逻辑
        # 需要从 Redis 获取原始数据集和配置
        
    except Exception as e:
        logger.error(f"[{task_id}] 恢复任务失败: {e}")
        raise
