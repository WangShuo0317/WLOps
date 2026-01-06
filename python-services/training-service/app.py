"""
训练服务 - 基于LLaMA Factory
提供模型训练API，供Spring Boot调用
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uvicorn
from loguru import logger
import sys
import os

# 添加LLaMA Factory到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../LLaMA-Factory/src'))

from llamafactory_adapter import LLaMAFactoryAdapter

# 创建FastAPI应用
app = FastAPI(
    title="IMTS Training Service",
    description="模型训练微服务 - 基于LLaMA Factory",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局适配器
adapter = None


@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    global adapter
    llamafactory_path = os.getenv("LLAMAFACTORY_PATH", "../../LLaMA-Factory")
    adapter = LLaMAFactoryAdapter(llamafactory_path)
    logger.info("训练服务启动完成")


# ==================== 数据模型 ====================

class TrainingRequest(BaseModel):
    """训练请求"""
    model_name: str = Field(..., description="模型名称")
    dataset: str = Field(..., description="数据集名称")
    stage: str = Field(default="sft", description="训练阶段")
    finetuning_type: str = Field(default="lora", description="微调类型")
    batch_size: int = Field(default=2, ge=1)
    learning_rate: float = Field(default=5e-5, gt=0)
    epochs: float = Field(default=3.0, gt=0)
    max_steps: int = Field(default=-1)
    lora_rank: int = Field(default=8, ge=1)
    lora_alpha: int = Field(default=16, ge=1)
    output_dir: Optional[str] = None
    custom_config: Optional[Dict[str, Any]] = None


class TrainingResponse(BaseModel):
    """训练响应"""
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    """任务状态"""
    job_id: str
    status: str
    pid: Optional[int] = None
    progress: Optional[float] = None
    current_loss: Optional[float] = None


# ==================== API端点 ====================

@app.post("/train", response_model=TrainingResponse)
async def create_training_job(request: TrainingRequest, background_tasks: BackgroundTasks):
    """创建训练任务"""
    try:
        import uuid
        job_id = f"train_{uuid.uuid4().hex[:8]}"
        
        job_config = {
            "job_id": job_id,
            "model_name": request.model_name,
            "dataset": request.dataset,
            "stage": request.stage,
            "finetuning_type": request.finetuning_type,
            "batch_size": request.batch_size,
            "learning_rate": request.learning_rate,
            "epochs": request.epochs,
            "max_steps": request.max_steps,
            "lora_rank": request.lora_rank,
            "lora_alpha": request.lora_alpha,
            "output_dir": request.output_dir or f"./outputs/{job_id}",
        }
        
        if request.custom_config:
            job_config.update(request.custom_config)
        
        config_path = adapter.create_training_config(job_config)
        background_tasks.add_task(adapter.start_training, job_id, config_path)
        
        return TrainingResponse(
            job_id=job_id,
            status="pending",
            message="训练任务已创建"
        )
    except Exception as e:
        logger.error(f"创建训练任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """获取任务状态"""
    try:
        status = adapter.get_job_status(job_id)
        if status["status"] == "not_found":
            raise HTTPException(status_code=404, detail="任务不存在")
        return JobStatus(**status)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/jobs/{job_id}/stop")
async def stop_job(job_id: str):
    """停止训练任务"""
    try:
        success = adapter.stop_training(job_id)
        if success:
            return {"message": "任务已停止"}
        raise HTTPException(status_code=400, detail="无法停止任务")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "training-service"
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
