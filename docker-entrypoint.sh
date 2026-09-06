#!/bin/bash
set -e

# 若存在語系編譯腳本，編譯多國語系翻譯檔
if [ -f compile_translations.py ]; then
    echo ">>> [Docker Entrypoint] 正在編譯多國語系翻譯檔..."
    python compile_translations.py || true
fi

echo ">>> [Docker Entrypoint] 正在檢查並套用資料庫遷移..."
python manage.py migrate --noinput

echo ">>> [Docker Entrypoint] 啟動應用程式..."
exec "$@"
