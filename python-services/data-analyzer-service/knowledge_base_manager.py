"""
知识库管理器
管理向量数据库和知识检索
"""
from typing import List, Dict, Any
from loguru import logger
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from config import config


class KnowledgeBaseManager:
    """知识库管理器"""
    
    def __init__(self, embedding_model: SentenceTransformer):
        """
        初始化知识库
        
        Args:
            embedding_model: Embedding 模型
        """
        self.embedding_model = embedding_model
        self.dimension = embedding_model.get_sentence_embedding_dimension()
        
        # 初始化 FAISS 索引
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # 存储原始文本
        self.documents = []
        
        logger.info(f"知识库初始化完成，维度: {self.dimension}")
    
    def add_knowledge(self, texts: List[str], metadata: List[Dict] = None):
        """
        添加知识到知识库
        
        Args:
            texts: 知识文本列表
            metadata: 元数据列表（可选）
        """
        if not texts:
            return
        
        logger.info(f"添加 {len(texts)} 条知识到知识库...")
        
        # 生成 embeddings
        embeddings = self.embedding_model.encode(
            texts,
            batch_size=config.EMBEDDING_BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        # 添加到 FAISS 索引
        self.index.add(embeddings.astype('float32'))
        
        # 存储原始文本和元数据
        for i, text in enumerate(texts):
            doc = {
                "text": text,
                "metadata": metadata[i] if metadata and i < len(metadata) else {}
            }
            self.documents.append(doc)
        
        logger.info(f"知识库当前大小: {len(self.documents)} 条")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        检索相关知识
        
        Args:
            query: 查询文本
            top_k: 返回前 k 个结果
            
        Returns:
            相关文档列表
        """
        if len(self.documents) == 0:
            return []
        
        # 生成查询 embedding
        query_embedding = self.embedding_model.encode(
            [query],
            convert_to_numpy=True
        ).astype('float32')
        
        # 搜索
        top_k = min(top_k, len(self.documents))
        distances, indices = self.index.search(query_embedding, top_k)
        
        # 构建结果
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc["score"] = float(distances[0][i])
                results.append(doc)
        
        return results
    
    def clear(self):
        """清空知识库"""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        logger.info("知识库已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        return {
            "total_documents": len(self.documents),
            "dimension": self.dimension,
            "index_size": self.index.ntotal
        }
