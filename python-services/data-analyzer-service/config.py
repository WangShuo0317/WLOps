"""
配置文件
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """配置类"""
    
    # 服务配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8001))
    
    # LLM 配置
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))
    
    # Embedding 配置
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    # 存储配置
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./outputs")
    SAVE_DATASETS = os.getenv("SAVE_DATASETS", "true").lower() == "true"
    SAVE_REPORTS = os.getenv("SAVE_REPORTS", "true").lower() == "true"
    
    # Redis 配置
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}" if REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    
    # Celery 配置
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
    
    # 分片配置
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", 50))  # 每批处理的样本数
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", 4))  # 最大并发 Worker 数
    
    # 任务配置
    TASK_TIMEOUT = int(os.getenv("TASK_TIMEOUT", 3600))  # 任务超时时间（秒）
    TASK_RETRY_LIMIT = int(os.getenv("TASK_RETRY_LIMIT", 3))  # 任务重试次数


config = Config()
