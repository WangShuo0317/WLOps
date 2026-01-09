# 使用指南

## 🎯 系统功能

本系统实现完整的数据优化流程：

```
原始数据集
    ↓
[诊断] → 识别稀缺样本 + 低质量样本
    ↓
[优化] → COT重写低质量样本 + 生成稀缺样本
    ↓
[校验] → RAG校验所有优化/生成的样本
    ↓
[清洗] → PII隐私清洗
    ↓
纯净的高质量数据集
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

```bash
export OPENAI_API_KEY="your-api-key"
export EMBEDDING_MODEL="BAAI/bge-m3"
```

### 3. 运行测试

```python
python test_self_evolving_system.py
```

## 💡 使用示例

### 基础用法

```python
from llm_client import LLMClient
from sentence_transformers import SentenceTransformer
from system_integration import SelfEvolvingDataOptimizer

# 初始化
llm_client = LLMClient()
embedding_model = SentenceTransformer("BAAI/bge-m3")
optimizer = SelfEvolvingDataOptimizer(llm_client, embedding_model)

# 加载知识库（用于RAG校验）
knowledge = ["知识1", "知识2", ...]
optimizer.load_knowledge_base(knowledge)

# 执行优化
result = optimizer.run_iteration(dataset, iteration_id=0)
high_quality_dataset = result["optimized_dataset"]
```

### 数据格式

输入数据集格式：

```json
[
  {
    "question": "3 + 5 = ?",
    "answer": "8"
  },
  {
    "question": "小明有10元，买了3元的笔，还剩多少？",
    "answer": "7元",
    "chain_of_thought": "10 - 3 = 7"
  }
]
```

输出数据集格式（所有样本都包含推理过程）：

```json
[
  {
    "question": "3 + 5 = ?",
    "chain_of_thought": "这是一个加法运算。3加5等于8。",
    "answer": "8",
    "_optimized": true
  },
  {
    "question": "小明有10元，买了3元的笔，还剩多少？",
    "chain_of_thought": "10 - 3 = 7",
    "answer": "7元"
  }
]
```

## 📊 核心模块

### Module 1: 诊断智能体

- **语义分布分析**: 使用 Embedding + HDBSCAN 聚类识别稀缺样本
- **推理质量分析**: 使用 LLM 评估推理质量，识别低质量样本

### Module 2: 生成增强智能体

- **COT 重写**: 为低质量样本补充推理过程
- **合成生成**: 针对稀缺特征生成新样本

### Module 3: RAG 校验智能体

- **事实提取**: 从推理过程中提取事实宣称
- **检索**: 在知识库中检索相关证据
- **校验**: 验证事实一致性，自动修正错误

### Module 4: 隐私清洗智能体

- **PII 检测**: 识别个人敏感信息
- **合成替换**: 保留语义的同时替换敏感信息

## 🔧 配置参数

```bash
# LLM配置
OPENAI_API_KEY="your-key"
OPENAI_MODEL="gpt-4"

# Embedding配置
EMBEDDING_MODEL="BAAI/bge-m3"
EMBEDDING_BATCH_SIZE=32

# 向量数据库
VECTOR_DB_TYPE="faiss"
VECTOR_DB_PATH="./vector_db"

# RAG校验
RAG_CONFIDENCE_THRESHOLD=0.8
RAG_ENABLE_SELF_CORRECTION=true

# 聚类参数
MIN_CLUSTER_SIZE=5
MIN_SAMPLES=3
```

## 📈 性能指标

| 操作 | 100样本 | 耗时 | Token消耗 |
|------|---------|------|-----------|
| 诊断分析 | 15秒 | 0 (本地) |
| 优化样本 | 2分钟 | 25K |
| 生成样本 | 1分钟 | 16K |
| RAG校验 | 1.5分钟 | 15K |
| **总计** | **5分钟** | **56K** |

## 🎓 最佳实践

1. **知识库质量**: 使用权威、准确的知识源
2. **采样策略**: 推理分析采样 30-50 个样本
3. **阈值调整**: 根据实际情况调整置信度阈值
4. **成本控制**: 使用 GPT-3.5 降低成本

## 📞 技术支持

- 查看 `README.md` 了解项目概述
- 运行 `test_self_evolving_system.py` 查看完整示例
- 查看代码注释获取详细说明

---

**版本**: 3.1.0  
**更新**: 2026-01-09
