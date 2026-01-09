"""
向量数据库管理器
支持 FAISS 和 ChromaDB
"""
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
import numpy as np
from pathlib import Path
import json
import pickle

class VectorStore:
    """向量数据库抽象类"""
    
    def __init__(self, store_type: str = "faiss", persist_path: str = "./vector_db"):
        """
        初始化向量数据库
        
        Args:
            store_type: 数据库类型 (faiss 或 chromadb)
            persist_path: 持久化路径
        """
        self.store_type = store_type
        self.persist_path = Path(persist_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        
        self.index = None
        self.documents = []  # 存储原始文档
        self.metadata = []   # 存储元数据
        
        logger.info(f"初始化向量数据库: {store_type}, 路径: {persist_path}")
        
        if store_type == "faiss":
            self._init_faiss()
        elif store_type == "chromadb":
            self._init_chromadb()
        else:
            raise ValueError(f"不支持的数据库类型: {store_type}")
    
    def _init_faiss(self):
        """初始化 FAISS"""
        try:
            import faiss
            self.faiss = faiss
            logger.info("FAISS 初始化成功")
        except ImportError:
            logger.error("FAISS 未安装，请运行: pip install faiss-cpu")
            raise
    
    def _init_chromadb(self):
        """初始化 ChromaDB"""
        try:
            import chromadb
            self.chromadb_client = chromadb.PersistentClient(path=str(self.persist_path))
            logger.info("ChromaDB 初始化成功")
        except ImportError:
            logger.error("ChromaDB 未安装，请运行: pip install chromadb")
            raise
    
    def add_documents(
        self, 
        documents: List[str], 
        embeddings: np.ndarray, 
        metadata: List[Dict] = None
    ):
        """
        添加文档到向量数据库
        
        Args:
            documents: 文档列表
            embeddings: 文档的向量表示 (n_docs, embedding_dim)
            metadata: 元数据列表
        """
        if len(documents) != len(embeddings):
            raise ValueError("文档数量与向量数量不匹配")
        
        if metadata is None:
            metadata = [{"doc_id": i} for i in range(len(documents))]
        
        if self.store_type == "faiss":
            self._add_to_faiss(documents, embeddings, metadata)
        elif self.store_type == "chromadb":
            self._add_to_chromadb(documents, embeddings, metadata)
        
        logger.info(f"添加 {len(documents)} 个文档到向量数据库")
    
    def _add_to_faiss(self, documents: List[str], embeddings: np.ndarray, metadata: List[Dict]):
        """添加到 FAISS"""
        embeddings = embeddings.astype('float32')
        
        if self.index is None:
            # 创建索引
            dimension = embeddings.shape[1]
            self.index = self.faiss.IndexFlatIP(dimension)  # 内积相似度
            # 归一化向量以使用余弦相似度
            self.faiss.normalize_L2(embeddings)
        
        # 添加向量
        self.index.add(embeddings)
        
        # 存储文档和元数据
        self.documents.extend(documents)
        self.metadata.extend(metadata)
    
    def _add_to_chromadb(self, documents: List[str], embeddings: np.ndarray, metadata: List[Dict]):
        """添加到 ChromaDB"""
        collection = self.chromadb_client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )
        
        # 生成 ID
        start_id = collection.count()
        ids = [f"doc_{start_id + i}" for i in range(len(documents))]
        
        # 添加文档
        collection.add(
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadata,
            ids=ids
        )
    
    def search(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        检索相似文档
        
        Args:
            query_embedding: 查询向量 (embedding_dim,)
            top_k: 返回前 k 个结果
            
        Returns:
            检索结果列表
        """
        if self.store_type == "faiss":
            return self._search_faiss(query_embedding, top_k)
        elif self.store_type == "chromadb":
            return self._search_chromadb(query_embedding, top_k)
    
    def _search_faiss(self, query_embedding: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """FAISS 检索"""
        if self.index is None or self.index.ntotal == 0:
            logger.warning("向量数据库为空")
            return []
        
        # 归一化查询向量
        query_embedding = query_embedding.astype('float32').reshape(1, -1)
        self.faiss.normalize_L2(query_embedding)
        
        # 检索
        distances, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
        
        # 构建结果
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.documents):
                results.append({
                    "document": self.documents[idx],
                    "metadata": self.metadata[idx],
                    "score": float(dist),
                    "index": int(idx)
                })
        
        return results
    
    def _search_chromadb(self, query_embedding: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """ChromaDB 检索"""
        collection = self.chromadb_client.get_collection(name="knowledge_base")
        
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )
        
        # 构建结果
        output = []
        for i in range(len(results['documents'][0])):
            output.append({
                "document": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "score": 1 - results['distances'][0][i],  # 转换为相似度
                "id": results['ids'][0][i]
            })
        
        return output
    
    def save(self, name: str = "default"):
        """保存向量数据库"""
        if self.store_type == "faiss":
            self._save_faiss(name)
        elif self.store_type == "chromadb":
            logger.info("ChromaDB 自动持久化，无需手动保存")
    
    def _save_faiss(self, name: str):
        """保存 FAISS 索引"""
        if self.index is None:
            logger.warning("索引为空，跳过保存")
            return
        
        # 保存索引
        index_path = self.persist_path / f"{name}.index"
        self.faiss.write_index(self.index, str(index_path))
        
        # 保存文档和元数据
        data_path = self.persist_path / f"{name}.pkl"
        with open(data_path, 'wb') as f:
            pickle.dump({
                "documents": self.documents,
                "metadata": self.metadata
            }, f)
        
        logger.info(f"FAISS 索引已保存: {index_path}")
    
    def load(self, name: str = "default"):
        """加载向量数据库"""
        if self.store_type == "faiss":
            self._load_faiss(name)
        elif self.store_type == "chromadb":
            logger.info("ChromaDB 自动加载，无需手动操作")
    
    def _load_faiss(self, name: str):
        """加载 FAISS 索引"""
        index_path = self.persist_path / f"{name}.index"
        data_path = self.persist_path / f"{name}.pkl"
        
        if not index_path.exists() or not data_path.exists():
            logger.warning(f"索引文件不存在: {name}")
            return
        
        # 加载索引
        self.index = self.faiss.read_index(str(index_path))
        
        # 加载文档和元数据
        with open(data_path, 'rb') as f:
            data = pickle.load(f)
            self.documents = data["documents"]
            self.metadata = data["metadata"]
        
        logger.info(f"FAISS 索引已加载: {index_path}, 文档数: {len(self.documents)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        if self.store_type == "faiss":
            return {
                "store_type": "faiss",
                "total_documents": len(self.documents),
                "index_size": self.index.ntotal if self.index else 0,
                "dimension": self.index.d if self.index else 0
            }
        elif self.store_type == "chromadb":
            collection = self.chromadb_client.get_collection(name="knowledge_base")
            return {
                "store_type": "chromadb",
                "total_documents": collection.count()
            }
    
    def clear(self):
        """清空数据库"""
        if self.store_type == "faiss":
            self.index = None
            self.documents = []
            self.metadata = []
            logger.info("FAISS 索引已清空")
        elif self.store_type == "chromadb":
            self.chromadb_client.delete_collection(name="knowledge_base")
            self.chromadb_client.create_collection(name="knowledge_base")
            logger.info("ChromaDB 集合已清空")


class KnowledgeBase:
    """知识库管理器"""
    
    def __init__(self, vector_store: VectorStore, embedding_model):
        """
        初始化知识库
        
        Args:
            vector_store: 向量数据库
            embedding_model: Embedding 模型
        """
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        logger.info("知识库管理器初始化完成")
    
    def add_knowledge(self, texts: List[str], metadata: List[Dict] = None):
        """
        添加知识到知识库
        
        Args:
            texts: 文本列表
            metadata: 元数据列表
        """
        logger.info(f"添加 {len(texts)} 条知识到知识库")
        
        # 生成 Embeddings
        embeddings = self.embedding_model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # 添加到向量数据库
        self.vector_store.add_documents(texts, embeddings, metadata)
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        检索相关知识
        
        Args:
            query: 查询文本
            top_k: 返回前 k 个结果
            
        Returns:
            检索结果
        """
        # 生成查询向量
        query_embedding = self.embedding_model.encode(
            [query],
            convert_to_numpy=True
        )[0]
        
        # 检索
        results = self.vector_store.search(query_embedding, top_k)
        
        logger.debug(f"检索到 {len(results)} 条相关知识")
        return results
    
    def batch_retrieve(self, queries: List[str], top_k: int = 5) -> List[List[Dict[str, Any]]]:
        """
        批量检索
        
        Args:
            queries: 查询列表
            top_k: 每个查询返回前 k 个结果
            
        Returns:
            检索结果列表
        """
        logger.info(f"批量检索 {len(queries)} 个查询")
        
        # 批量生成查询向量
        query_embeddings = self.embedding_model.encode(
            queries,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # 批量检索
        all_results = []
        for query_embedding in query_embeddings:
            results = self.vector_store.search(query_embedding, top_k)
            all_results.append(results)
        
        return all_results
    
    def save(self, name: str = "default"):
        """保存知识库"""
        self.vector_store.save(name)
    
    def load(self, name: str = "default"):
        """加载知识库"""
        self.vector_store.load(name)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.vector_store.get_stats()
