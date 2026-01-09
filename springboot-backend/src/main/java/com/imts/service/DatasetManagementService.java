package com.imts.service;

import com.imts.entity.Dataset;
import com.imts.repository.DatasetRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import reactor.core.publisher.Mono;

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
        log.info("上传数据集: name={}, size={}, type={}, domain={}", 
            name, file.getSize(), datasetType, domain);
        
        return Mono.fromCallable(() -> {
            // 生成数据集ID
            String datasetId = "dataset_" + UUID.randomUUID().toString().substring(0, 8);
            
            // 构建存储路径
            String storagePath = String.format("s3://bucket/datasets/%s/%s/%s",
                userId, datasetId, file.getOriginalFilename());
            
            // TODO: 实际上传到对象存储
            // storageClient.uploadStream(storagePath, file.getInputStream());
            
            log.info("文件已上传到对象存储: path={}", storagePath);
            
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
     * 查询数据集详情
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
     * 更新数据集元数据
     */
    @Transactional
    public Mono<Dataset> updateDatasetMetadata(
        String datasetId,
        String name,
        String description,
        Integer sampleCount
    ) {
        log.info("更新数据集元数据: datasetId={}", datasetId);
        
        return Mono.fromCallable(() -> {
            Dataset dataset = datasetRepository.findByDatasetId(datasetId)
                .orElseThrow(() -> new RuntimeException("数据集不存在: " + datasetId));
            
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
     * 删除数据集
     */
    @Transactional
    public Mono<Void> deleteDataset(String datasetId) {
        log.info("删除数据集: datasetId={}", datasetId);
        
        return Mono.fromCallable(() -> {
            Dataset dataset = datasetRepository.findByDatasetId(datasetId)
                .orElseThrow(() -> new RuntimeException("数据集不存在: " + datasetId));
            
            // TODO: 从对象存储删除文件
            // storageClient.delete(dataset.getStoragePath());
            
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
