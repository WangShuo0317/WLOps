package com.imts.repository;

import com.imts.entity.TaskExecution;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * 任务执行记录仓储
 */
@Repository
public interface TaskExecutionRepository extends JpaRepository<TaskExecution, Long> {
    
    List<TaskExecution> findByTaskId(String taskId);
    
    List<TaskExecution> findByTaskIdOrderByIterationDesc(String taskId);
    
    Optional<TaskExecution> findByTaskIdAndIterationAndPhase(String taskId, Integer iteration, String phase);
    
    List<TaskExecution> findByTaskIdAndIteration(String taskId, Integer iteration);
}
