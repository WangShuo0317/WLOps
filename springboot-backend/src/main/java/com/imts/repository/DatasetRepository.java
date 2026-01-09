package com.imts.repository;

import com.imts.entity.Dataset;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * 数据集仓储
 */
@Repository
public interface DatasetRepository extends JpaRepository<Dataset, Long> {
    
    Optional<Dataset> findByDatasetId(String datasetId);
    
    List<Dataset> findByUserId(Long userId);
    
    List<Dataset> findByUserIdAndDomain(Long userId, String domain);
    
    List<Dataset> findBySourceDatasetId(String sourceDatasetId);
    
    boolean existsByDatasetId(String datasetId);
}
