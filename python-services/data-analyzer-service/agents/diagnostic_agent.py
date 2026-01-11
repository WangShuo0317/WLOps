"""
诊断智能体
负责识别数据集中的问题：稀缺样本和低质量样本
"""
from typing import Dict, List, Any
from loguru import logger
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.cluster import HDBSCAN
import umap

from config import config


class DiagnosticAgent:
    """诊断智能体"""
    
    def __init__(self, embedding_model: SentenceTransformer):
        self.embedding_model = embedding_model
    
    def diagnose_full(self, dataset: List[Dict]) -> Dict[str, Any]:
        """
        全面诊断（标注流程优化模式）
        
        1. 语义分布分析 - 识别稀缺聚类
        2. 推理质量分析 - 识别低质量样本（仅当数据包含 think 字段时）
        """
        logger.info("执行全面诊断...")
        
        # 检查数据集是否包含 think 字段（不区分大小写）
        has_think_field = self._check_has_think_field(dataset)
        
        # 1. 语义分布分析
        sparse_clusters = self._analyze_semantic_distribution(dataset)
        
        # 2. 推理质量分析（仅当有 think 字段时）
        low_quality_samples = []
        if has_think_field:
            logger.info("  检测到 think 字段，执行推理质量分析...")
            low_quality_samples = self._analyze_reasoning_quality(dataset)
        else:
            logger.info("  未检测到 think 字段，跳过推理质量分析")
        
        report = {
            "total_samples": len(dataset),
            "sparse_clusters_count": len(sparse_clusters),
            "low_quality_count": len(low_quality_samples),
            "analysis_type": "full",
            "has_think_field": has_think_field
        }
        
        return {
            "sparse_clusters": sparse_clusters,
            "low_quality_samples": low_quality_samples,
            "report": report
        }
    
    def diagnose_guided(
        self, 
        dataset: List[Dict], 
        guidance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        指导诊断（指定优化模式）
        
        根据优化指导诊断特定问题
        """
        logger.info("根据优化指导执行诊断...")
        
        focus_areas = guidance.get("focus_areas", [])
        sparse_clusters = []
        low_quality_samples = []
        
        # 检查数据集是否包含 think 字段
        has_think_field = self._check_has_think_field(dataset)
        
        # 根据指导的关注点进行诊断
        if "semantic_distribution" in focus_areas:
            sparse_clusters = self._analyze_semantic_distribution(dataset)
        
        if "reasoning_quality" in focus_areas:
            if has_think_field:
                logger.info("  检测到 think 字段，执行推理质量分析...")
                low_quality_samples = self._analyze_reasoning_quality(dataset)
            else:
                logger.warning("  未检测到 think 字段，跳过推理质量分析")
        
        # 如果指导中指定了特定的问题样本
        if "problem_indices" in guidance:
            for idx in guidance["problem_indices"]:
                if idx < len(dataset):
                    low_quality_samples.append({
                        "index": idx,
                        "sample": dataset[idx],
                        "issue": "guided_selection"
                    })
        
        report = {
            "total_samples": len(dataset),
            "sparse_clusters_count": len(sparse_clusters),
            "low_quality_count": len(low_quality_samples),
            "analysis_type": "guided",
            "focus_areas": focus_areas,
            "has_think_field": has_think_field
        }
        
        return {
            "sparse_clusters": sparse_clusters,
            "low_quality_samples": low_quality_samples,
            "report": report
        }
    
    def _analyze_semantic_distribution(self, dataset: List[Dict]) -> List[Dict]:
        """
        语义分布分析 - 识别稀缺聚类
        
        使用 HDBSCAN 聚类识别样本分布稀疏的区域
        """
        logger.info("  分析语义分布...")
        
        if len(dataset) < 10:
            logger.warning("  数据集太小，跳过语义分布分析")
            return []
        
        # 提取文本
        texts = []
        for sample in dataset:
            # 尝试多个可能的字段
            text = (
                sample.get("question", "") or 
                sample.get("instruction", "") or 
                sample.get("input", "") or
                str(sample)
            )
            texts.append(text)
        
        # 生成 embeddings
        logger.info(f"  生成 {len(texts)} 个样本的 embeddings...")
        embeddings = self.embedding_model.encode(
            texts, 
            batch_size=config.EMBEDDING_BATCH_SIZE,
            show_progress_bar=False
        )
        
        # 降维
        logger.info("  降维...")
        reducer = umap.UMAP(
            n_neighbors=min(15, len(dataset) - 1),
            n_components=min(5, len(dataset) - 1),
            metric='cosine',
            random_state=42
        )
        reduced_embeddings = reducer.fit_transform(embeddings)
        
        # 聚类
        logger.info("  聚类...")
        clusterer = HDBSCAN(
            min_cluster_size=max(3, config.MIN_CLUSTER_SIZE),
            min_samples=config.MIN_SAMPLES,
            metric='euclidean'
        )
        cluster_labels = clusterer.fit_predict(reduced_embeddings)
        
        # 识别稀缺聚类（样本数 < 20）
        sparse_clusters = []
        unique_labels = set(cluster_labels)
        
        for label in unique_labels:
            if label == -1:  # 跳过噪声
                continue
            
            cluster_indices = np.where(cluster_labels == label)[0]
            cluster_size = len(cluster_indices)
            
            if cluster_size < 20:  # 稀缺阈值
                # 提取聚类特征
                cluster_samples = [dataset[i] for i in cluster_indices[:3]]
                
                sparse_clusters.append({
                    "cluster_id": int(label),
                    "size": cluster_size,
                    "indices": cluster_indices.tolist(),
                    "sample_questions": [
                        s.get("question", s.get("instruction", "")) 
                        for s in cluster_samples
                    ],
                    "characteristics": f"稀缺聚类 {label}"
                })
        
        logger.info(f"  识别到 {len(sparse_clusters)} 个稀缺聚类")
        
        return sparse_clusters
    
    def _check_has_think_field(self, dataset: List[Dict]) -> bool:
        """
        检查数据集是否包含 think 字段（不区分大小写）
        
        只要有一个样本包含 think 字段，就认为整个数据集需要推理质量分析
        """
        if not dataset:
            return False
        
        # 检查前几个样本（最多检查10个）
        sample_size = min(10, len(dataset))
        
        for sample in dataset[:sample_size]:
            # 检查所有键（不区分大小写）
            for key in sample.keys():
                if key.lower() == 'think':
                    logger.info(f"  检测到 think 字段: '{key}'")
                    return True
        
        return False
    
    def _analyze_reasoning_quality(self, dataset: List[Dict]) -> List[Dict]:
        """
        推理质量分析 - 识别低质量样本
        
        检查样本是否包含推理过程（COT）
        """
        logger.info("  分析推理质量...")
        
        low_quality_samples = []
        
        # 推理字段的可能名称
        reasoning_fields = [
            "reasoning", "rationale", "explanation", 
            "steps", "cot", "chain_of_thought", "思考过程"
        ]
        
        for idx, sample in enumerate(dataset):
            # 检查是否有推理字段
            has_reasoning = any(
                field in sample and sample[field] 
                for field in reasoning_fields
            )
            
            # 检查回答是否过短（可能缺少详细推理）
            answer = sample.get("answer", sample.get("output", ""))
            is_too_short = len(str(answer)) < 50
            
            if not has_reasoning or is_too_short:
                low_quality_samples.append({
                    "index": idx,
                    "sample": sample,
                    "issue": "missing_cot" if not has_reasoning else "short_answer"
                })
        
        logger.info(f"  识别到 {len(low_quality_samples)} 个低质量样本")
        
        return low_quality_samples
