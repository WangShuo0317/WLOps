package com.imts.service;

import com.imts.entity.Dataset;
import com.imts.repository.DatasetRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import reactor.core.publisher.Mono;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

/**
 * 数据集管理服务
 * 
 * 职责：
 * 1. 数据集的CRUD操作
 * 2. 文件上传到对象存储（流式上传）
 * 3. 元数据记录
 * 
 * 约束：
 * - 严禁在此阶段进行任何数据清洗或优化操作
 * - 仅负责文件存储和元数据管理
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DatasetManagementService {
    
    private final DatasetRepository datasetRepository;
    // TODO: 注入对象存储客户端（MinIO/S3）
    // private final ObjectStorageClient storageClient;
    
    /**
     * 上传数据集
     * 
     * 流程：
     * 1. 流式上传文件到对象存储
     * 2. 记录元数据到数据库
     * 3. 返回数据集ID
     */
    @Transactional
    public Mono<Dataset> uploadDataset(
        MultipartFile file,
        String name,
        String description,
        String datasetType,
        String domain,
        Long userId
    ) {
        log.info("上传数据集: name={}, size={}, type={}, domain={}, userId={}", 
            name, file.getSize(), datasetType, domain, userId);
        
        return Mono.fromCallable(() -> {
            // 生成数据集ID
            String datasetId = "dataset_" + UUID.randomUUID().toString().substring(0, 8);
            
            // 构建本地存储路径 - 使用项目下的 Dataset 目录
            String baseDir = "Dataset";  // 项目根目录下的 Dataset 文件夹
            String userDir = String.format("%s/user_%s", baseDir, userId);
            String datasetDir = String.format("%s/%s", userDir, datasetId);
            
            // 创建目录
            Path datasetPath = Paths.get(datasetDir);
            Files.createDirectories(datasetPath);
            
            // 保存文件
            String fileName = file.getOriginalFilename();
            Path filePath = datasetPath.resolve(fileName);
            file.transferTo(filePath.toFile());
            
            // 构建存储路径（相对路径，用于数据库记录）
            String storagePath = String.format("%s/%s", datasetDir, fileName);
            
            log.info("文件已保存到本地: path={}, absolutePath={}", 
                storagePath, filePath.toAbsolutePath());
            
            // 创建数据集元数据
            Dataset dataset = Dataset.builder()
                .datasetId(datasetId)
                .name(name)
                .description(description)
                .storagePath(storagePath)
                .fileSize(file.getSize())
                .datasetType(datasetType)
                .domain(domain)
                .userId(userId)
                .isOptimized(false)
                .createdAt(LocalDateTime.now())
                .build();
            
            return datasetRepository.save(dataset);
        });
    }
    
    /**
     * 查询数据集详情（带用户验证）
     */
    public Mono<Dataset> getDataset(String datasetId, Long userId) {
        return Mono.fromCallable(() -> {
            Dataset dataset = datasetRepository.findByDatasetId(datasetId)
                .orElseThrow(() -> new RuntimeException("数据集不存在: " + datasetId));
            
            // 用户隔离验证
            if (!dataset.getUserId().equals(userId)) {
                throw new RuntimeException("无权访问此数据集");
            }
            
            return dataset;
        });
    }
    
    /**
     * 查询数据集详情（不验证用户，用于内部调用）
     */
    public Mono<Dataset> getDataset(String datasetId) {
        return Mono.fromCallable(() -> datasetRepository.findByDatasetId(datasetId)
            .orElseThrow(() -> new RuntimeException("数据集不存在: " + datasetId)));
    }
    
    /**
     * 查询用户的所有数据集
     */
    public Mono<List<Dataset>> getUserDatasets(Long userId) {
        return Mono.fromCallable(() -> datasetRepository.findByUserId(userId));
    }
    
    /**
     * 查询用户指定领域的数据集
     */
    public Mono<List<Dataset>> getUserDatasetsByDomain(Long userId, String domain) {
        return Mono.fromCallable(() -> 
            datasetRepository.findByUserIdAndDomain(userId, domain)
        );
    }
    
    /**
     * 更新数据集元数据（带用户验证）
     */
    @Transactional
    public Mono<Dataset> updateDatasetMetadata(
        String datasetId,
        Long userId,
        String name,
        String description,
        Integer sampleCount
    ) {
        log.info("更新数据集元数据: datasetId={}, userId={}", datasetId, userId);
        
        return Mono.fromCallable(() -> {
            Dataset dataset = datasetRepository.findByDatasetId(datasetId)
                .orElseThrow(() -> new RuntimeException("数据集不存在: " + datasetId));
            
            // 用户隔离验证
            if (!dataset.getUserId().equals(userId)) {
                throw new RuntimeException("无权修改此数据集");
            }
            
            if (name != null) {
                dataset.setName(name);
            }
            if (description != null) {
                dataset.setDescription(description);
            }
            if (sampleCount != null) {
                dataset.setSampleCount(sampleCount);
            }
            
            dataset.setUpdatedAt(LocalDateTime.now());
            
            return datasetRepository.save(dataset);
        });
    }
    
    /**
     * 删除数据集（带用户验证）
     */
    @Transactional
    public Mono<Void> deleteDataset(String datasetId, Long userId) {
        log.info("删除数据集: datasetId={}, userId={}", datasetId, userId);
        
        return Mono.fromCallable(() -> {
            Dataset dataset = datasetRepository.findByDatasetId(datasetId)
                .orElseThrow(() -> new RuntimeException("数据集不存在: " + datasetId));
            
            // 用户隔离验证
            if (!dataset.getUserId().equals(userId)) {
                throw new RuntimeException("无权删除此数据集");
            }
            
            // 删除物理文件
            try {
                Path filePath = Paths.get(dataset.getStoragePath());
                if (Files.exists(filePath)) {
                    Files.delete(filePath);
                    log.info("物理文件已删除: {}", filePath);
                    
                    // 尝试删除空目录
                    Path parentDir = filePath.getParent();
                    if (parentDir != null && Files.isDirectory(parentDir)) {
                        try {
                            Files.delete(parentDir);
                            log.info("空目录已删除: {}", parentDir);
                        } catch (Exception e) {
                            // 目录不为空，忽略
                        }
                    }
                }
            } catch (IOException e) {
                log.warn("删除物理文件失败: {}", e.getMessage());
            }
            
            // 删除元数据
            datasetRepository.delete(dataset);
            
            log.info("数据集已删除: datasetId={}, path={}", datasetId, dataset.getStoragePath());
            
            return null;
        }).then();
    }
    
    /**
     * 获取数据集下载URL
     */
    public Mono<String> getDownloadUrl(String datasetId) {
        return Mono.fromCallable(() -> {
            Dataset dataset = datasetRepository.findByDatasetId(datasetId)
                .orElseThrow(() -> new RuntimeException("数据集不存在: " + datasetId));
            
            // TODO: 生成预签名URL
            // return storageClient.generatePresignedUrl(dataset.getStoragePath(), 3600);
            
            return dataset.getStoragePath();
        });
    }
    
    /**
     * 查询优化后的数据集
     */
    public Mono<List<Dataset>> getOptimizedDatasets(String sourceDatasetId) {
        return Mono.fromCallable(() -> 
            datasetRepository.findBySourceDatasetId(sourceDatasetId)
        );
    }
}
