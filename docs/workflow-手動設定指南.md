# GitHub Actions Workflow 手動設定指南

## ⚠️ 重要說明

由於 GitHub API 限制，無法透過 API 直接建立 `.github/workflows/` 目錄。
請按照以下步驟手動新增 workflow 檔案。

## 📋 步驟一：建立 Workflow 檔案

### 方法 1: 透過 GitHub 網頁介面（推薦）

1. 前往你的 repository: https://github.com/poh429/portfolio-automation
2. 點擊 **Actions** 頁籤
3. 如果是第一次使用，會看到 "Get started with GitHub Actions"
4. 點擊 **"set up a workflow yourself"** 或 **"New workflow"**
5. 將檔案命名為 `portfolio-health-check.yml`
6. 複製貼上以下完整內容：

```yaml
name: Portfolio Health Check

on:
  schedule:
    # 每日台北時間 14:00 (UTC 06:00) 執行
    - cron: '0 6 * * *'
  workflow_dispatch:  # 允許手動觸發

jobs:
  analyze-portfolio:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install yfinance pandas numpy requests beautifulsoup4 lxml
      
      - name: Create necessary directories
        run: |
          mkdir -p data/raw
          mkdir -p data/analysis
          mkdir -p docs
      
      - name: Fetch Taiwan stock data
        run: |
          python code/fetch_taiwan_stock_data.py
        continue-on-error: true
      
      - name: Run Tang 16 Metrics Analysis
        run: |
          python -c "
          import json
          import sys
          sys.path.insert(0, 'scripts/general')
          from tang_16_metrics import transform
          
          # 讀取持倉
          with open('data/config/portfolio_holdings.json', 'r', encoding='utf-8') as f:
              portfolio = json.load(f)
          
          all_scores = {}
          
          # 分析台股
          for ticker in portfolio.get('taiwan_stocks', {}).keys():
              tw_ticker = f'{ticker}.TW'
              print(f'分析 {tw_ticker}...')
              result = transform({'ticker': tw_ticker, 'years': 3}, {})
              if 'error' not in result:
                  all_scores[ticker] = result
          
          # 分析美股
          for ticker in portfolio.get('us_stocks', {}).keys():
              print(f'分析 {ticker}...')
              result = transform({'ticker': ticker, 'years': 3}, {})
              if 'error' not in result:
                  all_scores[ticker] = result
          
          # 儲存結果
          with open('data/analysis/tang_scores.json', 'w', encoding='utf-8') as f:
              json.dump(all_scores, f, ensure_ascii=False, indent=2)
          
          print(f'✅ 完成 {len(all_scores)} 支股票的唐石峻評分')
          "
        continue-on-error: true
      
      - name: Run Henry Supply Chain Risk Assessment
        run: |
          python -c "
          import json
          import sys
          sys.path.insert(0, 'scripts/general')
          from henry_supply_chain_risk import transform
          
          # 讀取持倉
          with open('data/config/portfolio_holdings.json', 'r', encoding='utf-8') as f:
              portfolio = json.load(f)
          
          all_risks = {}
          
          # 分析所有持股
          all_tickers = list(portfolio.get('taiwan_stocks', {}).keys()) + list(portfolio.get('us_stocks', {}).keys())
          
          for ticker in all_tickers:
              print(f'評估 {ticker} 風險...')
              result = transform({'ticker': ticker}, {})
              if 'error' not in result:
                  all_risks[ticker] = result
          
          # 儲存結果
          with open('data/analysis/risk_levels.json', 'w', encoding='utf-8') as f:
              json.dump(all_risks, f, ensure_ascii=False, indent=2)
          
          print(f'✅ 完成 {len(all_risks)} 支股票的風險評估')
          "
        continue-on-error: true
      
      - name: Generate Portfolio Report
        run: |
          python code/generate_portfolio_report.py
      
      - name: Update Google Sheets
        env:
          GOOGLE_SHEETS_CREDENTIALS: ${{ secrets.GOOGLE_SHEETS_CREDENTIALS }}
          SPREADSHEET_ID: ${{ secrets.SPREADSHEET_ID }}
        run: |
          python -c "
          import json
          import os
          from google.oauth2.service_account import Credentials
          from googleapiclient.discovery import build
          
          # 載入憑證
          creds_json = os.environ['GOOGLE_SHEETS_CREDENTIALS']
          creds_dict = json.loads(creds_json)
          creds = Credentials.from_service_account_info(creds_dict)
          
          service = build('sheets', 'v4', credentials=creds)
          
          # 讀取待更新數據
          with open('tmp/sheets_update_data.json', 'r', encoding='utf-8') as f:
              data = json.load(f)
          
          spreadsheet_id = os.environ['SPREADSHEET_ID']
          range_name = 'Analysis!A1'
          
          body = {'values': data['rows']}
          
          result = service.spreadsheets().values().update(
              spreadsheetId=spreadsheet_id,
              range=range_name,
              valueInputOption='RAW',
              body=body
          ).execute()
          
          print(f'✅ 已更新 {result.get(\"updatedCells\")} 個儲存格')
          "
        continue-on-error: true
      
      - name: Commit and push if changed
        run: |
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git config --global user.name "github-actions[bot]"
          git add -A
          git diff --quiet && git diff --staged --quiet || (git commit -m "🤖 自動更新持倉分析報告 $(date +'%Y-%m-%d %H:%M')" && git push)
      
      - name: Send Telegram notification (optional)
        if: always()
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
            STATUS="${{ job.status }}"
            MESSAGE="📊 持倉健康檢查執行完成%0A狀態: $STATUS%0A時間: $(date +'%Y-%m-%d %H:%M')"
            curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
              -d "chat_id=$TELEGRAM_CHAT_ID" \
              -d "text=$MESSAGE"
          fi
```

7. 點擊 **"Commit changes..."**
8. 確認 commit 訊息，點擊 **"Commit changes"**

### 方法 2: 透過 Git 指令

```bash
# Clone repository
git clone https://github.com/poh429/portfolio-automation.git
cd portfolio-automation

# 建立目錄
mkdir -p .github/workflows

# 建立 workflow 檔案
cat > .github/workflows/portfolio-health-check.yml << 'EOF'
# (貼上上方完整的 YAML 內容)
EOF

# Commit 並推送
git add .github/workflows/portfolio-health-check.yml
git commit -m "ci: 新增 GitHub Actions workflow"
git push
```

## 📋 步驟二：設定 GitHub Secrets

請參考主要的 [GitHub-Actions-部署指南.md](./GitHub-Actions-部署指南.md)

## ✅ 驗證

1. 前往 **Actions** 頁籤
2. 應該會看到 "Portfolio Health Check" workflow
3. 可以手動點擊 **"Run workflow"** 測試執行

---

**注意**: 這個檔案只是補充說明，主要部署指南請參考 `GitHub-Actions-部署指南.md`
