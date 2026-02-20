# CLAUDE.md — SysMon 開發指南

本文件提供 Claude Code 在此專案工作時所需的完整情境。

---

## 專案概覽

**SysMon** 是一個網路/系統資訊查詢平台：
- **Web 版**（Streamlit）：部署至 Streamlit Cloud，跨裝置使用
- **CLI 版**（Typer + Rich）：本機執行，含系統規格查詢
- **UI 語言**：全繁體中文

---

## 環境設定

```bash
# 套件管理：uv（非 pip）
uv sync          # 安裝依賴
uv add <pkg>     # 新增依賴
uv run <cmd>     # 在虛擬環境中執行

# 啟動 Web
uv run streamlit run app.py

# 使用 CLI（Windows 需設 PYTHONIOENCODING）
PYTHONIOENCODING=utf-8 uv run sysmon --help
```

---

## 架構原則

### 分層設計
```
pages/*.py  ──→  sysmon/core/*.py  ←──  sysmon/cli.py
  (UI 層)          (業務邏輯層)          (CLI 層)
```

- **`sysmon/core/`**：純 Python 業務邏輯，**不可** import streamlit
- **`pages/`**：只負責 UI，從 core 取資料渲染
- **`sysmon/cli.py`**：在命令函數內才 import core（懶載入，加快 --help 速度）

### 雲端/本機偵測

`pages/9_💻_系統資訊.py` 檢查環境變數判斷是否為 Streamlit Cloud：

```python
IS_CLOUD = bool(
    os.environ.get("STREAMLIT_SHARING_MODE")
    or os.environ.get("IS_STREAMLIT_CLOUD")
    or os.environ.get("STREAMLIT_SERVER_HEADLESS")
)
```

---

## 關鍵檔案

| 檔案 | 說明 |
|------|------|
| `app.py` | Streamlit 主入口，定義導覽與側邊欄 API Key 輸入 |
| `sysmon/cli.py` | Typer CLI，10 個子命令 |
| `sysmon/core/ip_info.py` | ip-api.com（免費）+ ipinfo.io（Token）|
| `sysmon/core/dns_tools.py` | dnspython，支援 10 種記錄類型 |
| `sysmon/core/whois_tools.py` | python-whois（域名）+ ipwhois/RDAP（IP）|
| `sysmon/core/ssl_tools.py` | ssl + cryptography，解析憑證鏈 |
| `sysmon/core/web_tools.py` | httpx，追蹤重定向，解析 HTML title |
| `sysmon/core/port_scanner.py` | ThreadPoolExecutor，最多 1000 埠 |
| `sysmon/core/subnet_calc.py` | 標準函式庫 ipaddress，IPv4/IPv6 |
| `sysmon/core/system_info.py` | psutil，CPU/RAM/磁碟/網路介面 |
| `.streamlit/config.toml` | 深色主題，主色 `#00B4D8` |

---

## API Key 設計

API Key 採「**可選設計**」：

- 預設使用免費 API（ip-api.com 等），無需任何 Key
- 使用者在 Web 側邊欄輸入 Key 存入 `st.session_state`
- CLI 透過 `--token` 選項傳入

目前支援：
- `ipinfo_token` → `sysmon/core/ip_info.py` 的 `query_ip()`
- `abuseipdb_key`、`virustotal_key` → 側邊欄預留位置（功能待擴充）

---

## 常見問題與解法

### Windows CP950 Unicode 錯誤
```
UnicodeEncodeError: 'cp950' codec can't encode character '\U0001f5a5'
```
**解法**：`typer.Typer(help=...)` 的 app 層級 help 字串不可含 emoji。
各 `@app.command()` 的 docstring 裡的繁體中文沒問題。
CLI 執行時需設 `PYTHONIOENCODING=utf-8`。

### Streamlit `st.context.headers` 取 IP
在 Streamlit Cloud 上，真實 IP 在 `X-Forwarded-For` header，
備援方案是呼叫 `https://api.ipify.org`。

### `ssl_tools.py` 的 `not_valid_before_utc`
使用 `cryptography` >= 42.x 時，應用 `.not_valid_before_utc`（timezone-aware）
而非 `.not_valid_before`（deprecated）。

---

## 測試命令

```bash
# 功能測試
PYTHONIOENCODING=utf-8 uv run sysmon ip 8.8.8.8
PYTHONIOENCODING=utf-8 uv run sysmon dns google.com --type MX
PYTHONIOENCODING=utf-8 uv run sysmon ssl github.com
PYTHONIOENCODING=utf-8 uv run sysmon subnet 192.168.1.0/24
PYTHONIOENCODING=utf-8 uv run sysmon system
PYTHONIOENCODING=utf-8 uv run sysmon network

# Web 測試
uv run streamlit run app.py
```

---

## Streamlit Cloud 部署檢查清單

- [ ] `requirements.txt` 與 `pyproject.toml` 依賴同步
- [ ] `.streamlit/config.toml` 存在（主題設定）
- [ ] `.python-version` 為 `3.12`
- [ ] 主檔案：`app.py`
- [ ] `pages/` 目錄與 `app.py` 同層

---

## 新增功能指引

### 新增 core 模組
1. 在 `sysmon/core/` 新增 `xxx_tools.py`
2. 在 `pages/` 新增對應 Streamlit 頁面
3. 在 `sysmon/cli.py` 新增 `@app.command()`
4. 更新 `app.py` 的 `pages` 列表

### 新增 API Key
1. 在 `app.py` 側邊欄新增 `st.text_input(key="new_key")`
2. 在對應頁面從 `st.session_state.get("new_key", "")` 取值
3. 傳入 core 函數作為選填參數

---

## 依賴版本（已安裝）

見 `uv.lock`。主要版本：
- streamlit 1.54.0
- typer 0.24.0
- rich 14.3.3
- dnspython 2.8.0
- cryptography 46.0.5
- httpx 0.28.1
- psutil 7.2.2
- plotly 6.5.2
