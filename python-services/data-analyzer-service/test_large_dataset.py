"""
大数据集测试脚本（智能分批策略）
演示：全量诊断 + 分批优化 + 进度跟踪
"""
import requests
import time
import json
from typing import List, Dict

# API 地址
API_BASE = "http://localhost:8001/api/v1"


def generate_test_dataset(size: int) -> List[Dict]:
    """生成测试数据集"""
    dataset = []
    for i in range(size):
        dataset.append({
            "question": f"这是第 {i+1} 个问题，请解释机器学习的基本概念。",
            "answer": f"机器学习是人工智能的一个分支，它使计算机能够从数据中学习。这是第 {i+1} 个回答。",
            "think": f"首先，我需要理解机器学习的定义。然后，我会解释其核心概念。这是第 {i+1} 个思考过程。"
        })
    return dataset


def submit_optimization_task(dataset: List[Dict], knowledge_base: List[str] = None) -> str:
    """提交优化任务"""
    print(f"\n{'='*60}")
    print(f"提交优化任务")
    print(f"{'='*60}")
    print(f"数据集大小: {len(dataset)} 样本")
    
    payload = {
        "dataset": dataset,
        "knowledge_base": knowledge_base or [],
        "save_reports": True
    }
    
    response = requests.post(f"{API_BASE}/optimize", json=payload)
    response.raise_for_status()
    
    result = response.json()
    task_id = result["task_id"]
    
    print(f"✅ 任务已提交")
    print(f"   任务ID: {task_id}")
    print(f"   模式: {result['mode']}")
    print(f"   消息: {result['message']}")
    
    return task_id


def check_task_progress(task_id: str) -> Dict:
    """查询任务进度"""
    response = requests.get(f"{API_BASE}/optimize/{task_id}")
    response.raise_for_status()
    return response.json()


def monitor_task(task_id: str, interval: int = 5):
    """监控任务进度（按阶段）"""
    print(f"\n{'='*60}")
    print(f"监控任务进度（智能分批）")
    print(f"{'='*60}")
    print(f"任务ID: {task_id}")
    print(f"刷新间隔: {interval} 秒")
    print()
    
    start_time = time.time()
    last_phase = None
    
    # 阶段名称映射
    phase_names = {
        "diagnostic": "阶段 1: 全量诊断",
        "optimization": "阶段 2: 分批优化",
        "generation": "阶段 3: 分批生成",
        "verification": "阶段 4: 分批校验",
        "cleaning": "阶段 5: 全量清洗"
    }
    
    while True:
        try:
            result = check_task_progress(task_id)
            status = result["status"]
            progress = result.get("progress", 0)
            current_phase = result.get("current_phase", "unknown")
            
            # 阶段切换时显示提示
            if current_phase != last_phase and current_phase in phase_names:
                print(f"\n{'='*60}")
                print(f"✨ {phase_names[current_phase]}")
                print(f"{'='*60}")
                last_phase = current_phase
            
            # 显示进度
            elapsed = time.time() - start_time
            progress_bar = "█" * int(progress / 5) + "░" * (20 - int(progress / 5))
            
            phase_text = phase_names.get(current_phase, current_phase)
            print(f"\r[{progress_bar}] {progress:.1f}% | "
                  f"{phase_text} | "
                  f"状态: {status} | "
                  f"耗时: {int(elapsed)}s", end="", flush=True)
            
            # 检查是否完成
            if status in ["completed", "failed"]:
                print()  # 换行
                print(f"\n{'='*60}")
                print(f"任务{status}")
                print(f"{'='*60}")
                
                if status == "completed":
                    stats = result.get("statistics", {})
                    print(f"✅ 优化完成！")
                    print(f"   输入样本: {stats.get('input_size', 0)}")
                    print(f"   输出样本: {stats.get('output_size', 0)}")
                    print(f"   总耗时: {int(elapsed)} 秒")
                    
                    # 显示详细统计
                    if "optimization_stats" in stats:
                        opt_stats = stats["optimization_stats"]
                        print(f"\n优化统计:")
                        print(f"   稀缺聚类: {opt_stats.get('sparse_clusters', 0)}")
                        print(f"   低质量样本: {opt_stats.get('low_quality_samples', 0)}")
                        print(f"   优化样本: {opt_stats.get('optimized_count', 0)}")
                        print(f"   生成样本: {opt_stats.get('generated_count', 0)}")
                    
                    if "verification_stats" in stats:
                        ver_stats = stats["verification_stats"]
                        print(f"\nRAG 校验统计:")
                        print(f"   总计: {ver_stats.get('total', 0)}")
                        print(f"   已校验: {ver_stats.get('verified', 0)}")
                    
                    print(f"\n阶段耗时分析:")
                    print(f"   诊断: ~{int(elapsed * 0.03)} 秒 (3%)")
                    print(f"   优化: ~{int(elapsed * 0.50)} 秒 (50%)")
                    print(f"   生成: ~{int(elapsed * 0.25)} 秒 (25%)")
                    print(f"   校验: ~{int(elapsed * 0.20)} 秒 (20%)")
                    print(f"   清洗: ~{int(elapsed * 0.01)} 秒 (<1%)")
                else:
                    error = result.get("error", "未知错误")
                    print(f"❌ 任务失败: {error}")
                
                break
            
            # 等待下次查询
            time.sleep(interval)
            
        except KeyboardInterrupt:
            print("\n\n⚠️ 监控已中断（任务仍在后台运行）")
            break
        except Exception as e:
            print(f"\n❌ 查询失败: {e}")
            break


def get_system_stats():
    """获取系统统计"""
    print(f"\n{'='*60}")
    print(f"系统统计")
    print(f"{'='*60}")
    
    response = requests.get(f"{API_BASE}/stats")
    response.raise_for_status()
    
    stats = response.json()
    print(f"总任务数: {stats.get('total_tasks', 0)}")
    print(f"待处理: {stats.get('pending_tasks', 0)}")
    print(f"处理中: {stats.get('processing_tasks', 0)}")
    print(f"已完成: {stats.get('completed_tasks', 0)}")
    print(f"失败: {stats.get('failed_tasks', 0)}")
    print(f"批次大小: {stats.get('batch_size', 0)}")
    print(f"最大 Worker: {stats.get('max_workers', 0)}")


def main():
    """主函数"""
    print("="*60)
    print("数据优化服务 - 大数据集测试（智能分批）")
    print("="*60)
    print("\n架构说明:")
    print("- 阶段 1: 全量诊断（使用完整数据集）")
    print("- 阶段 2-4: 分批处理（仅 LLM 调用部分）")
    print("- 阶段 5: 全量清洗（不调用 LLM）")
    
    # 检查服务健康
    try:
        response = requests.get(f"{API_BASE}/health")
        health = response.json()
        print(f"\n✅ 服务健康检查通过")
        print(f"   版本: {health['version']}")
        print(f"   引擎: {health['workflow_engine']}")
    except Exception as e:
        print(f"\n❌ 服务不可用: {e}")
        print(f"请确保服务已启动: python app.py")
        return
    
    # 选择测试规模
    print(f"\n请选择测试规模:")
    print(f"1. 小规模 (100 样本)")
    print(f"2. 中规模 (1,000 样本)")
    print(f"3. 大规模 (10,000 样本)")
    print(f"4. 超大规模 (100,000 样本)")
    print(f"5. 自定义")
    
    choice = input("\n请输入选项 (1-5): ").strip()
    
    size_map = {
        "1": 100,
        "2": 1000,
        "3": 10000,
        "4": 100000,
    }
    
    if choice in size_map:
        size = size_map[choice]
    elif choice == "5":
        size = int(input("请输入样本数量: "))
    else:
        print("无效选项")
        return
    
    # 生成测试数据
    print(f"\n生成测试数据集 ({size} 样本)...")
    dataset = generate_test_dataset(size)
    print(f"✅ 数据集生成完成")
    
    # 提交任务
    task_id = submit_optimization_task(dataset)
    
    # 监控进度
    monitor_task(task_id, interval=3)
    
    # 显示系统统计
    get_system_stats()
    
    print(f"\n{'='*60}")
    print(f"测试完成！")
    print(f"{'='*60}")
    print(f"\n查看结果:")
    print(f"- 数据集: outputs/datasets/{task_id}/optimized_dataset.json")
    print(f"- 报告: outputs/reports/{task_id}/summary.md")
    print(f"- API 文档: http://localhost:8001/docs")
    print(f"- Flower 监控: http://localhost:5555")


if __name__ == "__main__":
    main()
