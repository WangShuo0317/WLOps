"""
配置文件
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """服务配置"""
    
    # 服务配置
    SERVICE_NAME = "data-analyzer-service"
    PORT = int(os.getenv("PORT", "8002"))
    HOST = os.getenv("HOST", "0.0.0.0")
    
    # OpenAI配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # Embedding模型配置
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cuda")  # cpu or cuda
    
    # 向量数据库配置
    VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "faiss")  # faiss or chromadb
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./vector_db")
    VECTOR_DB_COLLECTION = os.getenv("VECTOR_DB_COLLECTION", "knowledge_base")
    
    # 分析阈值
    HEALTH_SCORE_THRESHOLD = 70.0
    DISTRIBUTION_BIAS_THRESHOLD = 0.3  # 类别占比差异阈值
    SEMANTIC_SIMILARITY_THRESHOLD = 0.85
    
    # 聚类配置
    MIN_CLUSTER_SIZE = int(os.getenv("MIN_CLUSTER_SIZE", "5"))
    MIN_SAMPLES = int(os.getenv("MIN_SAMPLES", "3"))
    CLUSTER_SELECTION_EPSILON = float(os.getenv("CLUSTER_SELECTION_EPSILON", "0.0"))
    
    # 数据增强配置
    AUGMENTATION_RATIO = 0.2  # 增强样本占比
    MIN_SAMPLES_PER_CLASS = 50
    
    # COT配置
    COT_TEMPERATURE = 0.7
    COT_MAX_TOKENS = 500
    
    # RAG 校验配置
    RAG_RETRIEVAL_TOP_K = int(os.getenv("RAG_RETRIEVAL_TOP_K", "5"))
    RAG_CONFIDENCE_THRESHOLD = float(os.getenv("RAG_CONFIDENCE_THRESHOLD", "0.8"))
    RAG_ENABLE_SELF_CORRECTION = os.getenv("RAG_ENABLE_SELF_CORRECTION", "true").lower() == "true"
    
    # 事实提取配置
    FACT_EXTRACTION_TEMPERATURE = 0.3
    FACT_EXTRACTION_MAX_TOKENS = 1000
    
    # PII清洗配置
    PII_ENTITIES = ["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION", "CREDIT_CARD", "IP_ADDRESS"]
    PII_LANGUAGE = "zh"  # 支持中文
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # 输出配置
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./outputs")
    SAVE_DATASETS = os.getenv("SAVE_DATASETS", "true").lower() == "true"
    SAVE_REPORTS = os.getenv("SAVE_REPORTS", "true").lower() == "true"

config = Config()
