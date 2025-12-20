import re 
from datetime import datetime
import streamlit as st
from typing import List, Tuple, Dict, Optional

LOG_PATTERN = re.compile(
    r'(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) '  
    r'- - '                                         
    r'\[(?P<time>[^\]]+)\] '                        
    r'"(?P<method>\w+) '                            
    r'(?P<path>[^\s]+) '                            
    r'HTTP/[0-9.]+" '                                
    r'(?P<status>\d{3}) '                           
    r'(?P<size>\d+|-)'                               
)

STATUS_MESSAGES ={
    200: "OK",
    201: "Created",
    204: "No Content",

    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",

    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",

    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}

def determine_log_level (status_code : int) ->str:
  """
    Hàm dùng dể phân loại mức độ log dựa trên status code
  """
  if status_code <= 400:
    return "INFO"
  elif status_code < 500:
    return "WARNING"
  else:
    return "ERROR"
  

def determine_response_text(status_code: int) ->str:
  
  return STATUS_MESSAGES.get(status_code, f"HTTP {status_code}")

def validate_ip (ip_address: str) ->bool:
  try:
    parts = ip_address.split(".")

    if len(parts) !=4:
        return False
    for part in parts:
        num = int(part)
    if num <0 or num > 255:
        return False
    return True
  except ValueError:
    return False

def parse_timestamp(time_str: str) -> Optional[datetime]:
    """
    Parse timestamp từ log với nhiều format khác nhau
    
    Args:
        time_str (str): Chuỗi thời gian từ log
    
    Returns:
        datetime hoặc None nếu parse thất bại
    """
    time_str = time_str.split()[0] if ' ' in time_str else time_str
    
    # Thử các format phổ biến
    formats = [
        '%d/%b/%Y:%H:%M:%S',      # 04/Dec/2025:10:00:00
        '%d/%m/%Y:%H:%M:%S',      # 04/12/2025:10:00:00
        '%Y-%m-%d %H:%M:%S',      # 2025-12-04 10:00:00
        '%d-%b-%Y %H:%M:%S',      # 04-Dec-2025 10:00:00
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    
    return None
  

def parse_log_file(uploaded_file) -> Tuple[List[Tuple], Dict]:
    """
    Đọc file log và trả về danh sách các bản ghi đã parse
    
    Returns:
        tuple: (data_list, stats_dict)
            - data_list: List các tuple (ip_address, timestamp, status, log_level, response)
            - stats_dict: Dictionary chứa thống kê parse
    """
    data_list = []
    stats = {
        'total_lines': 0,
        'parsed_success': 0,
        'parse_errors': 0,
        'invalid_ips': 0,
        'timestamp_errors': 0,
        'invalid_status': 0,
        'empty_lines': 0
    }
    

    try:
        content = uploaded_file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        try:
            content = uploaded_file.getvalue().decode("latin-1")
            st.info(" File được decode bằng Latin-1 encoding")
        except Exception as e:
            st.error(f" Không thể đọc file: {e}")
            return [], stats
    
    # Parse từng dòng log
    lines = content.splitlines()
    
    # Progress bar cho file lớn > 100 dòng
    if len(lines) > 100:
        progress_bar = st.progress(0)
        status_text = st.empty()
    else:
        progress_bar = None
        status_text = None
    
    for line_num, line in enumerate(lines, 1):
        stats['total_lines'] += 1
        
        # Update progress bar mỗi 100 dòng
        if progress_bar and line_num % 100 == 0:
            progress = min(line_num / len(lines), 1.0)
            progress_bar.progress(progress)
            status_text.text(f"Đang xử lý dòng {line_num}/{len(lines)}...")
        
        # Bỏ qua dòng trống
        line = line.strip()
        if not line:
            stats['empty_lines'] += 1
            continue
        
        # Tìm kiếm pattern trong dòng log
        match = LOG_PATTERN.search(line)
        if not match:
            stats['parse_errors'] += 1
            if stats['parse_errors'] <= 5:  # Chỉ hiện 5 cảnh báo đầu
                st.warning(f"⚠️ Dòng {line_num}: Không khớp pattern log")
            continue
        
        try:
            group = match.groupdict()
            
            # 1. Validate IP address
            ip_address = group['ip']
            if not validate_ip(ip_address):
                stats['invalid_ips'] += 1
                if stats['invalid_ips'] <= 3:
                    st.warning(f"⚠️ Dòng {line_num}: IP không hợp lệ '{ip_address}'")
                continue
            
            # 2. Parse timestamp
            timestamp = parse_timestamp(group['time'])
            if timestamp is None:
                stats['timestamp_errors'] += 1
                if stats['timestamp_errors'] <= 3:
                    st.warning(f"⚠️ Dòng {line_num}: Không parse được timestamp '{group['time']}'")
                continue
            
            # 3. Parse và validate status code
            try:
                status_code = int(group['status'])
                if not (100 <= status_code <= 599):
                    raise ValueError(f"Status code ngoài phạm vi HTTP")
            except ValueError as e:
                stats['invalid_status'] += 1
                if stats['invalid_status'] <= 3:
                    st.warning(f"⚠️ Dòng {line_num}: Status code không hợp lệ '{group['status']}'")
                continue
            
            # 4. Tạo các trường tự động
            log_level = determine_log_level(status_code)
            response_text = determine_response_text(status_code)

            entry = (
                ip_address,
                timestamp,
                status_code,
                log_level,
                response_text
            )
            
            data_list.append(entry)
            stats['parsed_success'] += 1
            
        except Exception as e:
            stats['parse_errors'] += 1
            if stats['parse_errors'] <= 3:
                st.warning(f"⚠️ Dòng {line_num}: Lỗi không xác định - {str(e)[:100]}")
            continue
    
    # Clear progress bar
    if progress_bar:
        progress_bar.empty()
        status_text.empty()
    
    # Hiển thị thống kê chi tiết
    if stats['total_lines'] > 0:
        success_rate = (stats['parsed_success'] / stats['total_lines']) * 100
        

        if success_rate >= 90:
            box_type = "success"
            emoji = "✅"
        elif success_rate >= 70:
            box_type = "info"
            emoji = "ℹ️"
        else:
            box_type = "warning"
            emoji = "⚠️"
        
        stats_message = f"""
        {emoji} **Kết quả parse log:**
        
        **Tổng quan:**
        - Tổng số dòng: **{stats['total_lines']:,}**
        - Parse thành công: **{stats['parsed_success']:,}** ({success_rate:.1f}%)
        - Dòng trống: **{stats['empty_lines']:,}**
        
        **Chi tiết lỗi:**
        - Không khớp pattern: **{stats['parse_errors']:,}**
        - IP không hợp lệ: **{stats['invalid_ips']:,}**
        - Lỗi timestamp: **{stats['timestamp_errors']:,}**
        - Status code không hợp lệ: **{stats['invalid_status']:,}**
        """
        
        if box_type == "success":
            st.success(stats_message)
        elif box_type == "info":
            st.info(stats_message)
        else:
            st.warning(stats_message)
        
        # Cảnh báo nếu quá nhiều lỗi
        total_errors = (stats['parse_errors'] + stats['invalid_ips'] + 
                       stats['timestamp_errors'] + stats['invalid_status'])
        
        if total_errors > stats['parsed_success']:
            st.error("""
            ⚠️ Số dòng lỗi nhiều hơn số dòng thành công!
            
            Gợi ý khắc phục:
            1. Kiểm tra format log có đúng chuẩn Apache/Nginx không
            2. Xem mẫu log mong đợi: `127.0.0.1 - - [04/Dec/2025:10:00:00 +0700] "GET /index.html HTTP/1.1" 200 1024`
            3. Kiểm tra encoding file (UTF-8 hoặc Latin-1)
            """)
    
    return data_list, stats

def generate_sample_log(num_lines: int = 10) -> str:
    """
    Tạo file log mẫu để test
  
    """
    import random
    from datetime import timedelta
    
    ips = ['192.168.1.100', '10.0.0.50', '172.16.0.1', '203.0.113.45', '8.8.8.8']
    methods = ['GET', 'POST', 'PUT', 'DELETE']
    paths = ['/index.html', '/api/users', '/login', '/dashboard', '/images/logo.png']
    statuses = [200, 200, 200, 404, 500, 403, 301]  
    
    logs = []
    base_time = datetime(2025, 12, 4, 10, 0, 0)
    
    for i in range(num_lines):
        ip = random.choice(ips)
        method = random.choice(methods)
        path = random.choice(paths)
        status = random.choice(statuses)
        size = random.randint(100, 5000)
        timestamp = base_time + timedelta(seconds=i*10)
        time_str = timestamp.strftime('%d/%b/%Y:%H:%M:%S')
        
        log_line = f'{ip} - - [{time_str} +0700] "{method} {path} HTTP/1.1" {status} {size}'
        logs.append(log_line)
    
    return '\n'.join(logs)


