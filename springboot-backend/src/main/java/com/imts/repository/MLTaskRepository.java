package com.imts.repository;

import com.imts.entity.MLTask;
import com.imts.enums.TaskStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * ML任务仓储
 */
@Repository
public interface MLTaskRepository extends JpaRepository<MLTask, Long> {
    
    Optional<MLTask> findByTaskId(String taskId);
    
    List<MLTask> findByUserId(Long userId);
    
    List<MLTask> findByUserIdAndStatus(Long userId, TaskStatus status);
    
    List<MLTask> findByStatus(TaskStatus status);
    
    boolean existsByTaskId(String taskId);
}
