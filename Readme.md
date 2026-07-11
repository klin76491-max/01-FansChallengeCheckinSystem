# 粉絲挑戰打卡系統 (Fans Challenge Check-in System)

這是一個基於 Django 5 建置的社群互動 MVP 系統，提供每日/每週挑戰、打卡紀錄、排行榜與成績分享功能。

## 🚀 系統需求

- Python 3.10+
- Django 5.x

## 🛠️ 本機開發與環境設定

本專案使用 `venv` 作為虛擬環境，並因為 Windows 執行原則限制，建議直接呼叫虛擬環境內的 `python.exe` 執行所有指令。

### 1. 安裝相依套件
如果您尚未安裝套件，請執行：
```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. 資料庫遷移 (Migration)
初次建置或有修改 Models 時，請執行以下指令更新資料庫 (SQLite)：
```powershell
.\venv\Scripts\python.exe manage.py makemigrations
.\venv\Scripts\python.exe manage.py migrate
```

## 👨‍💻 管理者與後台設定

為了能夠在後台建立挑戰任務，您需要先建立一組超級管理員 (Superuser) 帳號：abc/abc

### 1. 建立管理者帳號
```powershell
.\venv\Scripts\python.exe manage.py createsuperuser
```
*(依序輸入帳號、信箱與密碼即可)*

### 2. 啟動伺服器
```powershell
.\venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

### 3. 登入後台並建立挑戰
1. 伺服器啟動後，請開啟瀏覽器前往：[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
2. 使用剛剛建立的管理員帳號登入。
3. 在「**粉絲挑戰打卡系統**」區塊中找到「**挑戰列表**」，點擊「新增」。
4. 填寫挑戰的名稱、規則、時間區間與給分方式後儲存。

## 🌟 使用者前台介面

挑戰建立完成後，您可以前往前台首頁體驗：
👉 [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

- **一般使用者**：可點擊右上角註冊新帳號，加入您剛剛建立的挑戰並開始打卡！
- **功能包含**：AJAX 無刷新打卡、連擊 (Streak) 積分計算、即時排行榜預覽、以及 Web Share API 成績分享。