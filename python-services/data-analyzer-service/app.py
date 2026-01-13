"""
数据优化服务 API (重构版 - 支持大规模数据处理)
使用 LangGraph + Celery + Redis 构建的分布式数据优化服务
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uvicorn
from loguru import logger
import uuid
from datetime import datetime

from config import config
from task_manager import TaskManager
from storage_manager import StorageManager
from tasks import optimize_dataset_async

# 初始化 FastAPI
app = FastAPI(
    title="Data Optimization Service (Distributed)",
    description="基于 LangGraph + Celery + Redis 的分布式数据优化服务，支持大规模数据处理",
    version="5.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
task_manager = None
storage_manager = None

# ==================== 数据模型 ====================

class OptimizationRequest(BaseModel):
    """数据优化请求"""
    dataset: List[Dict[str, Any]] = Field(..., description="原始数据集")
    knowledge_base: Optional[List[str]] = Field(None, description="知识库（用于RAG校验）")
    optimization_guidance: Optional[Dict[str, Any]] = Field(
        None, 
        description="优化指导（可选）。如果提供，使用'指定优化'模式；否则使用'标注流程优化'模式"
    )
    task_id: Optional[str] = Field(None, description="任务ID（可选）")
    save_reports: bool = Field(True, description="是否保存分析报告")

class OptimizationResponse(BaseModel):
    """数据优化响应"""
    task_id: str
    status: str
    mode: str = Field(..., description="优化模式: auto（标注流程优化）或 guided（指定优化）")
    message: str

class OptimizationResult(BaseModel):
    """优化结果"""
    task_id: str
    status: str
    mode: Optional[str] = None
    progress: Optional[float] = Field(None, description="进度百分比 (0-100)")
    completed_batches: Optional[int] = Field(None, description="已完成批次数")
    total_batches: Optional[int] = Field(None, description="总批次数")
    optimized_dataset: Optional[List[Dict[str, Any]]] = None
    statistics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str
    llm_available: bool
    embedding_model: str
    workflow_engine: str

# ==================== 初始化 ====================

@app.on_event("startup")
async def startup_event():
    """服务启动时初始化"""
    global task_manager, storage_manager
    
    try:
        logger.info("="*60)
        logger.info("初始化数据优化服务 (分布式版本)")
        logger.info("="*60)
        
        # 初始化任务管理器
        logger.info("初始化任务管理器 (Redis)...")
        task_manager = TaskManager()
        
        # 初始化存储管理器
        if config.SAVE_DATASETS or config.SAVE_REPORTS:
            logger.info(f"初始化存储管理器: {config.OUTPUT_DIR}")
            storage_manager = StorageManager(output_dir=config.OUTPUT_DIR)
        
        logger.info("="*60)
        logger.info("✅ 数据优化服务初始化完成")
        logger.info(f"   - Redis: {config.REDIS_HOST}:{config.REDIS_PORT}")
        logger.info(f"   - 批次大小: {config.BATCH_SIZE}")
        logger.info(f"   - 最大 Worker: {config.MAX_WORKERS}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {e}")
        raise

# ==================== API 端点 ====================

@app.post("/api/v1/optimize", response_model=OptimizationResponse)
async def optimize_dataset(request: OptimizationRequest):
    """
    优化数据集（异步 - 使用 Celery）
    
    支持两种模式：
    1. 标注流程优化（auto）：不提供 optimization_guidance，自动诊断和优化
    2. 指定优化（guided）：提供 optimization_guidance，根据指导优化
    
    特性：
    - 分片处理：自动将大数据集切分成小批次处理
    - 持久化：任务状态保存在 Redis，支持断点续传
    - 进度跟踪：实时查看处理进度
    - 分布式：支持多 Worker 并行处理
    """
    try:
        task_id = request.task_id or f"task_{uuid.uuid4().hex[:8]}"
        mode = "guided" if request.optimization_guidance else "auto"
        
        logger.info(f"[{task_id}] 收到数据优化请求")
        logger.info(f"  数据集大小: {len(request.dataset)}")
        logger.info(f"  优化模式: {mode}")
        logger.info(f"  批次大小: {config.BATCH_SIZE}")
        
        # 创建任务记录
        task_manager.create_task(
            task_id=task_id,
            dataset_size=len(request.dataset),
            mode=mode,
            batch_size=config.BATCH_SIZE
        )
        
        # 提交到 Celery 队列
        optimize_dataset_async.delay(
            task_id=task_id,
            dataset=request.dataset,
            knowledge_base=request.knowledge_base,
            optimization_guidance=request.optimization_guidance,
            save_reports=request.save_reports
        )
        
        total_batches = (len(request.dataset) + config.BATCH_SIZE - 1) // config.BATCH_SIZE
        
        return OptimizationResponse(
            task_id=task_id,
            status="pending",
            mode=mode,
            message=f"数据优化任务已提交（{mode} 模式），数据集: {len(request.dataset)} 样本，分 {total_batches} 批处理"
        )
        
    except Exception as e:
        logger.error(f"创建优化任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/optimize/{task_id}", response_model=OptimizationResult)
async def get_optimization_result(task_id: str):
    """
    获取优化结果（支持进度查询）
    
    返回：
    - status: pending, processing, completed, failed
    - progress: 0-100 的进度百分比
    - completed_batches: 已完成的批次数
    - total_batches: 总批次数
    """
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    
    # 如果任务已完成，获取完整结果
    optimized_dataset = None
    if task["status"] == "completed":
        batch_results = task_manager.get_batch_results(task_id)
        optimized_dataset = []
        for batch in batch_results:
            if "optimized_samples" in batch:
                optimized_dataset.extend(batch["optimized_samples"])
    
    return OptimizationResult(
        task_id=task_id,
        status=task["status"],
        mode=task.get("mode"),
        progress=task.get("progress"),
        completed_batches=task.get("completed_batches"),
        total_batches=task.get("total_batches"),
        optimized_dataset=optimized_dataset,
        statistics=task.get("statistics"),
        error=task.get("error")
    )


@app.post("/api/v1/optimize/sync")
async def optimize_dataset_sync(request: OptimizationRequest):
    """
    优化数据集（同步 - 仅用于小数据集）
    
    警告：仅适用于小数据集（< 100 样本）
    大数据集请使用异步接口 /api/v1/optimize
    """
    if len(request.dataset) > 100:
        raise HTTPException(
            status_code=400,
            detail="数据集过大，请使用异步接口 /api/v1/optimize"
        )
    
    try:
        task_id = request.task_id or f"task_{uuid.uuid4().hex[:8]}"
        mode = "guided" if request.optimization_guidance else "auto"
        
        logger.info(f"[{task_id}] 同步优化数据集")
        logger.info(f"  数据集大小: {len(request.dataset)}")
        logger.info(f"  优化模式: {mode}")
        
        # 直接调用 Celery 任务（同步执行）
        result = optimize_dataset_async(
            task_id=task_id,
            dataset=request.dataset,
            knowledge_base=request.knowledge_base,
            optimization_guidance=request.optimization_guidance,
            save_reports=request.save_reports
        )
        
        return result
        
    except Exception as e:
        logger.error(f"同步优化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/knowledge-base/load")
async def load_knowledge_base(knowledge: List[str]):
    """
    加载知识库
    
    注意：在分布式环境中，知识库需要在每个 Worker 中加载
    建议在优化请求中直接传递知识库
    """
    try:
        logger.info(f"收到知识库加载请求，共 {len(knowledge)} 条知识")
        
        return {
            "status": "success",
            "message": f"知识库将在任务执行时加载（共 {len(knowledge)} 条）",
            "note": "在分布式环境中，请在优化请求中直接传递知识库"
        }
        
    except Exception as e:
        logger.error(f"加载知识库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    try:
        # 检查 Redis 连接
        task_manager.redis_client.ping()
        redis_available = True
    except:
        redis_available = False
    
    return HealthResponse(
        status="healthy" if redis_available else "degraded",
        service="data-optimization-service",
        version="5.0.0",
        llm_available=redis_available,  # 简化检查
        embedding_model=config.EMBEDDING_MODEL,
        workflow_engine="LangGraph + Celery + Redis"
    )


@app.get("/api/v1/tasks")
async def list_saved_tasks():
    """列出所有已保存的任务"""
    if not storage_manager:
        raise HTTPException(status_code=503, detail="存储管理器未初始化")
    
    try:
        tasks = storage_manager.list_tasks()
        return {
            "status": "success",
            "total": len(tasks),
            "tasks": tasks
        }
    except Exception as e:
        logger.error(f"列出任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/tasks/{task_id}/dataset")
async def get_saved_dataset(task_id: str):
    """获取已保存的数据集"""
    if not storage_manager:
        raise HTTPException(status_code=503, detail="存储管理器未初始化")
    
    try:
        data = storage_manager.load_dataset(task_id)
        return {
            "status": "success",
            "task_id": task_id,
            "dataset": data["dataset"],
            "metadata": data["metadata"]
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"加载数据集失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stats")
async def get_system_stats():
    """获取系统统计信息"""
    if not task_manager:
        raise HTTPException(status_code=503, detail="服务未初始化")
    
    all_tasks = task_manager.list_tasks()
    
    return {
        "total_tasks": len(all_tasks),
        "pending_tasks": len([t for t in all_tasks if t["status"] == "pending"]),
        "processing_tasks": len([t for t in all_tasks if t["status"] == "processing"]),
        "completed_tasks": len([t for t in all_tasks if t["status"] == "completed"]),
        "failed_tasks": len([t for t in all_tasks if t["status"] == "failed"]),
        "workflow_engine": "LangGraph + Celery + Redis",
        "batch_size": config.BATCH_SIZE,
        "max_workers": config.MAX_WORKERS
    }


@app.post("/api/v1/tasks/{task_id}/resume")
async def resume_task_endpoint(task_id: str):
    """恢复中断的任务"""
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    
    if task["status"] in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail=f"任务已{task['status']}，无法恢复")
    
    # 重新提交任务
    from tasks import resume_task
    resume_task.delay(task_id)
    
    return {
        "status": "success",
        "message": f"任务 {task_id} 已重新提交",
        "task_id": task_id
    }


@app.delete("/api/v1/tasks/{task_id}")
async def delete_task_endpoint(task_id: str):
    """删除任务"""
    task = task_manager.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    
    task_manager.delete_task(task_id)
    
    return {
        "status": "success",
        "message": f"任务 {task_id} 已删除"
    }


# ==================== 启动服务 ====================

if __name__ == "__main__":
    port = config.PORT
    logger.info(f"启动数据优化服务（分布式版本），端口: {port}")
    logger.info(f"Redis: {config.REDIS_HOST}:{config.REDIS_PORT}")
    logger.info(f"批次大小: {config.BATCH_SIZE}")
    uvicorn.run(app, host=config.HOST, port=port)
