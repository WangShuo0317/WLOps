package com.imts.controller;

import com.imts.entity.Dataset;
import com.imts.service.DatasetManagementService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import reactor.core.publisher.Mono;

import java.util.List;
import java.util.Map;

/**
 * 数据集管理控制器
 * 
 * 提供数据集CRUD的REST API
 */
@Slf4j
@RestController
@RequestMapping("/api/datasets")
@RequiredArgsConstructor
public class DatasetController {
    
    private final DatasetManagementService datasetService;
    
    /**
     * 上传数据集
     * 
     * POST /api/datasets/upload
     */
    @PostMapping("/upload")
    public Mono<ResponseEntity<Dataset>> uploadDataset(
        @RequestParam("file") MultipartFile file,
        @RequestParam("name") String name,
        @RequestParam(value = "description", required = false) String description,
        @RequestParam("datasetType") String datasetType,
        @RequestParam("domain") String domain,
        @RequestParam("userId") Long userId
    ) {
        log.info("上传数据集: name={}, size={}, type={}, domain={}", 
            name, file.getSize(), datasetType, domain);
        
        return datasetService.uploadDataset(
            file, name, description, datasetType, domain, userId
        ).map(ResponseEntity::ok)
         .onErrorResume(error -> {
             log.error("上传数据集失败", error);
             return Mono.just(ResponseEntity.internalServerError().build());
         });
    }
    
    /**
     * 查询数据集详情
     * 
     * GET /api/datasets/{datasetId}
     */
    @GetMapping("/{datasetId}")
    public Mono<ResponseEntity<Dataset>> getDataset(
        @PathVariable String datasetId
    ) {
        return datasetService.getDataset(datasetId)
            .map(ResponseEntity::ok)
            .onErrorResume(error -> 
                Mono.just(ResponseEntity.notFound().build())
            );
    }
    
    /**
     * 查询用户的所有数据集
     * 
     * GET /api/datasets/user/{userId}
     */
    @GetMapping("/user/{userId}")
    public Mono<ResponseEntity<List<Dataset>>> getUserDatasets(
        @PathVariable Long userId
    ) {
        return datasetService.getUserDatasets(userId)
            .map(ResponseEntity::ok);
    }
    
    /**
     * 查询用户指定领域的数据集
     * 
     * GET /api/datasets/user/{userId}/domain/{domain}
     */
    @GetMapping("/user/{userId}/domain/{domain}")
    public Mono<ResponseEntity<List<Dataset>>> getUserDatasetsByDomain(
        @PathVariable Long userId,
        @PathVariable String domain
    ) {
        return datasetService.getUserDatasetsByDomain(userId, domain)
            .map(ResponseEntity::ok);
    }
    
    /**
     * 更新数据集元数据
     * 
     * PUT /api/datasets/{datasetId}
     */
    @PutMapping("/{datasetId}")
    public Mono<ResponseEntity<Dataset>> updateDatasetMetadata(
        @PathVariable String datasetId,
        @RequestBody Map<String, Object> request
    ) {
        log.info("更新数据集元数据: datasetId={}", datasetId);
        
        String name = (String) request.get("name");
        String description = (String) request.get("description");
        Integer sampleCount = request.get("sampleCount") != null 
            ? Integer.valueOf(request.get("sampleCount").toString()) 
            : null;
        
        return datasetService.updateDatasetMetadata(
            datasetId, name, description, sampleCount
        ).map(ResponseEntity::ok);
    }
    
    /**
     * 删除数据集
     * 
     * DELETE /api/datasets/{datasetId}
     */
    @DeleteMapping("/{datasetId}")
    public Mono<ResponseEntity<Map<String, String>>> deleteDataset(
        @PathVariable String datasetId
    ) {
        log.info("删除数据集: {}", datasetId);
        
        return datasetService.deleteDataset(datasetId)
            .then(Mono.just(ResponseEntity.ok(Map.of(
                "message", "数据集已删除",
                "datasetId", datasetId
            ))))
            .onErrorResume(error -> 
                Mono.just(ResponseEntity.badRequest().body(Map.of(
                    "error", error.getMessage()
                )))
            );
    }
    
    /**
     * 获取数据集下载URL
     * 
     * GET /api/datasets/{datasetId}/download-url
     */
    @GetMapping("/{datasetId}/download-url")
    public Mono<ResponseEntity<Map<String, String>>> getDownloadUrl(
        @PathVariable String datasetId
    ) {
        return datasetService.getDownloadUrl(datasetId)
            .map(url -> ResponseEntity.ok(Map.of(
                "datasetId", datasetId,
                "downloadUrl", url
            )));
    }
    
    /**
     * 查询优化后的数据集
     * 
     * GET /api/datasets/{datasetId}/optimized
     */
    @GetMapping("/{datasetId}/optimized")
    public Mono<ResponseEntity<List<Dataset>>> getOptimizedDatasets(
        @PathVariable String datasetId
    ) {
        return datasetService.getOptimizedDatasets(datasetId)
            .map(ResponseEntity::ok);
    }
}
