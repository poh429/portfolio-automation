# 📈 波克夏演算法投資組合自動化系統

每日自動執行三層投資分析，整合唐石峻量化篩選、巴菲特護城河分析與 Henry 供應鏈風險評估。

## 🎯 功能特色

- **自動化分析**: 每日台北時間 14:00 自動執行
- **三層分析**:
  1. 唐石峻 16 指標量化篩選 (滿分 100)
  2. 巴菲特護城河與內在價值評估
  3. Henry 供應鏈風險與資本保全評估
- **多平台整合**: 自動更新 Google Sheets + GitHub 報告
- **即時通知**: 可選 Telegram 推播

## 📁 專案結構

```
.
├── .github/
│   └── workflows/
│       └── portfolio-health-check.yml    # GitHub Actions 自動執行
├── code/
│   ├── fetch_taiwan_stock_data.py        # 台股數據抓取
│   └── generate_portfolio_report.py      # 報告生成器
├── scripts/
│   └── general/
│       ├── tang_16_metrics.py            # 唐石峻 16 指標
│       └── henry_supply_chain_risk.py    # Henry 風險評估
├── data/
│   └── config/
│       └── portfolio_holdings.json       # 持倉數據 (需自行建立)
├── docs/
│   └── GitHub-Actions-部署指南.md
└── README.md
```

## 🚀 快速開始

### 1. Fork 此專案

### 2. 設定持倉數據

在 `data/config/` 建立 `portfolio_holdings.json`:

```json
{
  "taiwan_stocks": {
    "2330": {"name": "台積電", "shares": 10, "cost_price": 600},
    "2317": {"name": "鴻海", "shares": 50, "cost_price": 100}
  },
  "us_stocks": {
    "AAPL": {"name": "Apple", "shares": 5, "cost_price": 150},
    "MSFT": {"name": "Microsoft", "shares": 3, "cost_price": 350}
  }
}
```

### 3. 設定 GitHub Secrets

在 Repository Settings > Secrets and variables > Actions 新增:

#### 必要 (Google Sheets):
- `GOOGLE_SHEETS_CREDENTIALS`: Google Service Account JSON 憑證
- `GOOGLE_SHEET_ID`: 目標 Google Sheet ID

#### 可選 (Telegram):
- `TELEGRAM_BOT_TOKEN`: Telegram Bot Token
- `TELEGRAM_CHAT_ID`: 接收訊息的 Chat ID

### 4. 啟用 GitHub Actions

1. 前往 Repository > Actions 頁籤
2. 點擊 "I understand my workflows, go ahead and enable them"
3. 手動觸發測試: Actions > Portfolio Health Check > Run workflow

### 5. 驗證自動執行

- 預設每日台北時間 14:00 (UTC 06:00) 執行
- 檢查 Actions 頁籤查看執行紀錄
- 分析報告會自動 commit 到 `reports/` 資料夾

## 📊 輸出結果

### Google Sheets 更新
自動更新以下工作表:
- **持倉總覽**: 股票代碼、成本、現價、報酬率
- **Tang 評分**: 16 項量化指標詳細評分
- **風險評估**: Henry 資本保全分析

### GitHub 報告
每日自動 commit Markdown 報告到 `reports/YYYY-MM-DD.md`

### Telegram 通知 (可選)
即時推播關鍵警示:
- 🔴 Tang 評分 < 60 (不及格)
- 🟡 風險等級 = 高風險
- 🟢 新增買入機會

## 🔧 進階設定

### 修改執行時間

編輯 `.github/workflows/portfolio-health-check.yml`:

```yaml
on:
  schedule:
    # 每日 UTC 06:00 = 台北 14:00
    - cron: '0 6 * * *'
```

### 客製化分析參數

參考 `docs/GitHub-Actions-部署指南.md` 詳細說明。

## 📖 投資哲學

本系統整合三位投資大師的核心理念:

1. **唐石峻**: 量化指標篩選優質公司
2. **巴菲特**: 護城河與內在價值評估
3. **Henry**: 資本保全優先的風險管理

## ⚠️ 免責聲明

本系統僅供投資研究參考，不構成投資建議。投資有風險，請審慎評估。

## 📞 支援

- 詳細部署指南: [docs/GitHub-Actions-部署指南.md](docs/GitHub-Actions-部署指南.md)
- 技術支援: 開 Issue 討論

---

**Made with ❤️ by 波克夏演算法投資組合**
