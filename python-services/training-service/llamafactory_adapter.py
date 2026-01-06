"""
LLaMA Factory 适配器
封装LLaMA Factory训练功能
"""
import os
import subprocess
import threading
from typing import Dict, Any
from pathlib import Path
from loguru import logger
import yaml


class LLaMAFactoryAdapter:
    """LLaMA Factory适配器"""
    
    def __init__(self, llamafactory_path: str):
        self.llamafactory_path = Path(llamafactory_path)
        self.running_jobs = {}
        self.job_lock = threading.Lock()
        
        if not self.llamafactory_path.exists():
            raise ValueError(f"LLaMA Factory路径不存在: {llamafactory_path}")
        
        logger.info(f"LLaMA Factory适配器初始化: {llamafactory_path}")
    
    def create_training_config(self, job_config: Dict[str, Any]) -> str:
        """创建训练配置"""
        config = {
            "model_name_or_path": job_config.get("model_name"),
            "stage": job_config.get("stage", "sft"),
            "do_train": True,
            "finetuning_type": job_config.get("finetuning_type", "lora"),
            "dataset": job_config.get("dataset"),
            "template": "default",
            "cutoff_len": 1024,
            "lora_rank": job_config.get("lora_rank", 8),
            "lora_alpha": job_config.get("lora_alpha", 16),
            "per_device_train_batch_size": job_config.get("batch_size", 2),
            "learning_rate": job_config.get("learning_rate", 5e-5),
            "num_train_epochs": job_config.get("epochs", 3.0),
            "max_steps": job_config.get("max_steps", -1),
            "output_dir": job_config.get("output_dir"),
            "logging_steps": 10,
            "save_steps": 500,
            "bf16": True,
        }
        
        job_id = job_config.get("job_id")
        config_dir = Path(f"./configs/{job_id}")
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "config.yaml"
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        logger.info(f"配置已保存: {config_path}")
        return str(config_path)
    
    def start_training(self, job_id: str, config_path: str) -> bool:
        """启动训练"""
        try:
            train_script = self.llamafactory_path / "src" / "train.py"
            cmd = ["python", str(train_script), "--config", config_path]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            with self.job_lock:
                self.running_jobs[job_id] = {
                    "process": process,
                    "status": "running",
                    "pid": process.pid
                }
            
            threading.Thread(
                target=self._monitor_logs,
                args=(job_id, process),
                daemon=True
            ).start()
            
            logger.info(f"训练任务已启动: {job_id}, PID: {process.pid}")
            return True
        except Exception as e:
            logger.error(f"启动训练失败: {e}")
            return False
    
    def _monitor_logs(self, job_id: str, process: subprocess.Popen):
        """监控日志"""
        log_dir = Path(f"./logs/{job_id}")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        with open(log_dir / "training.log", 'w') as f:
            for line in process.stdout:
                f.write(line)
                f.flush()
        
        return_code = process.wait()
        
        with self.job_lock:
            if job_id in self.running_jobs:
                self.running_jobs[job_id]["status"] = "completed" if return_code == 0 else "failed"
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        with self.job_lock:
            if job_id not in self.running_jobs:
                return {"status": "not_found"}
            
            job = self.running_jobs[job_id]
            return {
                "job_id": job_id,
                "status": job.get("status"),
                "pid": job.get("pid")
            }
    
    def stop_training(self, job_id: str) -> bool:
        """停止训练"""
        with self.job_lock:
            if job_id not in self.running_jobs:
                return False
            
            process = self.running_jobs[job_id]["process"]
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=30)
                self.running_jobs[job_id]["status"] = "stopped"
                return True
            return False
