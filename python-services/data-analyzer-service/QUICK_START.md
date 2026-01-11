# 快速开始指南

## 🚀 5 分钟快速上手

### 1. 安装依赖

```bash
cd python-services/data-analyzer-service
pip install -r requirements.txt
```

### 2. 配置环境

创建 `.env` 文件：

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
```

### 3. 启动服务

```bash
# Windows
start.bat

# Linux/Mac
chmod +x start.sh
./start.sh
```

服务将在 `http://localhost:8002` 启动

### 4. 测试服务

打开新终端，运行测试：

```bash
python test_workflow.py
```

## 📡 基本使用

### 方式 1: 标注流程优化（推荐）

自动诊断和优化，无需提供指导：

```python
import requests

response = requests.post("http://localhost:8002/api/v1/optimize/sync", json={
    "dataset": [
        {
            "question": "什么是机器学习？",
            "answer": "机器学习是人工智能的一个分支"
        },
        {
            "question": "深度学习和机器学习有什么区别？",
            "answer": "深度学习是机器学习的子集"
        }
    ]
})

result = response.json()
print(f"模式: {result['mode']}")  # auto
print(f"输入: {result['statistics']['input_size']} 样本")
print(f"输出: {result['statistics']['output_size']} 样本")
print(f"优化后的数据集: {result['optimized_dataset']}")
```

### 方式 2: 指定优化

提供优化指导，按需优化：

```python
response = requests.post("http://localhost:8002/api/v1/optimize/sync", json={
    "dataset": [...],
    "optimization_guidance": {
        "focus_areas": ["reasoning_quality"],  # 只关注推理质量
        "optimization_instructions": "为每个样本添加详细的推理步骤"
    }
})

result = response.json()
print(f"模式: {result['mode']}")  # guided
```

## 🔍 查看 API 文档

启动服务后，访问：

- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

## 📊 工作流说明

```
原始数据集
    ↓
[模式选择] → auto（自动）或 guided（指导）
    ↓
[诊断] → 识别稀缺样本和低质量样本
    ↓
[优化] → COT 重写 + 合成生成
    ↓
[校验] → RAG 校验
    ↓
[清洗] → PII 清洗
    ↓
纯净的高质量数据集
```

## 🎯 两种模式对比

| 特性 | 标注流程优化（Auto） | 指定优化（Guided） |
|------|---------------------|-------------------|
| 使用场景 | 通用数据集优化 | 特定问题修复 |
| 需要指导 | ❌ 否 | ✅ 是 |
| 诊断范围 | 全面诊断 | 按指导诊断 |
| 优化方式 | 自动优化 | 按指导优化 |
| 适用数据 | 任何数据集 | 已知问题的数据集 |

## 💡 使用建议

1. **首次使用**：使用 Auto 模式，让系统自动诊断和优化
2. **已知问题**：使用 Guided 模式，提供具体的优化指导
3. **小数据集**：使用同步 API (`/optimize/sync`)
4. **大数据集**：使用异步 API (`/optimize`)

## 🐛 常见问题

### Q: 服务启动失败？
A: 检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确

### Q: Embedding 模型加载慢？
A: 首次加载需要下载模型，请耐心等待

### Q: 内存不足？
A: 使用更小的 Embedding 模型：
```bash
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## 📚 更多文档

- [完整文档](README.md)
- [重构说明](REFACTORING_V4.md)
- [配置说明](config.py)

## 🎉 开始使用

现在你已经准备好使用数据优化服务了！

试试运行测试脚本：
```bash
python test_workflow.py
```

或者直接调用 API：
```bash
curl -X POST http://localhost:8002/api/v1/health
```
