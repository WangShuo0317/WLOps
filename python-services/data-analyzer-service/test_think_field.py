"""
测试 think 字段检测功能
"""
import requests
import json

BASE_URL = "http://localhost:8002"

def test_with_think_field():
    """测试包含 think 字段的数据"""
    print("="*60)
    print("测试 1: 包含 think 字段的数据（推理数据）")
    print("="*60)
    
    test_data = {
        "dataset": [
            {
                "question": "计算 25 × 4 的结果",
                "think": "首先，我可以将 25 分解为 100/4，这样 25 × 4 = (100/4) × 4 = 100",
                "answer": "100"
            },
            {
                "question": "如果一个数的平方是 144，这个数是多少？",
                "think": "设这个数为 x，则 x² = 144，开平方得 x = ±12",
                "answer": "±12"
            }
        ],
        "save_reports": True
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/optimize/sync", json=test_data)
    result = response.json()
    
    print(f"\n✅ 任务ID: {result['task_id']}")
    print(f"✅ 模式: {result['mode']}")
    print(f"✅ 输出样本数: {len(result['optimized_dataset'])}")
    print(f"\n统计信息:")
    print(f"  - 优化样本数: {result['statistics']['optimization_stats']['optimized_count']}")
    print(f"  - 生成样本数: {result['statistics']['optimization_stats']['generated_count']}")
    
    # 检查是否有 reasoning 字段
    has_reasoning = any('reasoning' in sample for sample in result['optimized_dataset'])
    print(f"\n✅ COT 重写: {'已执行' if has_reasoning else '未执行'}")
    
    return result['task_id']


def test_without_think_field():
    """测试不包含 think 字段的数据（普通 QA）"""
    print("\n" + "="*60)
    print("测试 2: 不包含 think 字段的数据（普通 QA）")
    print("="*60)
    
    test_data = {
        "dataset": [
            {
                "question": "什么是机器学习？",
                "answer": "机器学习是人工智能的一个分支。"
            },
            {
                "question": "什么是深度学习？",
                "answer": "深度学习是机器学习的子集。"
            },
            {
                "question": "什么是神经网络？",
                "answer": "神经网络是一种计算模型。"
            }
        ],
        "save_reports": True
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/optimize/sync", json=test_data)
    result = response.json()
    
    print(f"\n✅ 任务ID: {result['task_id']}")
    print(f"✅ 模式: {result['mode']}")
    print(f"✅ 输出样本数: {len(result['optimized_dataset'])}")
    print(f"\n统计信息:")
    print(f"  - 优化样本数: {result['statistics']['optimization_stats']['optimized_count']}")
    print(f"  - 生成样本数: {result['statistics']['optimization_stats']['generated_count']}")
    
    # 检查是否有 reasoning 字段
    has_reasoning = any('reasoning' in sample for sample in result['optimized_dataset'])
    print(f"\n✅ COT 重写: {'已执行（不应该）' if has_reasoning else '跳过（正确）'}")
    
    return result['task_id']


def test_mixed_case_think():
    """测试不同大小写的 think 字段"""
    print("\n" + "="*60)
    print("测试 3: 不同大小写的 think 字段")
    print("="*60)
    
    test_data = {
        "dataset": [
            {
                "question": "测试 THINK 字段",
                "THINK": "这是大写的 THINK",
                "answer": "测试答案"
            },
            {
                "question": "测试 Think 字段",
                "Think": "这是首字母大写的 Think",
                "answer": "测试答案"
            }
        ],
        "save_reports": True
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/optimize/sync", json=test_data)
    result = response.json()
    
    print(f"\n✅ 任务ID: {result['task_id']}")
    print(f"✅ 应该检测到 think 字段并执行 COT 重写")
    print(f"✅ 优化样本数: {result['statistics']['optimization_stats']['optimized_count']}")
    
    return result['task_id']


def check_report(task_id):
    """检查报告内容"""
    print(f"\n检查任务 {task_id} 的报告...")
    
    import os
    report_path = f"outputs/reports/{task_id}/summary.md"
    
    if os.path.exists(report_path):
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查关键信息
        if "推理数据" in content or "普通 QA 数据" in content:
            print("✅ 报告包含数据类型信息")
        
        if "推理质量分析" in content:
            print("✅ 报告包含推理质量分析状态")
        
        if "COT 重写" in content:
            print("✅ 报告包含 COT 重写状态")
    else:
        print(f"❌ 报告文件不存在: {report_path}")


if __name__ == "__main__":
    try:
        # 测试 1: 包含 think 字段
        task_id_1 = test_with_think_field()
        check_report(task_id_1)
        
        # 测试 2: 不包含 think 字段
        task_id_2 = test_without_think_field()
        check_report(task_id_2)
        
        # 测试 3: 不同大小写
        task_id_3 = test_mixed_case_think()
        check_report(task_id_3)
        
        print("\n" + "="*60)
        print("✅ 所有测试完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
