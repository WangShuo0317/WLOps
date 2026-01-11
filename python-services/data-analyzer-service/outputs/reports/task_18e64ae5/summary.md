# 数据优化报告

## 基本信息

- **任务ID**: task_18e64ae5
- **生成时间**: 2026-01-11 00:01:28
- **优化模式**: auto (标注流程优化)

## 数据统计

### 输入输出
- **输入样本数**: 2
- **输出样本数**: 2
- **增长率**: 0.0%

### 诊断结果
- **稀缺聚类数**: 0
- **低质量样本数**: 2

### 优化统计
- **优化样本数**: 2
- **生成样本数**: 0
- **保留高质量样本**: 0

### RAG校验统计
- **总计**: 2
- **通过**: 2 (100.0%)
- **修正**: 0 (0.0%)
- **拒绝**: 0 (0.0%)

### PII清洗
- **清洗样本数**: 0

## 工作流执行

1. ✅ **Module 1: 诊断** - 识别问题样本
2. ✅ **Module 2: 生成增强** - COT重写和样本生成
3. ✅ **Module 3: RAG校验** - 知识库校验
4. ✅ **Module 4: PII清洗** - 隐私信息清洗

## 文件位置

- 优化后的数据集: `outputs/datasets/task_18e64ae5/optimized_dataset.json`
- 元数据: `outputs/datasets/task_18e64ae5/metadata.json`
- 诊断报告: `outputs/reports/task_18e64ae5/diagnostic_report.json`
- 统计信息: `outputs/reports/task_18e64ae5/statistics.json`

---
*报告由 Data Analyzer Service v4.0.0 自动生成*
