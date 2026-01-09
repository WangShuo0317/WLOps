package com.imts.service;

import com.imts.client.DataAnalyzerServiceClient;
import com.imts.dto.analyzer.OptimizationResult;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.List;
import java.util.Map;

/**
 * 数据优化服务
 * 
 * 封装数据优化的业务逻辑
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DataOptimizationService {
    
    private final DataAnalyzerServiceClient dataAnalyzerClient;
    
    /**
     * 智能优化数据集
     * 
     * 根据数据集大小自动选择同步或异步处理
     * 
     * @param dataset 原始数据集
     * @param knowledgeBase 知识库
     * @return 优化结果
     */
    public Mono<OptimizationResult> smartOptimize(
        List<Map<String, Object>> dataset,
        List<String> knowledgeBase
    ) {
        log.info("智能优化数据集: size={}", dataset.size());
        
        // 根据数据集大小选择处理方式
        if (dataset.size() <= 100) {
            // 小数据集：同步处理
            log.info("使用同步处理（数据集较小）");
            return dataAnalyzerClient.optimizeDatasetSync(dataset, knowledgeBase);
        } else {
            // 大数据集：异步处理
            log.info("使用异步处理（数据集较大）");
            return dataAnalyzerClient.optimizeDatasetAsync(dataset, knowledgeBase)
                .flatMap(response -> {
                    // 轮询等待结果
                    return pollForResult(response.getTaskId());
                });
        }
    }
    
    /**
     * 轮询异步任务结果
     * 
     * @param taskId 任务ID
     * @return 优化结果
     */
    private Mono<OptimizationResult> pollForResult(String taskId) {
        return dataAnalyzerClient.getOptimizationResult(taskId)
            .flatMap(result -> {
                if ("completed".equals(result.getStatus())) {
                    return Mono.just(result);
                } else if ("failed".equals(result.getStatus())) {
                    return Mono.error(new RuntimeException("优化任务失败: " + result.getError()));
                } else {
                    // 任务仍在处理中，等待后重试
                    return Mono.delay(Duration.ofSeconds(5))
                        .then(pollForResult(taskId));
                }
            });
    }
    
    /**
     * 预处理数据集
     * 
     * 在优化前进行数据清洗和格式化
     * 
     * @param rawDataset 原始数据
     * @return 预处理后的数据集
     */
    public List<Map<String, Object>> preprocessDataset(List<Map<String, Object>> rawDataset) {
        log.info("预处理数据集: size={}", rawDataset.size());
        
        return rawDataset.stream()
            .filter(item -> item.containsKey("question") && item.containsKey("answer"))
            .filter(item -> {
                String question = String.valueOf(item.get("question"));
                String answer = String.valueOf(item.get("answer"));
                return question != null && !question.trim().isEmpty() &&
                       answer != null && !answer.trim().isEmpty();
            })
            .toList();
    }
    
    /**
     * 构建默认知识库
     * 
     * @param domain 领域
     * @return 知识库
     */
    public List<String> buildDefaultKnowledgeBase(String domain) {
        return switch (domain.toLowerCase()) {
            case "math" -> List.of(
                "加法运算：两个数相加，得到它们的和。例如：3+5=8",
                "减法运算：从一个数中减去另一个数，得到差。例如：10-3=7",
                "乘法运算：一个数重复相加若干次。例如：3×4=12",
                "除法运算：将一个数平均分成若干份。例如：12÷3=4",
                "长方形面积公式：面积=长×宽",
                "正方形面积公式：面积=边长×边长"
            );
            case "language" -> List.of(
                "语法规则：主语+谓语+宾语的基本句式结构",
                "修辞手法：比喻、拟人、排比等表达技巧",
                "阅读理解：理解文章主旨、细节和作者意图"
            );
            default -> List.of(
                "逻辑推理：从已知条件推导出结论的思维过程",
                "因果关系：原因和结果之间的逻辑联系",
                "分类归纳：将事物按特征分组整理"
            );
        };
    }
    
    /**
     * 验证优化结果
     * 
     * @param result 优化结果
     * @return 是否通过验证
     */
    public boolean validateOptimizationResult(OptimizationResult result) {
        if (result == null || result.getOptimizedDataset() == null) {
            return false;
        }
        
        // 检查数据质量
        List<Map<String, Object>> dataset = result.getOptimizedDataset();
        
        // 验证所有样本都包含推理过程
        boolean allHaveReasoning = dataset.stream()
            .allMatch(item -> 
                item.containsKey("chain_of_thought") || 
                item.containsKey("reasoning") || 
                item.containsKey("rationale")
            );
        
        if (!allHaveReasoning) {
            log.warn("优化结果验证失败：部分样本缺少推理过程");
            return false;
        }
        
        // 检查质量提升
        Map<String, Object> stats = result.getStatistics();
        if (stats != null) {
            Object improvement = stats.get("quality_improvement");
            if (improvement instanceof Number && ((Number) improvement).doubleValue() < 10.0) {
                log.warn("优化结果验证失败：质量提升不足 {}%", improvement);
                return false;
            }
        }
        
        log.info("优化结果验证通过：dataset_size={}, all_have_reasoning={}", 
            dataset.size(), allHaveReasoning);
        return true;
    }
}
