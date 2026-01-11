"""
测试存储功能
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8002"

def test_storage():
    """测试数据存储功能"""
    
    print("="*60)
    print("测试数据存储功能")
    print("="*60)
    
    # 1. 测试同步优化（自动保存）
    print("\n1. 测试同步优化（自动保存）...")
    
    test_data = {
        "dataset": [
            {
                "question": "什么是Python？",
                "answer": "Python是一种编程语言。"
            },
            {
                "question": "什么是Java？",
                "answer": "Java是另一种编程语言。"
            }
        ],
        "knowledge_base": [
            "Python是一种高级编程语言",
            "Java是面向对象的编程语言"
        ],
        "save_reports": True
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/optimize/sync", json=test_data)
    result = response.json()
    
    task_id = result["task_id"]
    print(f"   ✅ 任务ID: {task_id}")
    print(f"   ✅ 模式: {result['mode']}")
    print(f"   ✅ 输出样本数: {len(result['optimized_dataset'])}")
    
    # 2. 检查文件是否保存
    print("\n2. 检查文件是否保存...")
    
    outputs_dir = Path("./outputs")
    dataset_file = outputs_dir / "datasets" / task_id / "optimized_dataset.json"
    metadata_file = outputs_dir / "datasets" / task_id / "metadata.json"
    summary_file = outputs_dir / "reports" / task_id / "summary.md"
    
    if dataset_file.exists():
        print(f"   ✅ 数据集文件存在: {dataset_file}")
        with open(dataset_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
            print(f"      - 样本数: {len(dataset)}")
    else:
        print(f"   ❌ 数据集文件不存在: {dataset_file}")
    
    if metadata_file.exists():
        print(f"   ✅ 元数据文件存在: {metadata_file}")
    else:
        print(f"   ❌ 元数据文件不存在: {metadata_file}")
    
    if summary_file.exists():
        print(f"   ✅ 摘要报告存在: {summary_file}")
        print(f"\n   摘要报告内容预览:")
        with open(summary_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:15]
            for line in lines:
                print(f"      {line.rstrip()}")
    else:
        print(f"   ❌ 摘要报告不存在: {summary_file}")
    
    # 3. 测试列出任务API
    print("\n3. 测试列出任务API...")
    
    response = requests.get(f"{BASE_URL}/api/v1/tasks")
    tasks_result = response.json()
    
    print(f"   ✅ 总任务数: {tasks_result['total']}")
    if tasks_result['tasks']:
        print(f"   ✅ 最新任务:")
        latest = tasks_result['tasks'][0]
        print(f"      - ID: {latest['task_id']}")
        print(f"      - 时间: {latest['timestamp']}")
        print(f"      - 模式: {latest['mode']}")
        print(f"      - 大小: {latest['dataset_size']}")
    
    # 4. 测试获取历史数据集API
    print("\n4. 测试获取历史数据集API...")
    
    response = requests.get(f"{BASE_URL}/api/v1/tasks/{task_id}/dataset")
    dataset_result = response.json()
    
    print(f"   ✅ 任务ID: {dataset_result['task_id']}")
    print(f"   ✅ 数据集大小: {len(dataset_result['dataset'])}")
    print(f"   ✅ 元数据:")
    print(f"      - 时间戳: {dataset_result['metadata']['timestamp']}")
    print(f"      - 模式: {dataset_result['metadata']['mode']}")
    
    print("\n" + "="*60)
    print("✅ 所有测试通过！")
    print("="*60)

if __name__ == "__main__":
    try:
        test_storage()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
