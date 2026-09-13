#!/bin/bash
set -e

# 自動載入 .env 環境變數 (若存在)
if [ -f ".env" ]; then
    set -a
    . ./.env
    set +a
fi

# 若存在語系編譯腳本，編譯多國語系翻譯檔
if [ -f compile_translations.py ]; then
    echo ">>> [Docker Entrypoint] 正在編譯多國語系翻譯檔..."
    python compile_translations.py || true
fi

# 若配置 PostgreSQL，等待資料庫連線就緒
if [ -n "$DB_HOST" ] && [ "$USE_SQLITE" != "True" ] && [ "$USE_SQLITE" != "true" ]; then
    echo ">>> [Docker Entrypoint] 等待 PostgreSQL ($DB_HOST:${DB_PORT:-5432}) 連線就緒..."
    python - <<'EOF'
import os
import socket
import time
import sys

host = os.getenv('DB_HOST', 'host.docker.internal')
port = int(os.getenv('DB_PORT', 5432))
timeout = 30
start = time.time()

while time.time() - start < timeout:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f">>> [Docker Entrypoint] 資料庫埠號 {host}:{port} 已就緒！")
            sys.exit(0)
    except (socket.timeout, ConnectionRefusedError, OSError):
        time.sleep(1)

print(f">>> [Docker Entrypoint] 警告：等待資料庫逾時 ({host}:{port})，嘗試繼續執行遷移...")
EOF
fi

echo ">>> [Docker Entrypoint] 正在檢查並套用資料庫遷移..."
python manage.py migrate --noinput

# 自動建立 Django 超級管理員帳號 (若環境變數已設定)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo ">>> [Docker Entrypoint] 正在建立超級管理員 '$DJANGO_SUPERUSER_USERNAME'..."
    python manage.py createsuperuser --noinput || true
fi

echo ">>> [Docker Entrypoint] 啟動應用程式..."
exec "$@"
