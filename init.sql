
CREATE DATABASE IF NOT EXISTS log_db;
USE log_db;


CREATE TABLE IF NOT EXISTS server_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    ip_address VARCHAR(50),      
    timestamp DATETIME,         
    status INT,                
    log_level VARCHAR(20),     
    response VARCHAR(255)        
);
#test
INSERT INTO server_logs (ip_address, timestamp, status, log_level, response)
VALUES ('127.0.0.1', NOW(), 200, 'INFO', 'OK');