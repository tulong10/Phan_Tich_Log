-- Tạo database nếu chưa tồn tại
CREATE DATABASE IF NOT EXISTS log_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE log_db;

CREATE TABLE IF NOT EXISTS server_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    
    ip_address VARCHAR(45) NOT NULL,  
    
    -- Thời gian log
    timestamp DATETIME NOT NULL,
    
    -- HTTP status code
    status INT NOT NULL,
    
    log_level ENUM('INFO', 'WARNING', 'ERROR', 'DEBUG', 'CRITICAL') NOT NULL DEFAULT 'INFO',
    

    response VARCHAR(255) NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    

    INDEX idx_timestamp (timestamp),
    INDEX idx_ip_address (ip_address),
    INDEX idx_status (status),
    INDEX idx_log_level (log_level),
    INDEX idx_composite (timestamp, log_level, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

# Database test 
INSERT INTO server_logs (ip_address, timestamp, status, log_level, response) VALUES
    ('127.0.0.1', '2025-12-01 10:00:00', 200, 'INFO', 'OK'),
    ('192.168.1.100', '2025-12-01 10:05:00', 404, 'WARNING', 'Not Found'),
    ('10.0.0.50', '2025-12-01 10:10:00', 500, 'ERROR', 'Internal Server Error'),
    ('172.16.0.1', '2025-12-01 10:15:00', 200, 'INFO', 'OK'),
    ('192.168.1.100', '2025-12-01 10:20:00', 403, 'WARNING', 'Forbidden'),
    ('8.8.8.8', '2025-12-01 10:25:00', 503, 'ERROR', 'Service Unavailable'),
    ('127.0.0.1', '2025-12-01 10:30:00', 301, 'INFO', 'Moved Permanently'),
    ('203.0.113.45', '2025-12-01 10:35:00', 401, 'WARNING', 'Unauthorized');


CREATE OR REPLACE VIEW log_statistics AS
SELECT 
    DATE(timestamp) as date,
    log_level,
    COUNT(*) as count,
    COUNT(DISTINCT ip_address) as unique_ips
FROM server_logs
GROUP BY DATE(timestamp), log_level
ORDER BY date DESC, log_level;

-- View để xem top IP có nhiều lỗi nhất
CREATE OR REPLACE VIEW top_error_ips AS
SELECT 
    ip_address,
    COUNT(*) as error_count,
    MAX(timestamp) as last_error
FROM server_logs
WHERE log_level IN ('ERROR', 'WARNING')
GROUP BY ip_address
ORDER BY error_count DESC
LIMIT 10;

-- Stored procedure để xóa log cũ hơn N ngày
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS clean_old_logs(IN days_old INT)
BEGIN
    DELETE FROM server_logs 
    WHERE timestamp < DATE_SUB(NOW(), INTERVAL days_old DAY);
    
    SELECT ROW_COUNT() as deleted_rows;
END //
DELIMITER ;

-- Kiểm tra dữ liệu đã insert
SELECT 'Database initialized successfully!' as status;
SELECT COUNT(*) as total_records FROM server_logs;