def transform(data, context):
    """
    唐石峻16指標自動計算器
    
    輸入格式 (data):
    {
        "ticker": "股票代碼",
        "years": 3,  # 分析年數（預設3年）
        "subjective": {  # 主觀判斷（需人工評估）
            "moat": 12,  # 護城河 (0-15分)
            "geopolitical_risk": 5,  # 地緣風險 (0-5分)
            "predictability": 8,  # 可預測性 (0-10分)
            "pricing_power": 9  # 定價能力 (0-10分)
        }
    }
    
    輸出: 16項指標評分 + 總分 + 詳細財報數據
    """
    import yfinance as yf
    import pandas as pd
    import numpy as np
    from datetime import datetime
    
    ticker = data.get('ticker')
    years = data.get('years', 3)
    subjective = data.get('subjective', {})
    
    if not ticker:
        return {"error": "缺少必要參數: ticker"}
    
    # 下載財報數據
    stock = yf.Ticker(ticker)
    
    try:
        # 獲取財務數據
        income_stmt = stock.financials.T  # 損益表
        balance_sheet = stock.balance_sheet.T  # 資產負債表
        cash_flow = stock.cashflow.T  # 現金流量表
        
        # 確保數據足夠（至少要有數據）
        if income_stmt.empty or balance_sheet.empty or cash_flow.empty:
            return {"error": f"無法獲取 {ticker} 的完整財報數據"}
        
        # 取最近N年數據
        income_stmt = income_stmt.head(years)
        balance_sheet = balance_sheet.head(years)
        cash_flow = cash_flow.head(years)
        
    except Exception as e:
        return {"error": f"數據獲取失敗: {str(e)}"}
    
    
    # ============ 主觀判斷（40%）============
    scores = {}
    
    # 1. 護城河 (15%)
    scores['moat'] = subjective.get('moat', 0)
    
    # 2. 地緣風險 (5%)
    scores['geopolitical_risk'] = subjective.get('geopolitical_risk', 0)
    
    # 3. 可預測性 (10%)
    scores['predictability'] = subjective.get('predictability', 0)
    
    # 4. 定價能力 (10%)
    scores['pricing_power'] = subjective.get('pricing_power', 0)
    
    
    # ============ 客觀表現（60%）============
    
    def safe_get(df, key, default=0):
        """安全獲取財報數據"""
        try:
            val = df.get(key, pd.Series([default] * len(df)))
            return val.fillna(0)
        except:
            return pd.Series([default] * len(df))
    
    def calculate_cagr(values):
        """計算複合年增長率"""
        try:
            values = [v for v in values if v != 0 and not pd.isna(v)]
            if len(values) < 2:
                return 0
            start = values[-1]
            end = values[0]
            n = len(values) - 1
            if start <= 0:
                return 0
            cagr = (pow(end / start, 1/n) - 1) * 100
            return cagr
        except:
            return 0
    
    def score_linear(value, min_val, max_val, max_score=5):
        """線性評分函數"""
        if value >= max_val:
            return max_score
        elif value <= min_val:
            return 0
        else:
            return max_score * (value - min_val) / (max_val - min_val)
    
    
    # 5. 財務狀況 (5%) - (現金 + 1年FCF) / 總借款
    try:
        cash = safe_get(balance_sheet, 'Cash And Cash Equivalents').iloc[0]
        total_debt = safe_get(balance_sheet, 'Total Debt').iloc[0]
        fcf = safe_get(cash_flow, 'Free Cash Flow').iloc[0]
        
        if total_debt > 0:
            financial_strength_ratio = (cash + fcf) / total_debt
        else:
            financial_strength_ratio = 999  # 無負債視為極佳
        
        scores['financial_strength'] = score_linear(financial_strength_ratio, 0.3, 1.0, 5)
        raw_data_financial = {
            "cash": float(cash),
            "fcf": float(fcf),
            "total_debt": float(total_debt),
            "ratio": float(financial_strength_ratio)
        }
    except:
        scores['financial_strength'] = 0
        raw_data_financial = {"error": "數據不足"}
    
    
    # 6. 股權稀釋 (5%) - 流通股數CAGR
    try:
        shares = safe_get(income_stmt, 'Diluted Average Shares')
        share_cagr = calculate_cagr(shares.tolist())
        
        # CAGR < -3% 得滿分（回購），> 0% 得零分（增發）
        scores['share_dilution'] = score_linear(-share_cagr, 0, 3, 5)
        raw_data_shares = {
            "share_count_history": shares.tolist(),
            "cagr": float(share_cagr)
        }
    except:
        scores['share_dilution'] = 0
        raw_data_shares = {"error": "數據不足"}
    
    
    # 7. 資本支出 (5%) - Capex / OCF
    try:
        capex = safe_get(cash_flow, 'Capital Expenditure').abs()
        ocf = safe_get(cash_flow, 'Operating Cash Flow')
        capex_ratio = (capex.iloc[0] / ocf.iloc[0] * 100) if ocf.iloc[0] > 0 else 0
        
        # < 10% 得滿分（輕資產），> 60% 得零分
        scores['capex'] = score_linear(60 - capex_ratio, 0, 50, 5)
        raw_data_capex = {
            "capex": float(capex.iloc[0]),
            "ocf": float(ocf.iloc[0]),
            "ratio_pct": float(capex_ratio)
        }
    except:
        scores['capex'] = 0
        raw_data_capex = {"error": "數據不足"}
    
    
    # 8. 研發支出 (5%) - R&D / OCF
    try:
        rnd = safe_get(income_stmt, 'Research And Development')
        ocf_rnd = safe_get(cash_flow, 'Operating Cash Flow')
        rnd_ratio = (rnd.iloc[0] / ocf_rnd.iloc[0] * 100) if ocf_rnd.iloc[0] > 0 else 0
        
        # < 10% 得滿分，> 50% 得零分
        scores['rnd'] = score_linear(50 - rnd_ratio, 0, 40, 5)
        raw_data_rnd = {
            "rnd": float(rnd.iloc[0]),
            "ocf": float(ocf_rnd.iloc[0]),
            "ratio_pct": float(rnd_ratio)
        }
    except:
        scores['rnd'] = 0
        raw_data_rnd = {"error": "數據不足"}
    
    
    # 9. 股票薪酬 (5%) - SBC / OCF
    try:
        sbc = safe_get(cash_flow, 'Stock Based Compensation')
        ocf_sbc = safe_get(cash_flow, 'Operating Cash Flow')
        sbc_ratio = (sbc.iloc[0] / ocf_sbc.iloc[0] * 100) if ocf_sbc.iloc[0] > 0 else 0
        
        # < 5% 得滿分，> 25% 得零分
        scores['sbc'] = score_linear(25 - sbc_ratio, 0, 20, 5)
        raw_data_sbc = {
            "sbc": float(sbc.iloc[0]),
            "ocf": float(ocf_sbc.iloc[0]),
            "ratio_pct": float(sbc_ratio)
        }
    except:
        scores['sbc'] = 0
        raw_data_sbc = {"error": "數據不足"}
    
    
    # 10. 投資資本回報率 ROIC (5%)
    try:
        nopat = safe_get(income_stmt, 'Operating Income').iloc[0] * 0.79  # 假設稅率21%
        total_equity = safe_get(balance_sheet, 'Total Equity Gross Minority Interest').iloc[0]
        total_debt_roic = safe_get(balance_sheet, 'Total Debt').iloc[0]
        invested_capital = total_equity + total_debt_roic
        
        roic = (nopat / invested_capital * 100) if invested_capital > 0 else 0
        
        # > 50% 得滿分
        scores['roic'] = score_linear(roic, 0, 50, 5)
        raw_data_roic = {
            "nopat": float(nopat),
            "invested_capital": float(invested_capital),
            "roic_pct": float(roic)
        }
    except:
        scores['roic'] = 0
        raw_data_roic = {"error": "數據不足"}
    
    
    # 11. 自由現金流增長 (5%)
    try:
        fcf_series = safe_get(cash_flow, 'Free Cash Flow')
        fcf_cagr = calculate_cagr(fcf_series.tolist())
        
        # CAGR > 20% 得滿分，< 5% 得零分
        scores['fcf_growth'] = score_linear(fcf_cagr, 5, 20, 5)
        raw_data_fcf_growth = {
            "fcf_history": fcf_series.tolist(),
            "cagr": float(fcf_cagr)
        }
    except:
        scores['fcf_growth'] = 0
        raw_data_fcf_growth = {"error": "數據不足"}
    
    
    # 12. 現金流品質 (5%) - OCF / Net Income
    try:
        ocf_quality = safe_get(cash_flow, 'Operating Cash Flow').iloc[0]
        net_income = safe_get(income_stmt, 'Net Income').iloc[0]
        
        quality_ratio = (ocf_quality / net_income) if net_income > 0 else 0
        
        # > 1 得滿分，< 0.2 得零分
        scores['cash_quality'] = score_linear(quality_ratio, 0.2, 1.0, 5)
        raw_data_quality = {
            "ocf": float(ocf_quality),
            "net_income": float(net_income),
            "ratio": float(quality_ratio)
        }
    except:
        scores['cash_quality'] = 0
        raw_data_quality = {"error": "數據不足"}
    
    
    # 13. 營收增長 (5%)
    try:
        revenue = safe_get(income_stmt, 'Total Revenue')
        revenue_cagr = calculate_cagr(revenue.tolist())
        
        # CAGR > 20% 得滿分，< 0% 得零分
        scores['revenue_growth'] = score_linear(revenue_cagr, 0, 20, 5)
        raw_data_revenue = {
            "revenue_history": revenue.tolist(),
            "cagr": float(revenue_cagr)
        }
    except:
        scores['revenue_growth'] = 0
        raw_data_revenue = {"error": "數據不足"}
    
    
    # 14. 經營利潤增長 (5%)
    try:
        op_income = safe_get(income_stmt, 'Operating Income')
        op_income_cagr = calculate_cagr(op_income.tolist())
        
        # CAGR > 20% 得滿分，< 0% 得零分
        scores['op_income_growth'] = score_linear(op_income_cagr, 0, 20, 5)
        raw_data_op_growth = {
            "op_income_history": op_income.tolist(),
            "cagr": float(op_income_cagr)
        }
    except:
        scores['op_income_growth'] = 0
        raw_data_op_growth = {"error": "數據不足"}
    
    
    # 15. 經營利潤率 (5%)
    try:
        op_margin = (safe_get(income_stmt, 'Operating Income').iloc[0] / 
                     safe_get(income_stmt, 'Total Revenue').iloc[0] * 100)
        
        # > 40% 得滿分
        scores['op_margin'] = score_linear(op_margin, 0, 40, 5)
        raw_data_margin = {"op_margin_pct": float(op_margin)}
    except:
        scores['op_margin'] = 0
        raw_data_margin = {"error": "數據不足"}
    
    
    # 16. 經營利潤率擴張 (5%)
    try:
        revenue_series = safe_get(income_stmt, 'Total Revenue')
        op_income_series = safe_get(income_stmt, 'Operating Income')
        margins = (op_income_series / revenue_series * 100).tolist()
        
        margin_cagr = calculate_cagr(margins)
        
        # CAGR > 2% 得滿分，< -4% 得零分
        scores['margin_expansion'] = score_linear(margin_cagr, -4, 2, 5)
        raw_data_expansion = {
            "margin_history": margins,
            "cagr": float(margin_cagr)
        }
    except:
        scores['margin_expansion'] = 0
        raw_data_expansion = {"error": "數據不足"}
    
    
    # ============ 計算總分 ============
    total_score = sum(scores.values())
    
    # 評級
    if total_score >= 80:
        rating = "極優 - 頂級複利機器"
    elif total_score >= 70:
        rating = "優秀 - 值得長期持有"
    elif total_score >= 60:
        rating = "良好 - 需進一步評估"
    else:
        rating = "不合格 - 不建議投資"
    
    
    return {
        "ticker": ticker,
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "total_score": round(total_score, 2),
        "rating": rating,
        "scores": {
            "主觀判斷 (40%)": {
                "1_護城河": scores['moat'],
                "2_地緣風險": scores['geopolitical_risk'],
                "3_可預測性": scores['predictability'],
                "4_定價能力": scores['pricing_power'],
                "小計": sum([scores['moat'], scores['geopolitical_risk'], 
                           scores['predictability'], scores['pricing_power']])
            },
            "客觀表現 (60%)": {
                "5_財務狀況": round(scores['financial_strength'], 2),
                "6_股權稀釋": round(scores['share_dilution'], 2),
                "7_資本支出": round(scores['capex'], 2),
                "8_研發支出": round(scores['rnd'], 2),
                "9_股票薪酬": round(scores['sbc'], 2),
                "10_ROIC": round(scores['roic'], 2),
                "11_FCF增長": round(scores['fcf_growth'], 2),
                "12_現金流品質": round(scores['cash_quality'], 2),
                "13_營收增長": round(scores['revenue_growth'], 2),
                "14_經營利潤增長": round(scores['op_income_growth'], 2),
                "15_經營利潤率": round(scores['op_margin'], 2),
                "16_利潤率擴張": round(scores['margin_expansion'], 2),
                "小計": round(sum([scores[k] for k in scores if k not in 
                                 ['moat', 'geopolitical_risk', 'predictability', 'pricing_power']]), 2)
            }
        },
        "raw_financial_data": {
            "financial_strength": raw_data_financial,
            "share_dilution": raw_data_shares,
            "capex": raw_data_capex,
            "rnd": raw_data_rnd,
            "sbc": raw_data_sbc,
            "roic": raw_data_roic,
            "fcf_growth": raw_data_fcf_growth,
            "cash_quality": raw_data_quality,
            "revenue_growth": raw_data_revenue,
            "op_income_growth": raw_data_op_growth,
            "op_margin": raw_data_margin,
            "margin_expansion": raw_data_expansion
        }
    }
