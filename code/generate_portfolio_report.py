#!/usr/bin/env python3
"""
持倉分析報告生成器
整合三層分析結果並推送到 Google Sheets
"""

import json
import os
from datetime import datetime
from typing import Dict, List

class PortfolioReportGenerator:
    """持倉分析報告生成器"""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def load_analysis_results(self) -> Dict:
        """載入所有分析結果"""
        results = {
            'portfolio': {},
            'tang_scores': {},
            'moat_ratings': {},
            'risk_levels': {}
        }
        
        # 載入持倉數據
        try:
            with open('data/config/portfolio_holdings.json', 'r', encoding='utf-8') as f:
                results['portfolio'] = json.load(f)
        except FileNotFoundError:
            print("❌ 找不到持倉數據")
            return results
        
        # 載入分析結果
        analysis_files = {
            'tang_scores': 'data/analysis/tang_scores.json',
            'moat_ratings': 'data/analysis/moat_ratings.json',
            'risk_levels': 'data/analysis/risk_levels.json'
        }
        
        for key, filepath in analysis_files.items():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    results[key] = json.load(f)
            except FileNotFoundError:
                print(f"⚠️  找不到 {filepath}，跳過")
        
        return results
    
    def generate_markdown_report(self, results: Dict) -> str:
        """生成 Markdown 格式報告"""
        report = f"""# 📊 持倉健康檢查報告

**分析時間**: {self.timestamp}

---

## 一、持倉概況

"""
        # 台股部分
        taiwan_stocks = results['portfolio'].get('taiwan_stocks', {})
        if taiwan_stocks:
            report += "### 🇹🇼 台股持倉\n\n"
            report += "| 股票代碼 | 名稱 | 成本價 | 持股數 | 唐石峻評分 | 護城河等級 | 風險等級 | 建議 |\n"
            report += "|---------|------|--------|--------|-----------|----------|---------|------|\n"
            
            for ticker, info in taiwan_stocks.items():
                name = info.get('name', '-')
                cost = info.get('cost_price', '-')
                shares = info.get('shares', '-')
                
                # 取得分析結果
                tang_score = results['tang_scores'].get(ticker, {}).get('total_score', '-')
                moat = results['moat_ratings'].get(ticker, {}).get('rating', '-')
                risk = results['risk_levels'].get(ticker, {}).get('level', '-')
                
                # 決定建議
                recommendation = self._get_recommendation(tang_score, moat, risk)
                
                report += f"| {ticker} | {name} | {cost} | {shares} | {tang_score} | {moat} | {risk} | {recommendation} |\n"
        
        # 美股部分
        us_stocks = results['portfolio'].get('us_stocks', {})
        if us_stocks:
            report += "\n### 🇺🇸 美股持倉\n\n"
            report += "| 股票代碼 | 名稱 | 成本價 | 持股數 | 唐石峻評分 | 護城河等級 | 風險等級 | 建議 |\n"
            report += "|---------|------|--------|--------|-----------|----------|---------|------|\n"
            
            for ticker, info in us_stocks.items():
                name = info.get('name', '-')
                cost = info.get('cost_price', '-')
                shares = info.get('shares', '-')
                
                tang_score = results['tang_scores'].get(ticker, {}).get('total_score', '-')
                moat = results['moat_ratings'].get(ticker, {}).get('rating', '-')
                risk = results['risk_levels'].get(ticker, {}).get('level', '-')
                
                recommendation = self._get_recommendation(tang_score, moat, risk)
                
                report += f"| {ticker} | {name} | ${cost} | {shares} | {tang_score} | {moat} | {risk} | {recommendation} |\n"
        
        # 風險提醒
        report += "\n---\n\n## 二、重點關注事項\n\n"
        high_risk_stocks = [
            (ticker, data) for ticker, data in results['risk_levels'].items()
            if data.get('level') in ['高風險', 'High Risk']
        ]
        
        if high_risk_stocks:
            report += "### ⚠️ 高風險標的\n\n"
            for ticker, data in high_risk_stocks:
                reason = data.get('reason', '未知原因')
                report += f"- **{ticker}**: {reason}\n"
        else:
            report += "✅ 目前無高風險標的\n"
        
        # 底部說明
        report += f"""

---

## 三、評分說明

### 唐石峻16指標評分
- **80分以上**: 優質標的，可考慮加碼
- **60-80分**: 健康持有
- **60分以下**: 需密切觀察

### 護城河等級
- **寬護城河**: 長期競爭優勢明顯
- **窄護城河**: 有一定競爭優勢
- **無護城河**: 競爭優勢不明顯

### 風險等級
- **低風險**: 財務穩健，供應鏈分散
- **中風險**: 有部分風險因素需注意
- **高風險**: 存在重大風險，建議減碼

---

*本報告由 Nebula AI 波克夏投資分析師自動生成*  
*數據來源: 台灣證交所、Yahoo Finance*
"""
        
        return report
    
    def _get_recommendation(self, tang_score, moat, risk) -> str:
        """根據三層分析給出建議"""
        # 簡化邏輯
        if risk in ['高風險', 'High Risk']:
            return "🔴 減碼"
        
        if isinstance(tang_score, (int, float)):
            if tang_score >= 80:
                if moat in ['寬護城河', 'Wide Moat']:
                    return "🟢 加碼"
                else:
                    return "🟡 持有"
            elif tang_score >= 60:
                return "🟡 持有"
            else:
                return "🟠 觀察"
        
        return "⚪ 待評估"
    
    def save_report(self, report: str, filename: str = 'portfolio_health_report.md'):
        """儲存報告"""
        output_path = f'docs/{filename}'
        os.makedirs('docs', exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ 報告已儲存至 {output_path}")
        return output_path
    
    def prepare_sheets_data(self, results: Dict) -> List[List]:
        """準備要推送到 Google Sheets 的數據"""
        rows = [['更新時間', self.timestamp, '', '', '', '', '', '']]
        rows.append(['股票代碼', '名稱', '成本價', '持股數', '唐石峻評分', '護城河', '風險等級', '建議'])
        
        # 台股
        for ticker, info in results['portfolio'].get('taiwan_stocks', {}).items():
            tang_score = results['tang_scores'].get(ticker, {}).get('total_score', '-')
            moat = results['moat_ratings'].get(ticker, {}).get('rating', '-')
            risk = results['risk_levels'].get(ticker, {}).get('level', '-')
            recommendation = self._get_recommendation(tang_score, moat, risk)
            
            rows.append([
                ticker,
                info.get('name', '-'),
                info.get('cost_price', '-'),
                info.get('shares', '-'),
                tang_score,
                moat,
                risk,
                recommendation
            ])
        
        # 美股
        for ticker, info in results['portfolio'].get('us_stocks', {}).items():
            tang_score = results['tang_scores'].get(ticker, {}).get('total_score', '-')
            moat = results['moat_ratings'].get(ticker, {}).get('rating', '-')
            risk = results['risk_levels'].get(ticker, {}).get('level', '-')
            recommendation = self._get_recommendation(tang_score, moat, risk)
            
            rows.append([
                ticker,
                info.get('name', '-'),
                f"${info.get('cost_price', '-')}",
                info.get('shares', '-'),
                tang_score,
                moat,
                risk,
                recommendation
            ])
        
        return rows


def main():
    """主函數"""
    print("=" * 80)
    print("📊 生成持倉健康檢查報告")
    print("=" * 80)
    
    generator = PortfolioReportGenerator()
    
    # 1. 載入分析結果
    print("\n📂 載入分析結果...")
    results = generator.load_analysis_results()
    
    # 2. 生成 Markdown 報告
    print("📝 生成 Markdown 報告...")
    report = generator.generate_markdown_report(results)
    report_path = generator.save_report(report)
    
    # 3. 準備 Google Sheets 數據
    print("📊 準備 Google Sheets 數據...")
    sheets_data = generator.prepare_sheets_data(results)
    
    # 建立 tmp 目錄並儲存 JSON 供後續使用
    os.makedirs('tmp', exist_ok=True)
    with open('tmp/sheets_update_data.json', 'w', encoding='utf-8') as f:
        json.dump({'rows': sheets_data}, f, ensure_ascii=False, indent=2)
    
    print("\n✅ 報告生成完成")
    print(f"   - Markdown 報告: {report_path}")
    print(f"   - Google Sheets 數據: tmp/sheets_update_data.json")
    
    return {
        'report_path': report_path,
        'sheets_data': sheets_data
    }


if __name__ == '__main__':
    main()
