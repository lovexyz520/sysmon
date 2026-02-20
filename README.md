# 🖥️ SysMon 系統查詢工具

> 網路與系統資訊查詢平台，支援 **CLI** 與 **Streamlit Web** 兩種操作方式。

- **Web 版**：部署至 Streamlit Cloud，支援 IP、DNS、WHOIS、SSL、HTTP、連接埠掃描、子網路計算
- **CLI 版**：本機執行，額外支援系統規格查詢（CPU、RAM、磁碟、網路介面）
- **UI 語言**：全繁體中文
- **API Key**：核心功能免費，可選填 API Key 解鎖進階功能

---

## 功能一覽

| 功能 | Web | CLI | 說明 |
|------|:---:|:---:|------|
| 🌐 IP 資訊 | ✅ | ✅ | IP 地理位置、ISP、ASN、代理偵測 |
| 🔍 DNS 查詢 | ✅ | ✅ | A/AAAA/MX/TXT/NS/CNAME/PTR/SOA/SRV/CAA |
| 📋 WHOIS | ✅ | ✅ | 域名與 IP WHOIS 查詢 |
| 🔒 SSL 憑證 | ✅ | ✅ | 憑證詳情、SAN、到期倒數 |
| 🔗 網站檢測 | ✅ | ✅ | HTTP 狀態碼、標頭、重定向鏈 |
| 🔌 連接埠掃描 | ✅ | ✅ | 多執行緒 TCP 掃描 |
| 🧮 子網路計算 | ✅ | ✅ | CIDR 子網路計算器 |
| 💻 系統資訊 | 本機 | ✅ | CPU/RAM/磁碟/網路介面 |

---

## 快速開始

### 環境需求

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) 套件管理器

### 安裝

```bash
# 克隆專案
git clone <repository-url>
cd sysmon

# 安裝依賴（uv 自動建立虛擬環境）
uv sync
```

### 啟動 Web 介面

```bash
uv run streamlit run app.py
# 或透過 CLI 啟動：
uv run sysmon serve
```

瀏覽器開啟 `http://localhost:8501`

### 使用 CLI

```bash
# Windows 建議加上編碼設定（避免中文亂碼）
# 可設定環境變數：set PYTHONIOENCODING=utf-8

uv run sysmon --help
```

---

## CLI 命令參考

### `ip` — IP 資訊查詢

```bash
# 自動偵測自己的公網 IP
uv run sysmon ip

# 查詢指定 IP
uv run sysmon ip 8.8.8.8

# 使用 ipinfo.io Token（更精確地理資訊）
uv run sysmon ip 8.8.8.8 --token YOUR_TOKEN
```

### `dns` — DNS 記錄查詢

```bash
# 查詢 A 記錄（預設）
uv run sysmon dns google.com

# 查詢指定類型
uv run sysmon dns google.com --type MX
uv run sysmon dns google.com --type TXT

# 使用指定 DNS 伺服器
uv run sysmon dns google.com --server 1.1.1.1
```

支援類型：`A` `AAAA` `MX` `TXT` `NS` `CNAME` `PTR` `SOA` `SRV` `CAA`

### `whois` — WHOIS 查詢

```bash
# 域名 WHOIS
uv run sysmon whois google.com

# IP WHOIS（使用 RDAP）
uv run sysmon whois 8.8.8.8
```

### `ssl` — SSL 憑證

```bash
# 查詢 HTTPS 憑證（port 443）
uv run sysmon ssl github.com

# 自訂連接埠
uv run sysmon ssl example.com --port 8443
```

### `web` — 網站 HTTP 檢測

```bash
uv run sysmon web https://google.com

# 自訂 User-Agent 與逾時
uv run sysmon web https://example.com --ua "curl/8.0" --timeout 30
```

### `scan` — 連接埠掃描

```bash
# 掃描常見連接埠（預設）
uv run sysmon scan 192.168.1.1

# 掃描 1-1024 全部連接埠
uv run sysmon scan 192.168.1.1 --preset all

# 指定連接埠（最多 1000 個）
uv run sysmon scan 192.168.1.1 --ports 80,443,3000,8080

# 調整逾時
uv run sysmon scan 192.168.1.1 --timeout 0.5
```

> ⚠️ 請僅對您有權限掃描的主機執行此操作。

### `subnet` — 子網路計算

```bash
uv run sysmon subnet 192.168.1.0/24
uv run sysmon subnet 10.0.0.0/8
uv run sysmon subnet 2001:db8::/32
```

### `system` — 系統資訊

```bash
# 顯示 OS、CPU、RAM、磁碟
uv run sysmon system

# 顯示網路介面
uv run sysmon network
```

### `serve` — 啟動 Web 介面

```bash
uv run sysmon serve

# 自訂連接埠
uv run sysmon serve --port 8888
```

---

## 專案結構

```
sysmon/
├── pyproject.toml              # UV 專案設定、依賴、CLI 入口
├── .python-version             # Python 3.12
├── requirements.txt            # Streamlit Cloud 部署用
├── app.py                      # Streamlit 主入口
├── .streamlit/
│   └── config.toml             # 深色主題（主色 #00B4D8）
├── pages/                      # Streamlit 多頁面
│   ├── 1_🏠_首頁.py
│   ├── 2_🌐_IP資訊.py
│   ├── 3_🔍_DNS查詢.py
│   ├── 4_📋_WHOIS.py
│   ├── 5_🔒_SSL憑證.py
│   ├── 6_🌐_網站檢測.py
│   ├── 7_🔌_連接埠掃描.py
│   ├── 8_🧮_子網路計算.py
│   └── 9_💻_系統資訊.py
└── sysmon/                     # Python 套件（業務邏輯）
    ├── cli.py                  # CLI 入口（Typer）
    └── core/
        ├── ip_info.py          # IP 地理/ISP 查詢
        ├── dns_tools.py        # DNS 解析（dnspython）
        ├── whois_tools.py      # WHOIS（python-whois + ipwhois）
        ├── ssl_tools.py        # SSL 憑證（cryptography）
        ├── web_tools.py        # HTTP 檢測（httpx）
        ├── port_scanner.py     # 連接埠掃描（多執行緒）
        ├── subnet_calc.py      # 子網路計算（標準函式庫）
        └── system_info.py      # 系統規格（psutil）
```

---

## 進階功能（API Key）

在 Web 版側邊欄或 CLI `--token` 選項輸入 API Key，解鎖進階功能：

| API | 功能 | 取得方式 |
|-----|------|----------|
| [ipinfo.io](https://ipinfo.io/signup) | 更精確 IP 地理資訊、隱私偵測 | 免費 50k 次/月 |
| [AbuseIPDB](https://www.abuseipdb.com/api) | IP 信譽/濫用報告 | 免費方案可用 |
| [VirusTotal](https://www.virustotal.com) | URL/IP 惡意軟體掃描 | 免費方案可用 |

---

## 部署至 Streamlit Cloud

1. 將專案推送至 GitHub
2. 前往 [share.streamlit.io](https://share.streamlit.io)
3. 連接 GitHub 儲存庫
4. 主檔案設定為 `app.py`
5. Python 版本選 `3.12`

系統資訊頁面（`9_💻_系統資訊.py`）在雲端環境會自動顯示提示，引導使用者改用 CLI 版本。

---

## 依賴套件

| 套件 | 用途 |
|------|------|
| `streamlit` | Web 介面框架 |
| `typer` + `rich` | CLI 框架與美化輸出 |
| `dnspython` | DNS 解析 |
| `python-whois` + `ipwhois` | WHOIS 查詢 |
| `cryptography` + `pyopenssl` | SSL 憑證解析 |
| `httpx` | HTTP 客戶端（支援重定向追蹤）|
| `psutil` | 系統資源監控 |
| `plotly` | 互動式圖表 |
| `requests` | IP API 呼叫 |

---

## Windows 中文顯示

若 CLI 輸出出現亂碼，請設定終端機編碼：

```powershell
# PowerShell 臨時設定
$env:PYTHONIOENCODING = "utf-8"

# 或在命令前加上
PYTHONIOENCODING=utf-8 uv run sysmon system
```

或永久設定系統環境變數 `PYTHONIOENCODING=utf-8`。

---

## License

MIT
