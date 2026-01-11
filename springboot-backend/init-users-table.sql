-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    real_name VARCHAR(50),
    role VARCHAR(20) DEFAULT 'USER',
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 插入默认测试用户（密码: admin123）
-- 密码使用 Base64 编码: YWRtaW4xMjM=
INSERT INTO users (username, password, email, real_name, role, created_at, updated_at)
VALUES 
('admin', 'YWRtaW4xMjM=', 'admin@example.com', '管理员', 'ADMIN', NOW(), NOW()),
('user1', 'dXNlcjEyMw==', 'user1@example.com', '用户1', 'USER', NOW(), NOW());

-- 密码说明：
-- admin 的密码: admin123 (Base64: YWRtaW4xMjM=)
-- user1 的密码: user123 (Base64: dXNlcjEyMw==)

SELECT 'Users table created successfully!' AS message;
