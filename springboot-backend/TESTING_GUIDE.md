# 测试指南

## 快速测试

### 1. 启动服务

```bash
# 启动 Python 数据优化服务
cd WLOps/python-services/data-analyzer-service
python api.py

# 启动 Spring Boot 后端
cd WLOps/springboot-backend
mvn spring-boot:run
```

### 2. 健康检查

```bash
# 检查 Python 服务
curl http://localhost:8002/api/v1/health

# 检查 Spring Boot 服务
curl http://localhost:8080/api/data-optimization/health
```

### 3. 测试同步优化

```bash
curl -X POST http://localhost:8080/api/data-optimization/optimize/sync \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": [
      {
        "question": "3 + 5 = ?",
        "answer": "8"
      },
      {
        "question": "10 - 3 = ?",
        "answer": "7"
      }
    ],
    "knowledge_base": [
      "加法运算：两个数相加，得到它们的和",
      "减法运算：从一个数中减去另一个数"
    ]
  }'
```

### 4. 测试异步优化

```bash
# 启动任务
TASK_ID=$(curl -X POST http://localhost:8080/api/data-optimization/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "dataset": [...],
    "knowledge_base": [...]
  }' | jq -r '.task_id')

# 查询结果
curl http://localhost:8080/api/data-optimization/optimize/$TASK_ID
```

## 集成测试

### 测试数据准备

创建测试数据文件 `test-data.json`:

```json
{
  "dataset": [
    {
      "question": "小明有10个苹果，吃了3个，还剩几个？",
      "answer": "7个"
    },
    {
      "question": "一个长方形的长是5米，宽是3米，面积是多少？",
      "answer": "15平方米"
    },
    {
      "question": "3 × 4 = ?",
      "answer": "12"
    }
  ],
  "knowledge_base": [
    "减法运算：从一个数中减去另一个数，得到差",
    "长方形面积公式：面积=长×宽",
    "乘法运算：一个数重复相加若干次"
  ]
}
```

### 执行测试

```bash
# 使用测试数据
curl -X POST http://localhost:8080/api/data-optimization/optimize/sync \
  -H "Content-Type: application/json" \
  -d @test-data.json
```

## 预期结果

### 成功响应示例

```json
{
  "task_id": "task_abc123",
  "status": "completed",
  "optimized_dataset": [
    {
      "question": "小明有10个苹果，吃了3个，还剩几个？",
      "chain_of_thought": "这是一个减法问题。小明原本有10个苹果，吃掉了3个，需要用减法计算剩余数量。10 - 3 = 7，所以还剩7个苹果。",
      "answer": "7个",
      "_optimized": true
    },
    {
      "question": "一个长方形的长是5米，宽是3米，面积是多少？",
      "chain_of_thought": "根据长方形面积公式：面积 = 长 × 宽。已知长是5米，宽是3米，所以面积 = 5 × 3 = 15平方米。",
      "answer": "15平方米",
      "_optimized": true
    },
    {
      "question": "3 × 4 = ?",
      "chain_of_thought": "这是一个乘法运算。3 × 4 表示3个4相加，即 4 + 4 + 4 = 12。",
      "answer": "12",
      "_optimized": true
    }
  ],
  "statistics": {
    "input_size": 3,
    "output_size": 3,
    "optimized_count": 3,
    "generated_count": 0,
    "quality_improvement": 55.2,
    "duration_seconds": 4.8
  }
}
```

## 常见问题

### 1. 连接失败

**问题**: `Connection refused`

**解决**:
- 确保 Python 服务已启动（端口 8002）
- 检查 `application.yml` 中的服务地址配置

### 2. 超时错误

**问题**: `Read timeout`

**解决**:
- 增加 WebClient 超时配置
- 对大数据集使用异步接口

### 3. JSON 解析错误

**问题**: `Cannot deserialize`

**解决**:
- 检查字段命名（使用 snake_case）
- 确保 DTO 类有 `@JsonProperty` 注解

## 性能测试

### 小数据集测试（< 100 样本）

```bash
# 测试 10 个样本
time curl -X POST http://localhost:8080/api/data-optimization/optimize/sync \
  -H "Content-Type: application/json" \
  -d @small-dataset.json

# 预期响应时间: < 5 秒
```

### 大数据集测试（> 100 样本）

```bash
# 测试 500 个样本
curl -X POST http://localhost:8080/api/data-optimization/optimize \
  -H "Content-Type: application/json" \
  -d @large-dataset.json

# 预期响应时间: 立即返回任务 ID
# 实际处理时间: 根据数据集大小而定
```

---

**版本**: 3.1.0  
**更新**: 2026-01-09
