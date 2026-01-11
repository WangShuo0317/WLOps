"""
数据优化服务 API (重构版)
使用 LangGraph 构建的多智能体工作流
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Literal
import uvicorn
from loguru import logger
import uuid
from datetime import datetime

from config import config
from llm_client import LLMClient
from sentence_transformers import SentenceTransformer
from knowledge_base_manager import KnowledgeBaseManager
from workflow_graph import DataOptimizationWorkflow
from storage_manager import StorageManager

# 初始化 FastAPI
app = FastAPI(
    title="Data Optimization Service (LangGraph)",
    description="基于 LangGraph 的自进化数据优化智能体服务",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
workflow = None
storage_manager = None
optimization_tasks = {}

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
    global workflow, storage_manager
    
    try:
        logger.info("="*60)
        logger.info("初始化数据优化服务 (LangGraph 版本)")
        logger.info("="*60)
        
        # 初始化 LLM 客户端
        logger.info("初始化 LLM 客户端...")
        llm_client = LLMClient()
        
        # 初始化 Embedding 模型
        logger.info(f"加载 Embedding 模型: {config.EMBEDDING_MODEL}")
        embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        
        # 初始化知识库管理器
        logger.info("初始化知识库管理器...")
        knowledge_base_manager = KnowledgeBaseManager(embedding_model)
        
        # 初始化 LangGraph 工作流
        logger.info("构建 LangGraph 工作流...")
        workflow = DataOptimizationWorkflow(
            llm_client=llm_client,
            embedding_model=embedding_model,
            knowledge_base_manager=knowledge_base_manager
        )
        
        # 初始化存储管理器
        if config.SAVE_DATASETS or config.SAVE_REPORTS:
            logger.info(f"初始化存储管理器: {config.OUTPUT_DIR}")
            storage_manager = StorageManager(output_dir=config.OUTPUT_DIR)
        
        logger.info("="*60)
        logger.info("✅ 数据优化服务初始化完成")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ 服务初始化失败: {e}")
        raise

# ==================== API 端点 ====================

@app.post("/api/v1/optimize", response_model=OptimizationResponse)
async def optimize_dataset(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks
):
    """
    优化数据集（异步）
    
    支持两种模式：
    1. 标注流程优化（auto）：不提供 optimization_guidance，自动诊断和优化
    2. 指定优化（guided）：提供 optimization_guidance，根据指导优化
    
    工作流：
    - Module 1: 诊断（识别稀缺样本和低质量样本）
    - Module 2: 生成增强（COT重写 + 合成生成）
    - Module 3: RAG校验（校验所有优化/生成的样本）
    - Module 4: PII清洗（清洗隐私信息）
    """
    try:
        task_id = request.task_id or f"task_{uuid.uuid4().hex[:8]}"
        mode = "guided" if request.optimization_guidance else "auto"
        
        logger.info(f"[{task_id}] 收到数据优化请求")
        logger.info(f"  数据集大小: {len(request.dataset)}")
        logger.info(f"  优化模式: {mode}")
        
        # 初始化任务状态
        optimization_tasks[task_id] = {
            "status": "processing",
            "mode": mode,
            "start_time": datetime.now().isoformat(),
            "dataset_size": len(request.dataset)
        }
        
        # 在后台执行优化
        background_tasks.add_task(
            run_optimization,
            task_id,
            request.dataset,
            request.knowledge_base,
            request.optimization_guidance,
            request.save_reports
        )
        
        return OptimizationResponse(
            task_id=task_id,
            status="processing",
            mode=mode,
            message=f"数据优化任务已启动（{mode} 模式），数据集大小: {len(request.dataset)}"
        )
        
    except Exception as e:
        logger.error(f"创建优化任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/optimize/{task_id}", response_model=OptimizationResult)
async def get_optimization_result(task_id: str):
    """获取优化结果"""
    if task_id not in optimization_tasks:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    
    task = optimization_tasks[task_id]
    
    return OptimizationResult(
        task_id=task_id,
        status=task["status"],
        mode=task.get("mode"),
        optimized_dataset=task.get("optimized_dataset"),
        statistics=task.get("statistics"),
        error=task.get("error")
    )


@app.post("/api/v1/optimize/sync")
async def optimize_dataset_sync(request: OptimizationRequest):
    """
    优化数据集（同步）
    
    同步执行优化，直接返回结果
    适用于小数据集（< 100 样本）
    """
    try:
        task_id = request.task_id or f"task_{uuid.uuid4().hex[:8]}"
        mode = "guided" if request.optimization_guidance else "auto"
        
        logger.info(f"[{task_id}] 同步优化数据集")
        logger.info(f"  数据集大小: {len(request.dataset)}")
        logger.info(f"  优化模式: {mode}")
        
        # 执行优化
        result = workflow.run(
            dataset=request.dataset,
            knowledge_base=request.knowledge_base,
            optimization_guidance=request.optimization_guidance,
            iteration_id=0
        )
        
        optimized_dataset = result["optimized_dataset"]
        statistics = result["statistics"]
        
        logger.info(f"[{task_id}] 优化完成: {len(request.dataset)} → {len(optimized_dataset)}")
        
        # 保存数据集和报告
        if storage_manager and request.save_reports:
            if config.SAVE_DATASETS:
                storage_manager.save_optimized_dataset(
                    task_id=task_id,
                    dataset=optimized_dataset,
                    statistics=statistics,
                    mode=mode
                )
            
            if config.SAVE_REPORTS:
                storage_manager.save_analysis_report(
                    task_id=task_id,
                    diagnostic_report=result.get("diagnostic_report", {}),
                    statistics=statistics,
                    mode=mode
                )
        
        return {
            "task_id": task_id,
            "status": "completed",
            "mode": mode,
            "optimized_dataset": optimized_dataset,
            "statistics": statistics
        }
        
    except Exception as e:
        logger.error(f"同步优化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/knowledge-base/load")
async def load_knowledge_base(knowledge: List[str]):
    """加载知识库"""
    try:
        logger.info(f"加载知识库，共 {len(knowledge)} 条知识")
        
        workflow.knowledge_base.add_knowledge(knowledge)
        
        return {
            "status": "success",
            "message": f"成功加载 {len(knowledge)} 条知识",
            "knowledge_base_stats": workflow.knowledge_base.get_stats()
        }
        
    except Exception as e:
        logger.error(f"加载知识库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        service="data-optimization-service",
        version="4.0.0",
        llm_available=workflow.llm_client.is_available() if workflow else False,
        embedding_model=config.EMBEDDING_MODEL,
        workflow_engine="LangGraph"
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
    if not workflow:
        raise HTTPException(status_code=503, detail="服务未初始化")
    
    return {
        "knowledge_base_stats": workflow.knowledge_base.get_stats(),
        "active_tasks": len([t for t in optimization_tasks.values() if t["status"] == "processing"]),
        "completed_tasks": len([t for t in optimization_tasks.values() if t["status"] == "completed"]),
        "failed_tasks": len([t for t in optimization_tasks.values() if t["status"] == "failed"]),
        "workflow_engine": "LangGraph"
    }


# ==================== 后台任务 ====================

async def run_optimization(
    task_id: str,
    dataset: List[Dict],
    knowledge_base: Optional[List[str]],
    optimization_guidance: Optional[Dict],
    save_reports: bool = True
):
    """后台执行优化任务"""
    try:
        logger.info(f"[{task_id}] 开始后台优化任务")
        
        mode = "guided" if optimization_guidance else "auto"
        
        # 执行工作流
        result = workflow.run(
            dataset=dataset,
            knowledge_base=knowledge_base,
            optimization_guidance=optimization_guidance,
            iteration_id=0
        )
        
        optimized_dataset = result["optimized_dataset"]
        statistics = result["statistics"]
        
        # 保存数据集和报告
        if storage_manager and save_reports:
            if config.SAVE_DATASETS:
                storage_manager.save_optimized_dataset(
                    task_id=task_id,
                    dataset=optimized_dataset,
                    statistics=statistics,
                    mode=mode
                )
            
            if config.SAVE_REPORTS:
                storage_manager.save_analysis_report(
                    task_id=task_id,
                    diagnostic_report=result.get("diagnostic_report", {}),
                    statistics=statistics,
                    mode=mode
                )
        
        # 更新任务状态
        optimization_tasks[task_id].update({
            "status": "completed",
            "end_time": datetime.now().isoformat(),
            "optimized_dataset": optimized_dataset,
            "statistics": statistics
        })
        
        logger.info(f"[{task_id}] 优化完成: {len(dataset)} → {len(optimized_dataset)}")
        
    except Exception as e:
        logger.error(f"[{task_id}] 优化失败: {e}")
        
        optimization_tasks[task_id].update({
            "status": "failed",
            "end_time": datetime.now().isoformat(),
            "error": str(e)
        })


# ==================== 启动服务 ====================

if __name__ == "__main__":
    port = config.PORT
    logger.info(f"启动数据优化服务（LangGraph 版本），端口: {port}")
    uvicorn.run(app, host=config.HOST, port=port)
