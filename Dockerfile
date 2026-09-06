FROM python:3.12-slim

# 設定環境變數
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data

# 設定工作目錄
WORKDIR /app

# 先複製依賴套件清單並安裝（利用 Docker 快取層優化建置速度）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案原始碼
COPY . .

# 賦予 entrypoint 腳本執行權限
RUN chmod +x docker-entrypoint.sh

# 暴露 Django 服務埠號
EXPOSE 8000

# 設定啟動進入點腳本
ENTRYPOINT ["./docker-entrypoint.sh"]

# 預設啟動指令
CMD ["python", "manage.py", "runserver", "--insecure", "0.0.0.0:8000"]
