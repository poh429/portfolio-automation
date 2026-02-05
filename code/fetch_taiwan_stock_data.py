#!/usr/bin/env python3
"""
台股財報數據抓取腳本
使用台灣證交所公開資訊觀測站 API
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class TWStockDataFetcher:
    """台股數據抓取器"""
    
    def __init__(self):
        self.base_url = "https://mops.twse.com.tw/mops/web/ajax_t163sb04"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch_financial_statement(self, stock_code: str, year: int, season: int) -> Optional[Dict]:
        """
        抓取單一股票的季度財報
        
        Args:
            stock_code: 股票代碼 (e.g., "2330")
            year: 民國年 (e.g., 113 for 2024)
            season: 季度 (1-4)
        
        Returns:
            財報數據字典，失敗回傳 None
        """
        params = {
            'encodeURIComponent': 1,
            'step': 1,
            'firstin': 1,
            'off': 1,
            'co_id': stock_code,
            'year': year,
            'season': season
        }
        
        try:
            response = requests.post(self.base_url, data=params, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # 簡化：返回原始 HTML，後續需解析
            return {
                'stock_code': stock_code,
                'year': year,
                'season': season,
                'timestamp': datetime.now().isoformat(),
                'raw_html': response.text[:500]  # 只存前500字符示範
            }
        
        except Exception as e:
            print(f"❌ 抓取失敗 {stock_code} ({year}Q{season}): {e}")
            return None
    
    def fetch_portfolio_data(self, portfolio_path: str = 'data/config/portfolio_holdings.json') -> Dict:
        """
        批次抓取持倉所有台股的最新財報
        
        Args:
            portfolio_path: 持倉數據檔案路徑
        
        Returns:
            所有股票的財報數據
        """
        # 讀取持倉
        with open(portfolio_path, 'r', encoding='utf-8') as f:
            portfolio = json.load(f)
        
        results = {}
        taiwan_stocks = portfolio.get('taiwan_stocks', {})
        
        # 計算當前民國年和季度
        now = datetime.now()
        tw_year = now.year - 1911
        current_season = (now.month - 1) // 3 + 1
        
        # 如果是季初，使用上一季
        if now.month % 3 == 1 and now.day < 15:
            current_season -= 1
            if current_season == 0:
                current_season = 4
                tw_year -= 1
        
        print(f"📅 抓取時間: {now.strftime('%Y-%m-%d %H:%M')}")
        print(f"📊 目標季度: {tw_year}年Q{current_season}")
        print("=" * 80)
        
        for stock_code, stock_info in taiwan_stocks.items():
            print(f"🔍 抓取 {stock_code} {stock_info['name']}...")
            data = self.fetch_financial_statement(stock_code, tw_year, current_season)
            
            if data:
                results[stock_code] = data
                print(f"  ✅ 成功")
            else:
                print(f"  ❌ 失敗")
            
            # 避免被封IP，延遲2秒
            time.sleep(2)
        
        return results


def main():
    """主函數"""
    fetcher = TWStockDataFetcher()
    
    # 抓取持倉數據
    results = fetcher.fetch_portfolio_data()
    
    # 儲存結果
    output_path = 'data/raw/tw_stock_financials.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 80)
    print(f"✅ 資料已儲存至 {output_path}")
    print(f"📊 共抓取 {len(results)} 檔案")


if __name__ == '__main__':
    main()
