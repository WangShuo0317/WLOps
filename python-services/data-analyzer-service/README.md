# 数据优化服务 v4.0.0

基于 **LangGraph** 构建的多智能体数据优化工作流，将原始数据集转换为纯净的高质量数据集。

## ✨ 核心特性

### 🎯 双模式支持

1. **标注流程优化（Auto Mode）**
   - 无需优化指导
   - 自动诊断数据集问题
   - 自动优化和生成样本
   - 适用于通用数据集优化

2. **指定优化（Guided Mode）**
   - 提供优化指导
   - 根据指导诊断特定问题
   - 按指导要求优化和生成
   - 适用于已知问题的数据集

### 🔄 工作流架构

```
原始数据集
    ↓
[模式选择] → auto / guided
    ↓
[Module 1: 诊断]
├─ 语义分布分析 → 识别稀缺样本
└─ 推理质量分析 → 识别低质量样本
    ↓
[Module 2: 生成增强]
├─ COT重写 → 优化低质量样本
└─ 合成生成 → 生成稀缺样本
    ↓
[Module 3: RAG校验]
└─ 校验所有优化/生成的样本
    ↓
[Module 4: PII清洗]
└─ 清洗隐私信息
    ↓
纯净的高质量数据集
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

创建 `.env` 文件：

```bash
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
EMBEDDING_MODEL=BAAI/bge-m3
```

### 3. 启动服务

```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

服务将在 `http://localhost:8002` 启动

### 4. 测试服务

```bash
python test_workflow.py
```

## 📡 API 使用

### 标注流程优化（Auto Mode）

```python
import requests

response = requests.post("http://localhost:8002/api/v1/optimize/sync", json={
    "dataset": [
        {
            "question": "什么是机器学习？",
            "answer": "机器学习是人工智能的一个分支"
        }
    ]
})

result = response.json()
print(f"模式: {result['mode']}")  # auto
print(f"输出: {result['optimized_dataset']}")
```

### 指定优化（Guided Mode）

```python
response = requests.post("http://localhost:8002/api/v1/optimize/sync", json={
    "dataset": [...],
    "optimization_guidance": {
        "focus_areas": ["reasoning_quality"],
        "optimization_instructions": "为每个样本添加详细的推理步骤"
    }
})

result = response.json()
print(f"模式: {result['mode']}")  # guided
```

## 🏗️ 技术架构

### LangGraph 工作流

- **状态管理**：自动管理工作流状态
- **节点**：4 个智能体节点（诊断、优化、校验、清洗）
- **边**：定义节点之间的转换
- **可视化**：支持工作流可视化

### 智能体

- **DiagnosticAgent**：诊断智能体（语义分布 + 推理质量）
- **OptimizationAgent**：优化智能体（COT 重写 + 合成生成）
- **VerificationAgent**：校验智能体（RAG 校验）
- **CleaningAgent**：清洗智能体（PII 清洗）

## 📁 项目结构

```
python-services/data-analyzer-service/
├── app.py                          # FastAPI 应用
├── workflow_graph.py               # LangGraph 工作流
├── knowledge_base_manager.py       # 知识库管理
├── agents/
│   ├── diagnostic_agent.py         # 诊断智能体
│   ├── optimization_agent.py       # 优化智能体
│   ├── verification_agent.py       # 校验智能体
│   └── cleaning_agent.py           # 清洗智能体
├── config.py                       # 配置
├── llm_client.py                   # LLM 客户端
├── requirements.txt                # 依赖
├── test_workflow.py                # 测试脚本
├── README.md                       # 本文档
├── QUICK_START.md                  # 快速开始
└── REFACTORING_V4.md               # 重构说明
```

## 📊 输出统计

```json
{
    "statistics": {
        "input_size": 100,
        "output_size": 150,
        "mode": "auto",
        "optimization_stats": {
            "optimized_count": 30,
            "generated_count": 20,
            "high_quality_kept": 70
        },
        "verification_stats": {
            "passed": 35,
            "corrected": 10,
            "rejected": 5
        },
        "pii_cleaned_count": 5
    }
}
```

## 🔧 配置说明

### RAG 校验

```python
RAG_RETRIEVAL_TOP_K = 5              # 检索 top-k 文档
RAG_CONFIDENCE_THRESHOLD = 0.8       # 置信度阈值
RAG_ENABLE_SELF_CORRECTION = True    # 启用自动修正
```

### 聚类

```python
MIN_CLUSTER_SIZE = 5                 # 最小聚类大小
MIN_SAMPLES = 3                      # 最小样本数
```

### PII 清洗

```python
PII_ENTITIES = ["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", ...]
PII_LANGUAGE = "zh"                  # 支持中文
```

## 📚 文档

- [快速开始](QUICK_START.md) - 5 分钟上手
- [重构说明](REFACTORING_V4.md) - 架构变更详情
- [API 文档](http://localhost:8002/docs) - Swagger UI

## 🎉 版本历史

- **v4.0.0** (2026-01-10)
  - 使用 LangGraph 重构
  - 支持双模式（auto/guided）
  - 多智能体架构
  - 代码量减少 40%

## 📄 许可证

MIT License
