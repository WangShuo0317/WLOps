-- 创建数据库表结构
USE imts;

-- 1. 数据集表
CREATE TABLE IF NOT EXISTS dataset (
    dataset_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    storage_path VARCHAR(500),
    file_size BIGINT,
    sample_count INT,
    dataset_type VARCHAR(50),
    domain VARCHAR(100),
    user_id BIGINT NOT NULL,
    is_optimized BOOLEAN DEFAULT FALSE,
    source_dataset_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_source_dataset (source_dataset_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. 机器学习任务表
CREATE TABLE IF NOT EXISTS ml_task (
    task_id VARCHAR(255) PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    task_mode VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    model_name VARCHAR(255) NOT NULL,
    dataset_id VARCHAR(255) NOT NULL,
    user_id BIGINT NOT NULL,
    hyperparameters TEXT,
    current_dataset_id VARCHAR(255),
    current_iteration INT DEFAULT 0,
    max_iterations INT,
    performance_threshold DOUBLE,
    latest_model_path VARCHAR(500),
    latest_evaluation_path VARCHAR(500),
    latest_score DOUBLE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_dataset_id (dataset_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. 任务执行记录表
CREATE TABLE IF NOT EXISTS task_execution (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL,
    iteration INT NOT NULL,
    phase VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    input_dataset_id VARCHAR(255),
    output_dataset_id VARCHAR(255),
    model_path VARCHAR(500),
    evaluation_path VARCHAR(500),
    score DOUBLE,
    error_message TEXT,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    duration_seconds BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_iteration (task_id, iteration),
    INDEX idx_phase (task_id, phase)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 插入测试数据
-- 插入测试数据集
INSERT INTO dataset (dataset_id, name, description, storage_path, file_size, sample_count, dataset_type, domain, user_id, is_optimized)
VALUES 
('test_dataset_001', '测试数学数据集', '用于测试的数学推理数据集', 's3://bucket/datasets/test_dataset_001.json', 1048576, 1000, 'training', 'math', 1, FALSE),
('test_dataset_002', '测试语文数据集', '用于测试的语文理解数据集', 's3://bucket/datasets/test_dataset_002.json', 2097152, 2000, 'training', 'chinese', 1, FALSE);

SELECT 'Database tables created successfully!' AS message;
