-- 1. Tạo Database
CREATE DATABASE IF NOT EXISTS log_db;
USE log_db;

-- 2. Tạo bảng server_logs
-- LƯU Ý: Tên cột ở đây phải khớp y hệt dòng INSERT trong code Python của bạn
CREATE TABLE IF NOT EXISTS server_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    ip_address VARCHAR(50),      -- Khớp với code: ip_address
    timestamp DATETIME,          -- Khớp với code: timestamp
    status INT,                  -- Khớp với code: status (Lưu ý: code bạn dùng 'status' chứ không phải 'status_code')
    log_level VARCHAR(20),       -- Khớp với code: log_level
    response VARCHAR(255)        -- Khớp với code: response (Để VARCHAR cho an toàn, chứa được cả text hoặc số)
);

-- 3. Dữ liệu mẫu để test
INSERT INTO server_logs (ip_address, timestamp, status, log_level, response)
VALUES ('127.0.0.1', NOW(), 200, 'INFO', 'OK');