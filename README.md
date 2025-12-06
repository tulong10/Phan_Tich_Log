# Log Analyzer
- Application for analyzing log files with Streamlit interface, MySQL database storage and PDF/PPTX report export.
Requirements

- Docker & Docker Compose
- Python 3.9+ (if running locally)

- Installation

## 2. Create .env file

- Create .env
```
DB_HOST=mysql
DB_USER=root
DB_PASSWORD="create your password"
DB_NAME=log_db
DB_PORT=3306
```
## 3. Run with Docker
- docker-compose up -d
- Application will run at: http://localhost:8501
## 4. Run locally (without Docker)
- pip install -r requirements.txt
- streamlit run app.py