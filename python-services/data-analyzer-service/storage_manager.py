"""
存储管理器
负责保存优化后的数据集和分析报告
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from loguru import logger

from config import config


class StorageManager:
    """存储管理器"""
    
    def __init__(self, output_dir: str = "./outputs"):
        """
        初始化存储管理器
        
        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.datasets_dir = self.output_dir / "datasets"
        self.reports_dir = self.output_dir / "reports"
        
        # 创建目录
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"存储管理器初始化完成，输出目录: {self.output_dir}")
    
    def save_optimized_dataset(
        self,
        task_id: str,
        dataset: List[Dict[str, Any]],
        statistics: Dict[str, Any],
        mode: str = "auto"
    ) -> str:
        """
        保存优化后的数据集
        
        Args:
            task_id: 任务ID
            dataset: 优化后的数据集
            statistics: 统计信息
            mode: 优化模式
            
        Returns:
            保存的文件路径
        """
        try:
            # 创建任务目录
            task_dir = self.datasets_dir / task_id
            task_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存数据集
            dataset_file = task_dir / "optimized_dataset.json"
            with open(dataset_file, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, ensure_ascii=False, indent=2)
            
            # 保存元数据
            metadata = {
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "mode": mode,
                "dataset_size": len(dataset),
                "statistics": statistics
            }
            metadata_file = task_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 数据集已保存: {dataset_file}")
            logger.info(f"   - 样本数: {len(dataset)}")
            logger.info(f"   - 模式: {mode}")
            
            return str(dataset_file)
            
        except Exception as e:
            logger.error(f"❌ 保存数据集失败: {e}")
            raise
    
    def save_analysis_report(
        self,
        task_id: str,
        diagnostic_report: Dict[str, Any],
        statistics: Dict[str, Any],
        mode: str = "auto"
    ) -> str:
        """
        保存分析报告
        
        Args:
            task_id: 任务ID
            diagnostic_report: 诊断报告
            statistics: 统计信息
            mode: 优化模式
            
        Returns:
            保存的目录路径
        """
        try:
            # 创建任务目录
            task_dir = self.reports_dir / task_id
            task_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存诊断报告
            diagnostic_file = task_dir / "diagnostic_report.json"
            with open(diagnostic_file, 'w', encoding='utf-8') as f:
                json.dump(diagnostic_report, f, ensure_ascii=False, indent=2)
            
            # 保存统计信息
            stats_file = task_dir / "statistics.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(statistics, f, ensure_ascii=False, indent=2)
            
            # 生成可读的摘要报告
            summary_file = task_dir / "summary.md"
            summary_content = self._generate_summary_markdown(
                task_id, diagnostic_report, statistics, mode
            )
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary_content)
            
            logger.info(f"✅ 分析报告已保存: {task_dir}")
            
            return str(task_dir)
            
        except Exception as e:
            logger.error(f"❌ 保存分析报告失败: {e}")
            raise
    
    def _generate_summary_markdown(
        self,
        task_id: str,
        diagnostic_report: Dict[str, Any],
        statistics: Dict[str, Any],
        mode: str
    ) -> str:
        """生成可读的摘要报告（Markdown格式）"""
        
        opt_stats = statistics.get("optimization_stats", {})
        ver_stats = statistics.get("verification_stats", {})
        
        summary = f"""# 数据优化报告

## 基本信息

- **任务ID**: {task_id}
- **生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **优化模式**: {mode} ({'标注流程优化' if mode == 'auto' else '指定优化'})
- **数据类型**: {'推理数据（包含 think 字段）' if diagnostic_report.get('has_think_field', False) else '普通 QA 数据'}

## 数据统计

### 输入输出
- **输入样本数**: {statistics.get('input_size', 0)}
- **输出样本数**: {statistics.get('output_size', 0)}
- **增长率**: {((statistics.get('output_size', 0) - statistics.get('input_size', 0)) / statistics.get('input_size', 1) * 100):.1f}%

### 诊断结果
- **稀缺聚类数**: {diagnostic_report.get('sparse_clusters_count', 0)}
- **低质量样本数**: {diagnostic_report.get('low_quality_count', 0)}
{'- **推理质量分析**: 已执行' if diagnostic_report.get('has_think_field', False) else '- **推理质量分析**: 跳过（无 think 字段）'}

### 优化统计
- **优化样本数**: {opt_stats.get('optimized_count', 0)}
- **生成样本数**: {opt_stats.get('generated_count', 0)}
- **保留高质量样本**: {opt_stats.get('high_quality_kept', 0)}
{'- **COT 重写**: 已执行' if diagnostic_report.get('has_think_field', False) else '- **COT 重写**: 跳过（无 think 字段）'}

### RAG校验统计
- **总计**: {ver_stats.get('total', 0)}
- **通过**: {ver_stats.get('passed', 0)} ({ver_stats.get('pass_rate', 0)*100:.1f}%)
- **修正**: {ver_stats.get('corrected', 0)} ({ver_stats.get('correction_rate', 0)*100:.1f}%)
- **拒绝**: {ver_stats.get('rejected', 0)} ({ver_stats.get('rejection_rate', 0)*100:.1f}%)

### PII清洗
- **清洗样本数**: {statistics.get('pii_cleaned_count', 0)}

## 工作流执行

1. ✅ **Module 1: 诊断** - 识别问题样本
   - 语义分布分析: 已执行
   - 推理质量分析: {'已执行' if diagnostic_report.get('has_think_field', False) else '跳过（无 think 字段）'}
2. ✅ **Module 2: 生成增强** - COT重写和样本生成
   - COT 重写: {'已执行' if diagnostic_report.get('has_think_field', False) else '跳过（无 think 字段）'}
   - 合成生成: 已执行
3. ✅ **Module 3: RAG校验** - 知识库校验
4. ✅ **Module 4: PII清洗** - 隐私信息清洗

## 文件位置

- 优化后的数据集: `outputs/datasets/{task_id}/optimized_dataset.json`
- 元数据: `outputs/datasets/{task_id}/metadata.json`
- 诊断报告: `outputs/reports/{task_id}/diagnostic_report.json`
- 统计信息: `outputs/reports/{task_id}/statistics.json`

---
*报告由 Data Analyzer Service v4.0.0 自动生成*
"""
        return summary
    
    def load_dataset(self, task_id: str) -> Dict[str, Any]:
        """
        加载已保存的数据集
        
        Args:
            task_id: 任务ID
            
        Returns:
            包含数据集和元数据的字典
        """
        task_dir = self.datasets_dir / task_id
        
        if not task_dir.exists():
            raise FileNotFoundError(f"任务 {task_id} 的数据不存在")
        
        # 加载数据集
        dataset_file = task_dir / "optimized_dataset.json"
        with open(dataset_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        # 加载元数据
        metadata_file = task_dir / "metadata.json"
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        return {
            "dataset": dataset,
            "metadata": metadata
        }
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """
        列出所有已保存的任务
        
        Returns:
            任务列表
        """
        tasks = []
        
        for task_dir in self.datasets_dir.iterdir():
            if task_dir.is_dir():
                metadata_file = task_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        tasks.append({
                            "task_id": task_dir.name,
                            "timestamp": metadata.get("timestamp"),
                            "mode": metadata.get("mode"),
                            "dataset_size": metadata.get("dataset_size")
                        })
        
        # 按时间倒序排序
        tasks.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return tasks
