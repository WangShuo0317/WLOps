"""
测试 LangGraph 工作流
"""
import requests
import json
from loguru import logger

API_BASE = "http://localhost:8002/api/v1"

def test_auto_mode():
    """测试标注流程优化模式（Auto Mode）"""
    logger.info("="*60)
    logger.info("测试 1: 标注流程优化（Auto Mode）")
    logger.info("="*60)
    
    dataset = [
        {
            "question": "什么是机器学习？",
            "answer": "机器学习是人工智能的一个分支"
        },
        {
            "question": "深度学习和机器学习有什么区别？",
            "answer": "深度学习是机器学习的子集"
        }
    ]
    
    response = requests.post(f"{API_BASE}/optimize/sync", json={
        "dataset": dataset
    })
    
    result = response.json()
    
    logger.info(f"✅ 测试通过")
    logger.info(f"   模式: {result['mode']}")
    logger.info(f"   输入: {result['statistics']['input_size']} 样本")
    logger.info(f"   输出: {result['statistics']['output_size']} 样本")
    logger.info(f"   优化: {result['statistics']['optimization_stats']['optimized_count']}")
    logger.info(f"   生成: {result['statistics']['optimization_stats']['generated_count']}")
    
    assert result['mode'] == 'auto', "模式应该是 auto"
    assert result['status'] == 'completed', "状态应该是 completed"
    
    return result


def test_guided_mode():
    """测试指定优化模式（Guided Mode）"""
    logger.info("\n" + "="*60)
    logger.info("测试 2: 指定优化（Guided Mode）")
    logger.info("="*60)
    
    dataset = [
        {
            "question": "什么是神经网络？",
            "answer": "神经网络是一种计算模型"
        }
    ]
    
    optimization_guidance = {
        "focus_areas": ["reasoning_quality"],
        "optimization_instructions": "为每个样本添加详细的推理步骤",
        "generation_instructions": "生成更多关于深度学习的样本"
    }
    
    response = requests.post(f"{API_BASE}/optimize/sync", json={
        "dataset": dataset,
        "optimization_guidance": optimization_guidance
    })
    
    result = response.json()
    
    logger.info(f"✅ 测试通过")
    logger.info(f"   模式: {result['mode']}")
    logger.info(f"   输入: {result['statistics']['input_size']} 样本")
    logger.info(f"   输出: {result['statistics']['output_size']} 样本")
    
    assert result['mode'] == 'guided', "模式应该是 guided"
    assert result['status'] == 'completed', "状态应该是 completed"
    
    return result


def test_health_check():
    """测试健康检查"""
    logger.info("\n" + "="*60)
    logger.info("测试 3: 健康检查")
    logger.info("="*60)
    
    response = requests.get(f"{API_BASE}/health")
    result = response.json()
    
    logger.info(f"✅ 测试通过")
    logger.info(f"   状态: {result['status']}")
    logger.info(f"   服务: {result['service']}")
    logger.info(f"   版本: {result['version']}")
    logger.info(f"   工作流引擎: {result['workflow_engine']}")
    logger.info(f"   LLM 可用: {result['llm_available']}")
    
    assert result['status'] == 'healthy', "服务应该是健康的"
    assert result['workflow_engine'] == 'LangGraph', "应该使用 LangGraph"
    
    return result


def test_knowledge_base():
    """测试知识库加载"""
    logger.info("\n" + "="*60)
    logger.info("测试 4: 知识库加载")
    logger.info("="*60)
    
    knowledge = [
        "机器学习是一种让计算机从数据中学习的技术",
        "深度学习使用多层神经网络来学习数据的层次化表示",
        "监督学习需要标注数据，无监督学习不需要标注"
    ]
    
    response = requests.post(f"{API_BASE}/knowledge-base/load", json=knowledge)
    result = response.json()
    
    logger.info(f"✅ 测试通过")
    logger.info(f"   状态: {result['status']}")
    logger.info(f"   消息: {result['message']}")
    logger.info(f"   知识库大小: {result['knowledge_base_stats']['total_documents']}")
    
    assert result['status'] == 'success', "加载应该成功"
    
    return result


if __name__ == "__main__":
    try:
        logger.info("开始测试 LangGraph 工作流...")
        
        # 测试健康检查
        test_health_check()
        
        # 测试知识库
        test_knowledge_base()
        
        # 测试 Auto 模式
        test_auto_mode()
        
        # 测试 Guided 模式
        test_guided_mode()
        
        logger.info("\n" + "="*60)
        logger.info("🎉 所有测试通过！")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
