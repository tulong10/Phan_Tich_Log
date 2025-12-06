
import pandas as pd
import mysql.connector
from mysql.connector import Error, pooling
import streamlit as st
import os
from typing import List, Tuple, Optional
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT', 3306))
}

@st.cache_resource
def get_connection_pool():

    try:
        pool = pooling.MySQLConnectionPool(
            pool_name="log_pool",
            pool_size=5,  # Số kết nối tối đa trong pool
            pool_reset_session=True,
            **DB_CONFIG
        )
        st.success(" Kết nối database thành công!")
        return pool
    except Error as err:
        st.error(f" Lỗi tạo connection pool: {err}")
        return None

@contextmanager # Cho phép sử dụng với 'with' statement và 'as' và đảm bảo đóng kết nối.
def get_db_connection():

    pool = get_connection_pool()
    if pool is None:
        yield None 
        return
    
    conn = None
    try:
        conn = pool.get_connection()
        yield conn
    except Error as err:
        st.error(f"Lỗi kết nối database: {err}")
        yield None
    finally:
        if conn and conn.is_connected():
            conn.close()

def get_data_to_dataframe() -> pd.DataFrame:
    """
    Lấy toàn bộ dữ liệu từ bảng server_logs
    
    Returns:
        pd.DataFrame: DataFrame chứa dữ liệu log, hoặc DataFrame rỗng nếu lỗi
    """
    with get_db_connection() as conn:
        if conn is None:
            st.warning(" Không thể kết nối database")
            return pd.DataFrame()
        
        try:
            query = "SELECT * FROM server_logs ORDER BY timestamp DESC"
            df = pd.read_sql(query, conn)
            
            # Convert timestamp sang datetime nếu chưa phải
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            st.success(f"Đã tải {len(df)} bản ghi từ database")
            return df
            
        except Exception as e:
            st.error(f" Lỗi khi đọc dữ liệu: {e}")
            return pd.DataFrame()

def save_log_data(list_data: List[Tuple]) -> bool:
    """
    Lưu danh sách log vào database
    
    Args:
        list_data: List các tuple (ip_address, timestamp, status, log_level, response)
    
    Returns:
        bool: True nếu thành công, False nếu có lỗi
    """ 
    if not list_data:
        st.warning("Không có dữ liệu để lưu")
        return False
    
    with get_db_connection() as conn:
        if conn is None:
            return False
        
        cursor = None
        try:
            cursor = conn.cursor()
            
            query = """
                INSERT INTO server_logs 
                (ip_address, timestamp, status, log_level, response) 
                VALUES (%s, %s, %s, %s, %s)
            """

            cursor.executemany(query, list_data)
            conn.commit()
            
            st.success(f"Đã lưu {cursor.rowcount} vào database")
            return True
            
        except Error as e:
            st.error(f" Lỗi khi lưu dữ liệu: {e}")
            if conn:
                conn.rollback()  # Rollback nếu có lỗi
            return False
            
        finally:
            if cursor:
                cursor.close()

def clear_all_logs() -> bool:
    """
    Xóa toàn bộ dữ liệu trong bảng server_logs
    
    Returns:
        bool: True nếu thành công
    """
    with get_db_connection() as conn:
        if conn is None:
            return False
        
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM server_logs")
            conn.commit()
            
            st.success(f"Đã xóa {cursor.rowcount} bản ghi")
            return True
            
        except Error as e:
            st.error(f"Lỗi khi xóa dữ liệu: {e}")
            if conn:
                conn.rollback()
            return False
            
        finally:
            if cursor:
                cursor.close()

def get_logs_by_filters(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    log_level: Optional[str] = None,
    ip_address: Optional[str] = None,
    min_status: Optional[int] = None,
    max_status: Optional[int] = None
) -> pd.DataFrame:
    """
    Lấy dữ liệu log với các bộ lọc tùy chọn
    
    Args:
        start_date: Ngày bắt đầu (YYYY-MM-DD)
        end_date: Ngày kết thúc (YYYY-MM-DD)
        log_level: Mức độ log ('INFO', 'WARNING', 'ERROR')
        ip_address: Địa chỉ IP cần lọc
        min_status: Status code tối thiểu
        max_status: Status code tối đa
    
    Returns:
        pd.DataFrame: DataFrame chứa kết quả lọc
    """
    with get_db_connection() as conn:
        if conn is None:
            return pd.DataFrame()
        
        # Build query động dựa trên filters
        query = "SELECT * FROM server_logs WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND timestamp >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= %s"
            params.append(end_date)
        
        if log_level:
            query += " AND log_level = %s"
            params.append(log_level)
        
        if ip_address:
            query += " AND ip_address = %s"
            params.append(ip_address)
        
        if min_status:
            query += " AND status >= %s"
            params.append(min_status)
        
        if max_status:
            query += " AND status <= %s"
            params.append(max_status)
        
        query += " ORDER BY timestamp DESC"
        
        try:
            df = pd.read_sql(query, conn, params=params)
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        except Exception as e:
            st.error(f"Lỗi khi lọc dữ liệu: {e}")
            return pd.DataFrame()

def get_statistics() -> dict:
    """
    Lấy thống kê tổng quan về logs
    
    Returns:
        dict: Dictionary chứa các thống kê
    """
    with get_db_connection() as conn:
        if conn is None:
            return {}
        
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Query thống kê
            stats_query = """
                SELECT 
                    COUNT(*) as total_logs,
                    COUNT(DISTINCT ip_address) as unique_ips,
                    SUM(CASE WHEN log_level = 'ERROR' THEN 1 ELSE 0 END) as error_count,
                    SUM(CASE WHEN log_level = 'WARNING' THEN 1 ELSE 0 END) as warning_count,
                    SUM(CASE WHEN log_level = 'INFO' THEN 1 ELSE 0 END) as info_count,
                    MIN(timestamp) as earliest_log,
                    MAX(timestamp) as latest_log
                FROM server_logs
            """
            
            cursor.execute(stats_query)
            result = cursor.fetchone()
            
            return result if result else {}
            
        except Error as e:
            st.error(f"Lỗi khi lấy thống kê: {e}")
            return {}
            
        finally:
            if cursor:
                cursor.close()

def test_connection() -> bool:
    """
    Kiểm tra kết nối database
    
    Returns:
        bool: True nếu kết nối thành công
    """
    with get_db_connection() as conn:
        if conn and conn.is_connected():
            st.success("Database đang hoạt động bình thường")
            return True
        else:
            st.error(" Không thể kết nối database")
            return False