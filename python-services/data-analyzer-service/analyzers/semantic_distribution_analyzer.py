"""
语义分布分析器（合并版）
使用 Embedding + 自动聚类分析数据集的语义分布
"""
from typing import Dict, List, Any, Optional
from loguru import logger
import numpy as np
from collections import Counter
import json
from datetime import datetime

class SemanticDistributionAnalyzer:
    """语义分布分析器"""
    
    def __init__(self, embedding_model_name: str = None, min_cluster_size: int = 5, min_samples: int = 3):
        """
        初始化分析器
        
        Args:
            embedding_model_name: Embedding模型名称
            min_cluster_size: 最小聚类大小
            min_samples: 最小样本数
        """
        self.embedding_model_name = embedding_model_name or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载 Embedding 模型"""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"加载 Embedding 模型: {self.embedding_model_name}")
            self.model = SentenceTransformer(self.embedding_model_name)
            logger.info("Embedding 模型加载成功")
        except Exception as e:
            logger.error(f"Embedding 模型加载失败: {e}")
            self.model = None
    
    def analyze(self, dataset: List[Dict], save_report: bool = True, report_path: str = None) -> Dict[str, Any]:
        """
        分析数据集的语义分布
        
        Args:
            dataset: 数据集
            save_report: 是否保存报告
            report_path: 报告保存路径
            
        Returns:
            分析报告
        """
        logger.info(f"开始语义分布分析，数据集大小: {len(dataset)}")
        
        if not self.model:
            logger.error("Embedding 模型未加载，无法进行分析")
            return self._generate_error_report("Embedding 模型未加载")
        
        # 1. 提取问题文本
        questions, indices = self._extract_questions(dataset)
        
        if not questions:
            logger.error("未能提取到问题文本")
            return self._generate_error_report("未能提取到问题文本")
        
        logger.info(f"提取到 {len(questions)} 个问题")
        
        # 2. 生成 Embeddings
        embeddings = self._generate_embeddings(questions)
        
        # 3. 自动聚类
        cluster_labels, n_clusters = self._auto_clustering(embeddings)
        
        # 4. 分析聚类结果
        cluster_analysis = self._analyze_clusters(questions, cluster_labels, n_clusters, dataset, indices)
        
        # 5. 计算分布均衡度
        balance_metrics = self._calculate_balance_metrics(cluster_labels, n_clusters)
        
        # 6. 识别问题和建议
        issues, recommendations = self._identify_issues(cluster_analysis, balance_metrics)
        
        # 7. 生成完整报告
        report = self._generate_report(
            dataset_size=len(dataset),
            n_questions=len(questions),
            n_clusters=n_clusters,
            cluster_analysis=cluster_analysis,
            balance_metrics=balance_metrics,
            issues=issues,
            recommendations=recommendations,
            embeddings=embeddings,
            cluster_labels=cluster_labels
        )
        
        # 8. 保存报告
        if save_report:
            report_path = report_path or f"semantic_distribution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self._save_report(report, report_path)
        
        logger.info(f"语义分布分析完成，发现 {n_clusters} 个聚类")
        
        return report
    
    def _extract_questions(self, dataset: List[Dict]) -> tuple[List[str], List[int]]:
        """提取问题文本"""
        questions = []
        indices = []
        
        question_fields = ["question", "input", "prompt", "query", "text"]
        
        for idx, item in enumerate(dataset):
            question = None
            for field in question_fields:
                if field in item and item[field]:
                    question = str(item[field]).strip()
                    break
            
            if question:
                questions.append(question)
                indices.append(idx)
        
        return questions, indices
    
    def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """生成文本 Embeddings"""
        logger.info("生成 Embeddings...")
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            logger.info(f"Embeddings 生成完成，形状: {embeddings.shape}")
            return embeddings
        except Exception as e:
            logger.error(f"Embeddings 生成失败: {e}")
            raise
    
    def _auto_clustering(self, embeddings: np.ndarray) -> tuple[np.ndarray, int]:
        """
        自动聚类（使用 HDBSCAN）
        
        Returns:
            (聚类标签, 聚类数量)
        """
        logger.info("执行自动聚类...")
        
        try:
            import hdbscan
            from umap import UMAP
            
            # 1. 降维（UMAP）
            logger.info("使用 UMAP 降维...")
            reducer = UMAP(
                n_neighbors=15,
                n_components=5,
                metric='cosine',
                random_state=42
            )
            reduced_embeddings = reducer.fit_transform(embeddings)
            
            # 2. 聚类（HDBSCAN）
            logger.info("使用 HDBSCAN 聚类...")
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=self.min_samples,
                metric='euclidean',
                cluster_selection_epsilon=0.0,
                cluster_selection_method='eom'
            )
            cluster_labels = clusterer.fit_predict(reduced_embeddings)
            
            # 计算聚类数量（-1 表示噪声点）
            n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
            n_noise = list(cluster_labels).count(-1)
            
            logger.info(f"聚类完成: {n_clusters} 个聚类, {n_noise} 个噪声点")
            
            return cluster_labels, n_clusters
            
        except Exception as e:
            logger.error(f"聚类失败: {e}")
            # 降级方案：使用 KMeans
            return self._fallback_clustering(embeddings)
    
    def _fallback_clustering(self, embeddings: np.ndarray) -> tuple[np.ndarray, int]:
        """降级聚类方案（KMeans）"""
        logger.warning("使用降级聚类方案: KMeans")
        
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score
        
        # 自动确定最佳聚类数
        best_k = 5
        best_score = -1
        
        for k in range(3, min(11, len(embeddings) // 10)):
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
            score = silhouette_score(embeddings, labels)
            
            if score > best_score:
                best_score = score
                best_k = k
        
        logger.info(f"最佳聚类数: {best_k}, 轮廓系数: {best_score:.3f}")
        
        kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings)
        
        return cluster_labels, best_k
    
    def _analyze_clusters(
        self, 
        questions: List[str], 
        cluster_labels: np.ndarray, 
        n_clusters: int,
        dataset: List[Dict],
        indices: List[int]
    ) -> List[Dict[str, Any]]:
        """分析每个聚类"""
        logger.info("分析聚类特征...")
        
        cluster_analysis = []
        
        for cluster_id in range(n_clusters):
            # 获取该聚类的样本
            cluster_mask = cluster_labels == cluster_id
            cluster_questions = [q for q, m in zip(questions, cluster_mask) if m]
            cluster_indices = [idx for idx, m in zip(indices, cluster_mask) if m]
            
            # 提取该聚类的数据集样本
            cluster_samples = [dataset[idx] for idx in cluster_indices]
            
            # 分析聚类特征
            analysis = {
                "cluster_id": int(cluster_id),
                "size": len(cluster_questions),
                "percentage": len(cluster_questions) / len(questions) * 100,
                "sample_questions": cluster_questions[:5],  # 前5个示例
                "characteristics": self._extract_cluster_characteristics(cluster_questions),
                "statistics": self._calculate_cluster_statistics(cluster_samples),
                "representative_samples": self._find_representative_samples(cluster_questions, cluster_samples, 3)
            }
            
            cluster_analysis.append(analysis)
        
        # 处理噪声点
        if -1 in cluster_labels:
            noise_mask = cluster_labels == -1
            noise_questions = [q for q, m in zip(questions, noise_mask) if m]
            
            cluster_analysis.append({
                "cluster_id": -1,
                "size": len(noise_questions),
                "percentage": len(noise_questions) / len(questions) * 100,
                "sample_questions": noise_questions[:5],
                "characteristics": {"type": "noise", "description": "未能归入任何聚类的样本"},
                "statistics": {},
                "representative_samples": []
            })
        
        # 按大小排序
        cluster_analysis.sort(key=lambda x: x["size"], reverse=True)
        
        return cluster_analysis
    
    def _extract_cluster_characteristics(self, questions: List[str]) -> Dict[str, Any]:
        """提取聚类特征"""
        # 统计长度
        lengths = [len(q) for q in questions]
        avg_length = np.mean(lengths)
        
        # 统计关键词
        all_text = " ".join(questions).lower()
        
        characteristics = {
            "avg_length": float(avg_length),
            "length_range": [int(min(lengths)), int(max(lengths))],
            "keywords": self._extract_keywords(questions),
            "question_types": self._identify_question_types(questions)
        }
        
        return characteristics
    
    def _extract_keywords(self, questions: List[str], top_k: int = 5) -> List[str]:
        """提取关键词"""
        # 简单的词频统计
        from collections import Counter
        import re
        
        # 中文分词（简单版）
        words = []
        for q in questions:
            # 提取中文词和英文单词
            chinese_words = re.findall(r'[\u4e00-\u9fa5]+', q)
            english_words = re.findall(r'[a-zA-Z]+', q.lower())
            words.extend(chinese_words)
            words.extend(english_words)
        
        # 过滤停用词
        stopwords = {'的', '了', '是', '在', '有', '和', '个', '我', '你', '他', '她', '它', 
                     'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been'}
        words = [w for w in words if w not in stopwords and len(w) > 1]
        
        # 统计词频
        word_counts = Counter(words)
        
        return [word for word, count in word_counts.most_common(top_k)]
    
    def _identify_question_types(self, questions: List[str]) -> Dict[str, int]:
        """识别问题类型"""
        types = {
            "计算题": 0,
            "应用题": 0,
            "概念题": 0,
            "推理题": 0,
            "其他": 0
        }
        
        for q in questions:
            q_lower = q.lower()
            
            if any(op in q for op in ['+', '-', '×', '÷', '*', '/', '=', '加', '减', '乘', '除']):
                types["计算题"] += 1
            elif any(word in q for word in ['应用', '实际', '场景', '情境', '小明', '小红']):
                types["应用题"] += 1
            elif any(word in q for word in ['什么是', '定义', '概念', '含义', '解释']):
                types["概念题"] += 1
            elif any(word in q for word in ['为什么', '如何', '推导', '证明', '分析']):
                types["推理题"] += 1
            else:
                types["其他"] += 1
        
        return types
    
    def _calculate_cluster_statistics(self, samples: List[Dict]) -> Dict[str, Any]:
        """计算聚类统计信息"""
        stats = {
            "total_samples": len(samples),
            "has_answer": 0,
            "has_reasoning": 0,
            "avg_answer_length": 0
        }
        
        answer_lengths = []
        
        for sample in samples:
            # 检查是否有答案
            if any(k in sample for k in ["answer", "output", "response"]):
                stats["has_answer"] += 1
                answer = self._get_field_value(sample, ["answer", "output", "response"])
                if answer:
                    answer_lengths.append(len(str(answer)))
            
            # 检查是否有推理过程
            if any(k in sample for k in ["reasoning", "rationale", "explanation", "cot"]):
                stats["has_reasoning"] += 1
        
        if answer_lengths:
            stats["avg_answer_length"] = float(np.mean(answer_lengths))
        
        return stats
    
    def _find_representative_samples(self, questions: List[str], samples: List[Dict], n: int = 3) -> List[Dict]:
        """找出代表性样本"""
        # 简单选择：取前n个
        representative = []
        for i, (q, s) in enumerate(zip(questions[:n], samples[:n])):
            representative.append({
                "question": q,
                "answer": self._get_field_value(s, ["answer", "output", "response"]),
                "index": i
            })
        
        return representative
    
    def _calculate_balance_metrics(self, cluster_labels: np.ndarray, n_clusters: int) -> Dict[str, Any]:
        """计算分布均衡度指标"""
        cluster_counts = Counter(cluster_labels)
        
        # 排除噪声点
        if -1 in cluster_counts:
            noise_count = cluster_counts.pop(-1)
        else:
            noise_count = 0
        
        if not cluster_counts:
            return {
                "is_balanced": False,
                "imbalance_ratio": 1.0,
                "gini_coefficient": 1.0,
                "entropy": 0.0,
                "noise_ratio": 1.0
            }
        
        counts = list(cluster_counts.values())
        total = sum(counts)
        
        # 不平衡比率
        max_count = max(counts)
        min_count = min(counts)
        imbalance_ratio = 1.0 - (min_count / max_count) if max_count > 0 else 0.0
        
        # 基尼系数
        gini = self._calculate_gini(counts)
        
        # 熵
        entropy = self._calculate_entropy(counts)
        
        # 噪声比率
        noise_ratio = noise_count / (total + noise_count) if (total + noise_count) > 0 else 0.0
        
        # 判断是否均衡
        is_balanced = imbalance_ratio < 0.5 and gini < 0.4 and noise_ratio < 0.1
        
        return {
            "is_balanced": is_balanced,
            "imbalance_ratio": float(imbalance_ratio),
            "gini_coefficient": float(gini),
            "entropy": float(entropy),
            "noise_ratio": float(noise_ratio),
            "max_cluster_size": int(max_count),
            "min_cluster_size": int(min_count),
            "avg_cluster_size": float(np.mean(counts)),
            "std_cluster_size": float(np.std(counts))
        }
    
    def _calculate_gini(self, counts: List[int]) -> float:
        """计算基尼系数"""
        if not counts:
            return 0.0
        
        sorted_counts = sorted(counts)
        n = len(sorted_counts)
        cumsum = np.cumsum(sorted_counts)
        
        return (2 * np.sum((np.arange(1, n + 1)) * sorted_counts)) / (n * cumsum[-1]) - (n + 1) / n
    
    def _calculate_entropy(self, counts: List[int]) -> float:
        """计算熵"""
        if not counts:
            return 0.0
        
        total = sum(counts)
        probs = [c / total for c in counts]
        
        return -sum(p * np.log2(p) for p in probs if p > 0)
    
    def _identify_issues(self, cluster_analysis: List[Dict], balance_metrics: Dict) -> tuple[List[str], List[str]]:
        """识别问题和生成建议"""
        issues = []
        recommendations = []
        
        # 检查均衡性
        if not balance_metrics["is_balanced"]:
            issues.append(f"数据分布不均衡，不平衡比率: {balance_metrics['imbalance_ratio']:.2f}")
            recommendations.append("建议对小类别进行数据增强，平衡各聚类的样本数量")
        
        # 检查噪声比率
        if balance_metrics["noise_ratio"] > 0.1:
            issues.append(f"噪声样本过多，占比: {balance_metrics['noise_ratio']*100:.1f}%")
            recommendations.append("建议检查噪声样本的质量，可能需要清洗或重新标注")
        
        # 检查小聚类
        small_clusters = [c for c in cluster_analysis if c["cluster_id"] != -1 and c["size"] < 10]
        if small_clusters:
            issues.append(f"存在 {len(small_clusters)} 个小聚类（样本数<10）")
            recommendations.append("建议为小聚类生成更多相似样本，或考虑合并相似的小聚类")
        
        # 检查大聚类
        if cluster_analysis and cluster_analysis[0]["percentage"] > 50:
            issues.append(f"最大聚类占比过高: {cluster_analysis[0]['percentage']:.1f}%")
            recommendations.append("建议增加其他类型样本的多样性，避免模型过拟合")
        
        # 检查推理覆盖
        total_samples = sum(c["statistics"].get("total_samples", 0) for c in cluster_analysis if c["cluster_id"] != -1)
        total_reasoning = sum(c["statistics"].get("has_reasoning", 0) for c in cluster_analysis if c["cluster_id"] != -1)
        
        if total_samples > 0:
            reasoning_ratio = total_reasoning / total_samples
            if reasoning_ratio < 0.3:
                issues.append(f"推理过程覆盖率低: {reasoning_ratio*100:.1f}%")
                recommendations.append("建议使用 COT 重写功能为样本补充推理链")
        
        return issues, recommendations
    
    def _generate_report(
        self,
        dataset_size: int,
        n_questions: int,
        n_clusters: int,
        cluster_analysis: List[Dict],
        balance_metrics: Dict,
        issues: List[str],
        recommendations: List[str],
        embeddings: np.ndarray,
        cluster_labels: np.ndarray
    ) -> Dict[str, Any]:
        """生成完整报告"""
        report = {
            "report_metadata": {
                "report_type": "semantic_distribution_analysis",
                "generated_at": datetime.now().isoformat(),
                "analyzer_version": "2.0.0",
                "embedding_model": self.embedding_model_name
            },
            "dataset_summary": {
                "total_samples": dataset_size,
                "analyzed_questions": n_questions,
                "coverage": n_questions / dataset_size if dataset_size > 0 else 0
            },
            "clustering_results": {
                "n_clusters": n_clusters,
                "clustering_method": "HDBSCAN + UMAP",
                "embedding_dimension": int(embeddings.shape[1])
            },
            "cluster_analysis": cluster_analysis,
            "balance_metrics": balance_metrics,
            "issues": issues,
            "recommendations": recommendations,
            "summary": {
                "health_score": self._calculate_distribution_health_score(balance_metrics, issues),
                "is_balanced": balance_metrics["is_balanced"],
                "needs_augmentation": len([c for c in cluster_analysis if c["cluster_id"] != -1 and c["size"] < 20]) > 0,
                "needs_cleaning": balance_metrics["noise_ratio"] > 0.1
            }
        }
        
        return report
    
    def _calculate_distribution_health_score(self, balance_metrics: Dict, issues: List[str]) -> float:
        """计算分布健康度评分"""
        score = 100.0
        
        # 不平衡惩罚
        score -= balance_metrics["imbalance_ratio"] * 30
        
        # 基尼系数惩罚
        score -= balance_metrics["gini_coefficient"] * 20
        
        # 噪声惩罚
        score -= balance_metrics["noise_ratio"] * 30
        
        # 问题数量惩罚
        score -= len(issues) * 5
        
        return max(0.0, min(100.0, score))
    
    def _save_report(self, report: Dict, path: str):
        """保存报告为 JSON"""
        try:
            # 移除不可序列化的数据
            report_copy = report.copy()
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(report_copy, f, ensure_ascii=False, indent=2)
            
            logger.info(f"报告已保存至: {path}")
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
    
    def _generate_error_report(self, error_message: str) -> Dict[str, Any]:
        """生成错误报告"""
        return {
            "report_metadata": {
                "report_type": "semantic_distribution_analysis",
                "generated_at": datetime.now().isoformat(),
                "status": "error"
            },
            "error": error_message,
            "cluster_analysis": [],
            "balance_metrics": {},
            "issues": [error_message],
            "recommendations": ["请检查数据集格式和 Embedding 模型配置"]
        }
    
    def _get_field_value(self, item: Dict, field_names: List[str]) -> Any:
        """获取字段值"""
        for field in field_names:
            if field in item:
                return item[field]
        return None
