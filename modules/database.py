import pandas as pd
import mysql.connector
import streamlit as st

# Cấu hình kết nối cơ sở dữ liệu MySQL.
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password':'python2025',
    'database': 'log_db',
    'port': 3307
}

@st.cache_resource
def connection_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print (f" Lỗi kết nối cơ sở dữ liệu:{err}")
        return None
    
def get_data_to_DataFame():
    conn = connection_db()
    if conn:
        query = "SELECT * FROM server_logs"
        df = pd.read_sql(query, conn)
        return df
    else:
        return pd.DataFrame() # Trả về DataFrame rỗng nếu không kết nối được

def save_log_data(list_data):
    conn = connection_db()
    if conn:
        cursor = conn.cursor() # Tạo con trỏ để thực thi câu lệnh SQL
        query = "INSERT INTO server_logs (ip_address, timestamp, status,log_level, response) VALUES (%s, %s, %s, %s, %s)"
        
        try:
            cursor.executemany(query, list_data) # Thực thi nhiều lệnh chèn dữ liệu
            conn.commit() # Lưu các thay đổi vào cơ sở dữ liệu
        except Exception as e:
            st.error(f"Lỗi khi lưu dữ liệu vào cơ sở dữ liệu: {e}")
        finally:
            cursor.close()
