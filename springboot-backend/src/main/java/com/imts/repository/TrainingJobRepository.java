package com.imts.repository;

import com.imts.entity.TrainingJob;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface TrainingJobRepository extends JpaRepository<TrainingJob, Long> {
    
    Optional<TrainingJob> findByJobId(String jobId);
}
