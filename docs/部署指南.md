# 🚀 GitHub Actions 自動化部署指南

本指南將協助你部署完整的持倉健康檢查自動化系統。

---

## 📋 準備清單

### 必要檔案 (已建立)
- ✅ `data/config/portfolio_holdings.json` - 持倉數據
- ✅ `code/fetch_taiwan_stock_data.py` - 台股數據抓取
- ✅ `scripts/general/tang_16_metrics.py` - 唐石峻16指標
- ✅ `scripts/general/henry_supply_chain_risk.py` - Henry風險評估
- ✅ `code/generate_portfolio_report.py` - 報告生成器
- ✅ `code/portfolio-health-check.yml` - GitHub Actions workflow

---

## 🔧 部署步驟

### 步驟 1: 建立 GitHub Repository

1. 在 GitHub 建立新 repo (或使用現有 repo)
2. 上傳以下檔案結構：

```
your-repo/
├── .github/
│   └── workflows/
│       └── portfolio-health-check.yml  ← 從 code/portfolio-health-check.yml 複製
├── data/
│   └── config/
│       └── portfolio_holdings.json
├── scripts/
│   └── general/
│       ├── tang_16_metrics.py
│       └── henry_supply_chain_risk.py
└── code/
    ├── fetch_taiwan_stock_data.py
    └── generate_portfolio_report.py
```

### 步驟 2: 設定 Google Sheets API

#### 2.1 啟用 Google Sheets API
1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立新專案或選擇現有專案
3. 啟用 **Google Sheets API**
4. 前往「憑證」頁面

#### 2.2 建立 Service Account
1. 點選「建立憑證」→「服務帳戶」
2. 填寫服務帳戶名稱 (例如: `portfolio-analyzer`)
3. 授予「編輯者」角色
4. 建立完成後，點選該服務帳戶
5. 進入「金鑰」分頁
6. 點選「新增金鑰」→「JSON」
7. 下載 JSON 金鑰檔案 (⚠️ 請妥善保管)

#### 2.3 分享 Google Sheets 給 Service Account
1. 打開你的 Google Sheets: `1TlQOV4K0jrmiwXV_bm2keEkNl0o4mCNZUJdVwwtRXFs`
2. 點選右上角「共用」
3. 將剛才建立的服務帳戶電子郵件 (格式: `xxx@xxx.iam.gserviceaccount.com`) 加入
4. 授予「編輯者」權限

### 步驟 3: 設定 GitHub Secrets

前往你的 GitHub repo → Settings → Secrets and variables → Actions

新增以下 Secrets：

#### 必要 Secrets

**1. GOOGLE_SHEETS_CREDENTIALS**
- 將步驟 2.2 下載的 JSON 檔案內容完整複製貼上
- 格式範例：
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "portfolio-analyzer@your-project.iam.gserviceaccount.com",
  ...
}
```

**2. SPREADSHEET_ID**
- 值: `1TlQOV4K0jrmiwXV_bm2keEkNl0o4mCNZUJdVwwtRXFs`

#### 選用 Secrets (Telegram 通知)

**3. TELEGRAM_BOT_TOKEN** (選用)
- 從 [@BotFather](https://t.me/BotFather) 取得
- 格式: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

**4. TELEGRAM_CHAT_ID** (選用)
- 從 [@userinfobot](https://t.me/userinfobot) 取得
- 格式: `123456789`

---

## ✅ 步驟 4: 測試執行

### 手動觸發測試
1. 前往 GitHub repo → Actions
2. 選擇「Portfolio Health Check」workflow
3. 點選「Run workflow」
4. 觀察執行過程

### 預期結果
✅ 所有步驟顯示綠色勾勾  
✅ 在 repo 中看到新的 commit (自動更新報告)  
✅ Google Sheets 的 `Analysis` 工作表被更新  
✅ (選用) 收到 Telegram 通知

---

## 📅 自動排程

Workflow 已設定每日台北時間 14:00 (UTC 06:00) 自動執行。

若要修改排程，編輯 `.github/workflows/portfolio-health-check.yml` 中的 cron 表達式：

```yaml
schedule:
  - cron: '0 6 * * *'  # 每日 UTC 06:00 = 台北 14:00
```

Cron 格式說明：
```
分 時 日 月 星期
0  6  *  *  *     ← 每天 06:00 UTC
0  6  *  *  1-5   ← 週一到週五 06:00 UTC
0  6,14 * * *     ← 每天 06:00 和 14:00 UTC
```

---

## 🔍 疑難排解

### Q1: Workflow 執行失敗怎麼辦？
**A:** 點選失敗的步驟查看錯誤訊息。常見問題：
- Google Sheets API 憑證錯誤 → 檢查 Secret 格式
- 找不到檔案 → 確認檔案路徑正確
- yfinance 抓取失敗 → 可能是網路問題或股票代碼錯誤

### Q2: Google Sheets 沒有更新？
**A:** 檢查：
1. Service Account 是否已加入 Sheets 共用
2. `SPREADSHEET_ID` Secret 是否正確
3. Sheets 中是否有 `Analysis` 工作表 (如沒有請手動建立)

### Q3: 台股數據抓取失敗？
**A:** 台灣證交所 API 可能有限流或維護，這是正常的。Workflow 設定了 `continue-on-error: true`，不會因此中斷。

### Q4: 如何查看歷史報告？
**A:** 每次執行都會 commit 到 GitHub，可在 repo 的 commit history 查看。

---

## 🎯 下一步優化

- [ ] 新增財報公告日提醒
- [ ] 整合更多數據源 (TEJ, CMoney)
- [ ] 加入技術指標分析
- [ ] 建立 Web Dashboard (GitHub Pages)
- [ ] 新增 Email 通知

---

## 📞 支援

遇到問題？在 GitHub repo 開 Issue 或聯繫 support@nebula.gg

*本系統由 Nebula AI 波克夏投資分析師開發*
