"""
任务管理器 - 使用 Redis 持久化任务状态
"""
import json
import redis
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

from config import config


class TaskManager:
    """任务管理器 - 基于 Redis"""
    
    def __init__(self):
        """初始化 Redis 连接"""
        try:
            self.redis_client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                password=config.REDIS_PASSWORD,
                decode_responses=True
            )
            # 测试连接
            self.redis_client.ping()
            logger.info(f"✅ Redis 连接成功: {config.REDIS_HOST}:{config.REDIS_PORT}")
        except Exception as e:
            logger.error(f"❌ Redis 连接失败: {e}")
            raise
    
    def create_task(
        self,
        task_id: str,
        dataset_size: int,
        mode: str,
        batch_size: int
    ) -> Dict[str, Any]:
        """
        创建新任务
        
        Args:
            task_id: 任务ID
            dataset_size: 数据集大小
            mode: 优化模式
            batch_size: 批次大小
            
        Returns:
            任务信息
        """
        total_batches = (dataset_size + batch_size - 1) // batch_size
        
        task_data = {
            "task_id": task_id,
            "status": "pending",
            "mode": mode,
            "dataset_size": dataset_size,
            "batch_size": batch_size,
            "total_batches": total_batches,
            "completed_batches": 0,
            "progress": 0.0,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "error": None,
            "statistics": {},
            "current_batch": 0
        }
        
        # 保存到 Redis
        self.redis_client.hset(
            f"task:{task_id}",
            mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in task_data.items()}
        )
        
        # 添加到任务列表
        self.redis_client.zadd("tasks:all", {task_id: datetime.now().timestamp()})
        
        logger.info(f"✅ 任务已创建: {task_id} (共 {total_batches} 批)")
        
        return task_data
    
    def update_task_status(
        self,
        task_id: str,
        status: str,
        **kwargs
    ):
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 状态 (pending, processing, completed, failed)
            **kwargs: 其他要更新的字段（如 progress, current_phase, completed_batches 等）
        """
        updates = {"status": status}
        updates.update(kwargs)
        
        # 更新 Redis
        self.redis_client.hset(
            f"task:{task_id}",
            mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in updates.items()}
        )
        
        logger.debug(f"任务状态更新: {task_id} -> {status} {kwargs}")
    
    def update_batch_progress(
        self,
        task_id: str,
        batch_index: int,
        batch_result: Dict[str, Any]
    ):
        """
        更新批次进度
        
        Args:
            task_id: 任务ID
            batch_index: 批次索引
            batch_result: 批次处理结果
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return
        
        completed_batches = task["completed_batches"] + 1
        total_batches = task["total_batches"]
        progress = (completed_batches / total_batches) * 100
        
        # 保存批次结果
        self.redis_client.hset(
            f"task:{task_id}:batch:{batch_index}",
            mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in batch_result.items()}
        )
        
        # 更新任务进度
        self.update_task_status(
            task_id,
            status="processing",
            completed_batches=completed_batches,
            progress=round(progress, 2),
            current_batch=batch_index
        )
        
        logger.info(f"📊 任务进度: {task_id} - {completed_batches}/{total_batches} ({progress:.1f}%)")
    
    def complete_task(
        self,
        task_id: str,
        statistics: Dict[str, Any]
    ):
        """
        完成任务
        
        Args:
            task_id: 任务ID
            statistics: 统计信息
        """
        self.update_task_status(
            task_id,
            status="completed",
            progress=100.0,
            end_time=datetime.now().isoformat(),
            statistics=statistics
        )
        
        logger.info(f"✅ 任务完成: {task_id}")
    
    def fail_task(
        self,
        task_id: str,
        error: str
    ):
        """
        标记任务失败
        
        Args:
            task_id: 任务ID
            error: 错误信息
        """
        self.update_task_status(
            task_id,
            status="failed",
            end_time=datetime.now().isoformat(),
            error=error
        )
        
        logger.error(f"❌ 任务失败: {task_id} - {error}")
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务信息，如果不存在返回 None
        """
        task_data = self.redis_client.hgetall(f"task:{task_id}")
        
        if not task_data:
            return None
        
        # 解析 JSON 字段
        for key in ["statistics", "error"]:
            if key in task_data and task_data[key]:
                try:
                    task_data[key] = json.loads(task_data[key])
                except:
                    pass
        
        # 转换数值字段
        for key in ["dataset_size", "batch_size", "total_batches", "completed_batches", "current_batch"]:
            if key in task_data:
                task_data[key] = int(task_data[key])
        
        if "progress" in task_data:
            task_data["progress"] = float(task_data["progress"])
        
        return task_data
    
    def get_batch_results(self, task_id: str) -> List[Dict[str, Any]]:
        """
        获取所有批次结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            批次结果列表
        """
        task = self.get_task(task_id)
        if not task:
            return []
        
        results = []
        for i in range(task["total_batches"]):
            batch_data = self.redis_client.hgetall(f"task:{task_id}:batch:{i}")
            if batch_data:
                # 解析 JSON 字段
                for key in ["optimized_samples", "statistics"]:
                    if key in batch_data and batch_data[key]:
                        try:
                            batch_data[key] = json.loads(batch_data[key])
                        except:
                            pass
                results.append(batch_data)
        
        return results
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        列出任务
        
        Args:
            status: 过滤状态（可选）
            limit: 返回数量限制
            
        Returns:
            任务列表
        """
        # 获取所有任务ID（按时间倒序）
        task_ids = self.redis_client.zrevrange("tasks:all", 0, limit - 1)
        
        tasks = []
        for task_id in task_ids:
            task = self.get_task(task_id)
            if task:
                if status is None or task.get("status") == status:
                    tasks.append(task)
        
        return tasks
    
    def delete_task(self, task_id: str):
        """
        删除任务
        
        Args:
            task_id: 任务ID
        """
        task = self.get_task(task_id)
        if not task:
            return
        
        # 删除批次数据
        for i in range(task["total_batches"]):
            self.redis_client.delete(f"task:{task_id}:batch:{i}")
        
        # 删除任务数据
        self.redis_client.delete(f"task:{task_id}")
        
        # 从任务列表移除
        self.redis_client.zrem("tasks:all", task_id)
        
        logger.info(f"🗑️ 任务已删除: {task_id}")
    
    def resume_task(self, task_id: str) -> Optional[int]:
        """
        恢复中断的任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            下一个要处理的批次索引，如果任务不存在或已完成返回 None
        """
        task = self.get_task(task_id)
        if not task:
            return None
        
        if task["status"] in ["completed", "failed"]:
            return None
        
        # 返回下一个未完成的批次
        next_batch = task["completed_batches"]
        
        logger.info(f"🔄 恢复任务: {task_id} - 从批次 {next_batch} 开始")
        
        return next_batch
