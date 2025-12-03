# 1. Chọn hệ điều hành có sẵn Python 3.9
FROM python:3.9-slim

# 2. Tạo thư mục làm việc bên trong Docker
WORKDIR /app

# 3. Copy file thư viện vào trước (để tận dụng cache của Docker)
COPY requirements.txt .

# 4. Cài đặt các thư viện
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy toàn bộ code dự án vào trong Docker
COPY . .

# 6. Mở cổng 8501 (Cổng mặc định của Streamlit)
EXPOSE 8501

# 7. Lệnh chạy ứng dụng khi khởi động
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]