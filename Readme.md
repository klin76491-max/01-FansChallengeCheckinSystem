# 🔥 FansChallengeCheckinSystem (粉絲挑戰打卡系統)

這是一個基於 Django 5.x 開發的現代化社群互動打卡應用程式（遵循 **A Little Wonder** 設計標準）。透過**每日/每週挑戰**、**AJAX 無刷新即時打卡**、**連續天數 (Streak) 紅利加分**、**即時排行榜**與**成就社群分享**，幫助學習者與粉絲養成持續練習與堅持的好習慣。

---

## ✨ 核心功能特色

- **🔥 挑戰任務管理**：支援每日挑戰 (Daily) 與每週挑戰 (Weekly)，可精確設定活動起訖時間與自訂基礎/連擊給分規則。
- **⚡ AJAX 無刷新即時打卡**：流暢的非同步互動體驗，提供動態數字跳動、微動畫回饋與即時分數結算，無需整頁重整。
- **🎯 連擊機制與紅利加分 (Streak System)**：自動偵測跨日連續打卡狀態，連續天數累加並加贈連擊紅利，若斷更則自動重置為 1。
- **🛡️ 嚴密防呆與交易安全**：以伺服器時區 (`Asia/Taipei`) 為基準防止跨區竄改時間，結合資料庫唯一約束與 `transaction.atomic` 確保高併發下數據絕對一致。
- **🏆 即時榮譽排行榜 (Leaderboard)**：依總積分、連續天數與報名順序即時排序，前三名金銀銅標章視覺呈現，並醒目標註個人當前名次。
- **📤 一鍵成就分享 (Web Share API)**：優先調用行動裝置原生 Web Share API 分享，並具備自動降級複製文案至剪貼簿機制，降低擴散門檻。
- **🎨 A Little Wonder 品牌視覺設計**：採用深海藍 (`#1a3a52`)、青松藍綠 (`#2d7a8a`) 與燕麥暖白 (`#f5f0e8`) 現代色彩系統，提供全響應式行動優先 (Mobile-First) 體驗。
- **🔐 Google OAuth 2.0 唯一快速註冊與登入**：全站統一支援 **Google 帳號一鍵授權登入 / 自動註冊**，無需手動填寫帳號密碼，安全快速且杜絕密碼外洩風險。



---

## 🚀 快速開始

### 1. 建立與啟動虛擬環境 (Virtual Environment)

本專案建議使用 `venv` 建立獨立虛擬環境。

```powershell
# 建立 Python 虛擬環境
python -m venv .venv
```

[!TIP]
**Windows PowerShell 執行原則提示**：  
若執行 `Activate.ps1` 出現 `UnauthorizedAccess` / `running scripts is disabled` 錯誤，有以下兩種解決方式：
1. **推薦方式（直接呼叫虛擬環境內的 Python，不需啟動）：**
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe manage.py migrate
   .\.venv\Scripts\python.exe manage.py runserver
   ```
2. **傳統方式（暫時放寬當前視窗的執行原則後啟動）：**
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   # macOS/Linux 請使用: source .venv/bin/activate
   ```

---

### 2. 安裝依賴套件

```powershell
# 若已啟動虛擬環境：
pip install -r requirements.txt

# 若未啟動虛擬環境（直接調用）：
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. 初始化資料庫

執行以下指令建立資料庫與資料表：
```powershell
# 若已啟動虛擬環境：
python manage.py makemigrations
python manage.py migrate

# 若未啟動虛擬環境：
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py migrate
```

### 4. 建立管理者帳號 (Superuser)

建立後台管理員以新增與管理挑戰活動：
```powershell
# 若已啟動虛擬環境：
python manage.py createsuperuser

# 若未啟動虛擬環境：
.\.venv\Scripts\python.exe manage.py createsuperuser
```
*(依序輸入使用者名稱、電子信箱與密碼)*

### 5. 執行自動化測試

本專案包含 46 個完整單元與整合測試案例（涵蓋 Models、Service 業務邏輯、Page CBV、AJAX API 與 Google OAuth 認證）：
```powershell
# 若已啟動虛擬環境：
python manage.py test challenges -v 2

# 若未啟動虛擬環境：
.\.venv\Scripts\python.exe manage.py test challenges -v 2
```

### 6. 設定 Google OAuth 2.0 (必要)

本專案採用 Google OAuth 2.0 作為唯一會員登入管道，請於 `.env` 中填入憑證（由 [Google Cloud Console](https://console.cloud.google.com/) 取得，完全免費、免綁信用卡）：
```env
GOOGLE_OAUTH_CLIENT_ID=xxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxx
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/accounts/google/callback/
```


### 7. 啟動應用程式

啟動本地端開發伺服器：
```powershell
# 若已啟動虛擬環境：
python manage.py runserver

# 若未啟動虛擬環境：
.\.venv\Scripts\python.exe manage.py runserver
```

伺服器啟動後，即可開啟瀏覽器訪問：
- 🌟 **前台挑戰首頁**：[http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- ⚙️ **管理員後台**：[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

### 8. 🐳 Docker 獨立微服務建置與部署 (獨立容器)

本專案支援獨立 Docker 容器化部署（嚴禁依賴 `docker-compose`，具備獨立生命週期與資料持久化）：

#### 8.1 建立與設定環境變數檔 (`.env`)
啟動容器前請確保目錄下已建立 `.env` 檔案並配置 Google OAuth 憑證：
```powershell
Copy-Item .env.example .env
```

#### 8.2 建置獨立 Docker 映像檔
```bash
docker build -t fwm-fans-challenge:latest .
```

#### 8.3 啟動微服務容器 (含 Volume 資料持久化與 Port 映射)
```bash
# 映射主機 8001 Port，並掛載 .env 與 SQLite 資料庫 Volume
docker run -d \
  --name fwm-app-01 \
  -p 8001:8000 \
  --env-file .env \
  -v fwm_challenge_data:/app \
  --restart unless-stopped \
  fwm-fans-challenge:latest
```
> [!NOTE]
> 容器啟動時，`docker-entrypoint.sh` 會自動執行 `python manage.py migrate --noinput` 資料庫遷移。
> 啟動後可開啟瀏覽器訪問：[http://localhost:8001/](http://localhost:8001/)

#### 8.4 查看即時日誌
```bash
docker logs -f fwm-app-01
```

#### 8.5 建立管理員帳號 (在容器內執行)
```bash
docker exec -it fwm-app-01 python manage.py createsuperuser
```

#### 8.6 執行容器內自動化測試
```bash
docker exec -it fwm-app-01 python manage.py test challenges -v 2
```

#### 8.7 停止、重啟與移除容器
```bash
# 停止容器
docker stop fwm-app-01

# 重新啟動容器
docker start fwm-app-01

# 刪除容器 (Volume 資料仍會妥善保留於 fwm_challenge_data)
docker rm -f fwm-app-01
```


---

## 📂 專案架構概覽

- `Dockerfile` — 獨立微服務 Docker 映像檔建置規格。
- `docker-entrypoint.sh` — 容器啟動進入點腳本（自動執行資料庫遷移）。
- `.dockerignore` — Docker 建置排除清單。
- `config/` — Django 專案核心設定、環境變數載入與根路由 (`urls.py`)。
- `challenges/` — 核心應用程式 (App)，遵循清晰的分層架構：
  - **`models.py`**: 資料模型（挑戰活動 `Challenge`、參與名冊 `Participant`、打卡明細 `CheckIn`）。
  - **`services.py`**: 核心業務邏輯層（`CheckInService` 打卡連擊計算、`GoogleAuthService` Google OAuth 認證同步）。
  - **`views.py` & `urls.py`**: 頁面視圖 (CBV) 與 AJAX 非同步 API 端點。
  - **`auth_views.py` & `auth_urls.py`**: 處理使用者註冊、密碼登入與 Google OAuth 登入/回傳處理。
  - **`forms.py`**: 自訂表單驗證（含 Email 唯一性檢查之 `CustomUserCreationForm`）。
  - **`admin.py`**: Django Admin 後台客製化介面。
  - **`tests/`**: 分層自動化測試模組（`test_models.py`、`test_services.py`、`test_views.py` 共 46 測試）。
- `templates/` — 前端 HTML 模板，採用語意化標籤與響應式排版（`base.html`、`challenges/`、`accounts/`）。
- `static/` — 前端靜態資源：
  - **`css/custom.css`**: A Little Wonder 品牌色彩系統與 Design Tokens。
  - **`js/checkin.js`**: AJAX 打卡/加入挑戰與數字跳動微動畫。
  - **`js/share.js`**: Web Share API 與剪貼簿降級分享處理。
- `db.sqlite3` — 本地開發 SQLite 資料庫。

---

*Keep Chasing & Keep Checking In! 堅持打卡，見證每一步的微小奇蹟！* 🎉


