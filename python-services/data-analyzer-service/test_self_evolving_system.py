"""
自进化数据优化智能体系统测试
完整的端到端测试示例
"""
import json
from loguru import logger
from sentence_transformers import SentenceTransformer

from llm_client import LLMClient
from system_integration import SelfEvolvingDataOptimizer

def create_test_dataset():
    """创建测试数据集"""
    dataset = [
        # 加法题（有推理）
        {
            "question": "小明有5个苹果，小红给了他3个，小明现在有几个苹果？",
            "chain_of_thought": "小明原本有5个苹果，小红给了他3个，所以总共是5+3=8个苹果。",
            "answer": "8个"
        },
        {
            "question": "一个班有20个男生和15个女生，一共有多少学生？",
            "chain_of_thought": "男生20人，女生15人，总人数=20+15=35人。",
            "answer": "35人"
        },
        
        # 减法题（无推理）
        {
            "question": "10 - 3 = ?",
            "answer": "7"
        },
        {
            "question": "小华有15元，买了一支8元的笔，还剩多少钱？",
            "answer": "7元"
        },
        
        # 乘法题（无推理）
        {
            "question": "3 × 4 = ?",
            "answer": "12"
        },
        {
            "question": "一盒鸡蛋有12个，5盒一共有多少个？",
            "answer": "60个"
        },
        
        # 除法题（稀缺，无推理）
        {
            "question": "12 ÷ 3 = ?",
            "answer": "4"
        },
        
        # 应用题（有推理）
        {
            "question": "一个长方形的长是8米，宽是5米，面积是多少？",
            "chain_of_thought": "长方形面积公式是：面积=长×宽。代入数值：面积=8×5=40平方米。",
            "answer": "40平方米"
        }
    ]
    
    return dataset


def create_knowledge_base():
    """创建测试知识库"""
    knowledge = [
        "加法运算：两个数相加，得到它们的和。例如：3+5=8",
        "减法运算：从一个数中减去另一个数，得到差。例如：10-3=7",
        "乘法运算：一个数重复相加若干次。例如：3×4=12，即3+3+3+3=12",
        "除法运算：将一个数平均分成若干份。例如：12÷3=4，即12分成3份，每份4个",
        "长方形面积公式：面积=长×宽",
        "正方形面积公式：面积=边长×边长",
        "三角形面积公式：面积=底×高÷2",
        "圆的面积公式：面积=π×半径²",
        "速度公式：速度=路程÷时间",
        "路程公式：路程=速度×时间"
    ]
    
    return knowledge


def main():
    """主测试流程"""
    logger.info("="*60)
    logger.info("自进化数据优化智能体系统测试")
    logger.info("="*60)
    
    # 1. 初始化系统
    logger.info("\n[步骤 1] 初始化系统...")
    
    # 初始化 LLM 客户端
    llm_client = LLMClient()
    
    if not llm_client.is_available():
        logger.error("LLM 客户端不可用，请配置 OPENAI_API_KEY")
        logger.info("提示: export OPENAI_API_KEY='your-api-key'")
        return
    
    # 初始化 Embedding 模型
    logger.info("加载 Embedding 模型...")
    embedding_model = SentenceTransformer("BAAI/bge-m3")
    
    # 初始化系统
    optimizer = SelfEvolvingDataOptimizer(
        llm_client=llm_client,
        embedding_model=embedding_model,
        knowledge_base_path="./test_vector_db"
    )
    
    logger.info("✓ 系统初始化完成")
    
    # 2. 加载知识库
    logger.info("\n[步骤 2] 加载知识库...")
    
    knowledge = create_knowledge_base()
    optimizer.load_knowledge_base(knowledge)
    
    logger.info(f"✓ 知识库加载完成，共 {len(knowledge)} 条知识")
    
    # 3. 创建测试数据集
    logger.info("\n[步骤 3] 创建测试数据集...")
    
    dataset = create_test_dataset()
    
    logger.info(f"✓ 测试数据集创建完成，共 {len(dataset)} 个样本")
    logger.info(f"  - 有推理过程: {sum(1 for d in dataset if 'chain_of_thought' in d)}")
    logger.info(f"  - 无推理过程: {sum(1 for d in dataset if 'chain_of_thought' not in d)}")
    
    # 4. 执行单轮迭代测试
    logger.info("\n[步骤 4] 执行单轮迭代测试...")
    
    result = optimizer.run_iteration(
        dataset=dataset,
        iteration_id=0,
        save_reports=True
    )
    
    optimized_dataset = result["optimized_dataset"]
    iteration_summary = result["iteration_summary"]
    
    logger.info("\n✓ 单轮迭代完成!")
    logger.info(f"  输入样本数: {iteration_summary['input_size']}")
    logger.info(f"  输出样本数: {iteration_summary['output_size']}")
    logger.info(f"  新增样本数: {iteration_summary['output_size'] - iteration_summary['input_size']}")
    logger.info(f"  质量提升: {iteration_summary['quality_improvement']:.1f}%")
    logger.info(f"  耗时: {iteration_summary['duration_seconds']:.1f} 秒")
    
    # 5. 查看诊断报告
    logger.info("\n[步骤 5] 查看诊断报告...")
    
    diagnostic = iteration_summary["diagnostic_report"]
    
    logger.info(f"\n语义分布分析:")
    semantic = diagnostic["semantic_analysis"]
    logger.info(f"  - 聚类数量: {semantic['clustering_results']['n_clusters']}")
    logger.info(f"  - 数据均衡: {'是' if semantic['balance_metrics']['is_balanced'] else '否'}")
    logger.info(f"  - 不平衡比率: {semantic['balance_metrics']['imbalance_ratio']:.2f}")
    
    logger.info(f"\n推理深度分析:")
    reasoning = diagnostic["reasoning_analysis"]
    logger.info(f"  - COT 覆盖率: {reasoning['basic_statistics']['cot_coverage']:.1%}")
    logger.info(f"  - 平均推理步数: {reasoning['basic_statistics']['avg_reasoning_steps']:.1f}")
    logger.info(f"  - 质量评分: {reasoning['overall_assessment']['quality_score']:.1f}/100")
    
    logger.info(f"\n稀缺聚类:")
    for cluster in diagnostic["sparse_clusters"]:
        logger.info(f"  - 聚类 {cluster['cluster_id']}: {cluster['size']} 个样本, 特征: {cluster['characteristics']}")
    
    # 6. 查看生成增强结果
    logger.info("\n[步骤 6] 查看生成增强结果...")
    
    evolution_stats = iteration_summary["evolution_stats"]
    logger.info(f"  - 原始样本: {evolution_stats['original_count']}")
    logger.info(f"  - 重写样本: {evolution_stats['rewritten_count']}")
    logger.info(f"  - 生成样本: {evolution_stats['generated_count']}")
    logger.info(f"  - 最终样本: {evolution_stats['final_count']}")
    
    # 7. 查看 RAG 校验结果
    logger.info("\n[步骤 7] 查看 RAG 校验结果...")
    
    verification_stats = iteration_summary["verification_stats"]
    if verification_stats["total"] > 0:
        logger.info(f"  - 校验样本: {verification_stats['total']}")
        logger.info(f"  - 通过: {verification_stats['passed']} ({verification_stats['pass_rate']:.1%})")
        logger.info(f"  - 修正: {verification_stats['corrected']} ({verification_stats['correction_rate']:.1%})")
        logger.info(f"  - 拒绝: {verification_stats['rejected']} ({verification_stats['rejection_rate']:.1%})")
    else:
        logger.info("  - 无新生成样本需要校验")
    
    # 8. 保存优化后的数据集
    logger.info("\n[步骤 8] 保存优化后的数据集...")
    
    output_file = "test_optimized_dataset.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(optimized_dataset, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✓ 数据集已保存: {output_file}")
    
    # 9. 展示优化后的样本
    logger.info("\n[步骤 9] 展示优化后的样本...")
    
    logger.info("\n示例 1 - 原始无推理样本被重写:")
    for sample in optimized_dataset:
        if sample.get("question") == "10 - 3 = ?":
            logger.info(f"  问题: {sample['question']}")
            logger.info(f"  推理: {sample.get('chain_of_thought', '无')}")
            logger.info(f"  答案: {sample['answer']}")
            break
    
    logger.info("\n示例 2 - 新生成的样本:")
    new_samples = [s for s in optimized_dataset if s not in dataset]
    if new_samples:
        sample = new_samples[0]
        logger.info(f"  问题: {sample['question']}")
        logger.info(f"  推理: {sample.get('chain_of_thought', '无')[:100]}...")
        logger.info(f"  答案: {sample['answer']}")
    
    # 10. 系统统计
    logger.info("\n[步骤 10] 系统统计...")
    
    stats = optimizer.get_system_stats()
    logger.info(f"  - 总迭代次数: {stats['total_iterations']}")
    logger.info(f"  - 知识库统计: {stats['knowledge_base_stats']}")
    
    logger.info("\n"+"="*60)
    logger.info("测试完成!")
    logger.info("="*60)
    
    logger.info("\n查看详细报告:")
    logger.info("  - 语义分布报告: reports/iteration_0_semantic.json")
    logger.info("  - 推理分析报告: reports/iteration_0_reasoning.json")
    logger.info("  - 迭代总结: reports/iteration_0_summary.json")


if __name__ == "__main__":
    main()
