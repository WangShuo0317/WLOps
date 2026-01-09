"""
数据优化服务 API
提供给 Spring Boot 调用的 RESTful 接口
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uvicorn
from loguru import logger
import json
import uuid
from pathlib import Path
from datetime import datetime

from config import config
from llm_client import LLMClient
from sentence_transformers import SentenceTransformer
from system_integration import SelfEvolvingDataOptimizer

# 初始化 FastAPI
app = FastAPI(
    title="Data Optimization Service",
    description="自进化数据优化智能体服务 - 将原始数据集转换为高质量数据集",
    version="3.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
optimizer = None
optimization_tasks = {}  # 存储优化任务状态

# ==================== 数据模型 ====================

class OptimizationRequest(BaseModel):
    """数据优化请求"""
    dataset: List[Dict[str, Any]] = Field(..., description="原始数据集")
    knowledge_base: Optional[List[str]] = Field(None, description="知识库（用于RAG校验）")
    task_id: Optional[str] = Field(None, description="任务ID（可选）")
    save_reports: bool = Field(True, description="是否保存分析报告")

class OptimizationResponse(BaseModel):
    """数据优化响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态: processing/completed/failed")
    message: str = Field(..., description="状态消息")

class OptimizationResult(BaseModel):
    """优化结果"""
    task_id: str
    status: str
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

# ==================== 初始化 ====================

@app.on_event("startup")
async def startup_event():
    """服务启动时初始化"""
    global optimizer
    
    try:
        logger.info("初始化数据优化服务...")
        
        # 初始化 LLM 客户端
        llm_client = LLMClient()
        
        # 初始化 Embedding 模型
        logger.info(f"加载 Embedding 模型: {config.EMBEDDING_MODEL}")
        embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)
        
        # 初始化优化器
        optimizer = SelfEvolvingDataOptimizer(
            llm_client=llm_client,
            embedding_model=embedding_model,
            knowledge_base_path=config.VECTOR_DB_PATH
        )
        
        logger.info("数据优化服务初始化完成")
        
    except Exception as e:
        logger.error(f"服务初始化失败: {e}")
        raise

# ==================== API 端点 ====================

@app.post("/api/v1/optimize", response_model=OptimizationResponse)
async def optimize_dataset(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks
):
    """
    优化数据集（异步）
    
    将原始数据集转换为纯净的高质量数据集
    
    流程:
    1. 诊断：识别稀缺样本和低质量样本
    2. 优化：COT重写低质量样本 + 生成稀缺样本
    3. 校验：RAG校验所有优化/生成的样本
    4. 清洗：PII隐私清洗
    
    返回：纯净的高质量数据集
    """
    try:
        # 生成任务ID
        task_id = request.task_id or f"task_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"[{task_id}] 收到数据优化请求，数据集大小: {len(request.dataset)}")
        
        # 初始化任务状态
        optimization_tasks[task_id] = {
            "status": "processing",
            "start_time": datetime.now().isoformat(),
            "dataset_size": len(request.dataset)
        }
        
        # 在后台执行优化
        background_tasks.add_task(
            run_optimization,
            task_id,
            request.dataset,
            request.knowledge_base,
            request.save_reports
        )
        
        return OptimizationResponse(
            task_id=task_id,
            status="processing",
            message=f"数据优化任务已启动，数据集大小: {len(request.dataset)}"
        )
        
    except Exception as e:
        logger.error(f"创建优化任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/optimize/{task_id}", response_model=OptimizationResult)
async def get_optimization_result(task_id: str):
    """
    获取优化结果
    
    查询优化任务的状态和结果
    """
    if task_id not in optimization_tasks:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    
    task = optimization_tasks[task_id]
    
    return OptimizationResult(
        task_id=task_id,
        status=task["status"],
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
        
        logger.info(f"[{task_id}] 同步优化数据集，大小: {len(request.dataset)}")
        
        # 加载知识库
        if request.knowledge_base:
            optimizer.load_knowledge_base(request.knowledge_base)
        
        # 执行优化
        result = optimizer.run_iteration(
            dataset=request.dataset,
            iteration_id=0,
            save_reports=request.save_reports
        )
        
        optimized_dataset = result["optimized_dataset"]
        iteration_summary = result["iteration_summary"]
        
        logger.info(f"[{task_id}] 优化完成: {len(request.dataset)} → {len(optimized_dataset)}")
        
        return {
            "task_id": task_id,
            "status": "completed",
            "optimized_dataset": optimized_dataset,
            "statistics": {
                "input_size": iteration_summary["input_size"],
                "output_size": iteration_summary["output_size"],
                "optimized_count": iteration_summary["optimization_stats"]["optimized_count"],
                "generated_count": iteration_summary["generation_stats"]["generated_count"],
                "quality_improvement": iteration_summary["quality_improvement"],
                "duration_seconds": iteration_summary["duration_seconds"]
            }
        }
        
    except Exception as e:
        logger.error(f"同步优化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/knowledge-base/load")
async def load_knowledge_base(knowledge: List[str]):
    """
    加载知识库
    
    用于 RAG 校验的外部知识库
    """
    try:
        logger.info(f"加载知识库，共 {len(knowledge)} 条知识")
        
        optimizer.load_knowledge_base(knowledge)
        
        return {
            "status": "success",
            "message": f"成功加载 {len(knowledge)} 条知识",
            "knowledge_base_stats": optimizer.knowledge_base.get_stats()
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
        version="3.1.0",
        llm_available=optimizer.llm_client.is_available() if optimizer else False,
        embedding_model=config.EMBEDDING_MODEL
    )


@app.get("/api/v1/stats")
async def get_system_stats():
    """获取系统统计信息"""
    if not optimizer:
        raise HTTPException(status_code=503, detail="服务未初始化")
    
    return {
        "system_stats": optimizer.get_system_stats(),
        "active_tasks": len([t for t in optimization_tasks.values() if t["status"] == "processing"]),
        "completed_tasks": len([t for t in optimization_tasks.values() if t["status"] == "completed"]),
        "failed_tasks": len([t for t in optimization_tasks.values() if t["status"] == "failed"])
    }


# ==================== 后台任务 ====================

async def run_optimization(
    task_id: str,
    dataset: List[Dict],
    knowledge_base: Optional[List[str]],
    save_reports: bool
):
    """后台执行优化任务"""
    try:
        logger.info(f"[{task_id}] 开始后台优化任务")
        
        # 加载知识库
        if knowledge_base:
            optimizer.load_knowledge_base(knowledge_base)
        
        # 执行优化
        result = optimizer.run_iteration(
            dataset=dataset,
            iteration_id=0,
            save_reports=save_reports
        )
        
        optimized_dataset = result["optimized_dataset"]
        iteration_summary = result["iteration_summary"]
        
        # 更新任务状态
        optimization_tasks[task_id].update({
            "status": "completed",
            "end_time": datetime.now().isoformat(),
            "optimized_dataset": optimized_dataset,
            "statistics": {
                "input_size": iteration_summary["input_size"],
                "output_size": iteration_summary["output_size"],
                "optimized_count": iteration_summary["optimization_stats"]["optimized_count"],
                "generated_count": iteration_summary["generation_stats"]["generated_count"],
                "quality_improvement": iteration_summary["quality_improvement"],
                "duration_seconds": iteration_summary["duration_seconds"]
            }
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
    logger.info(f"启动数据优化服务，端口: {port}")
    uvicorn.run(app, host=config.HOST, port=port)
