def transform(data, context):
    """
    Henry供應鏈風險評估器
    基於Henry「資本保全優於獲利預測」的慢思考原則
    
    輸入格式 (data):
    {
        "ticker": "股票代碼",
        "years": 3,  # 分析年數
        "major_customers": [  # 主要客戶（可選，若有年報資料）
            {"name": "客戶A", "revenue_pct": 35},
            {"name": "客戶B", "revenue_pct": 25}
        ],
        "major_suppliers": [  # 主要供應商（可選）
            {"name": "供應商X", "cost_pct": 40}
        ],
        "industry_cycle": "up/down/stable"  # 產業循環位置（可選）
    }
    
    輸出: 供應鏈風險評分 + 資本保全建議
    """
    import yfinance as yf
    import pandas as pd
    import numpy as np
    from datetime import datetime
    
    ticker = data.get('ticker')
    years = data.get('years', 3)
    major_customers = data.get('major_customers', [])
    major_suppliers = data.get('major_suppliers', [])
    industry_cycle = data.get('industry_cycle', 'unknown')
    
    if not ticker:
        return {"error": "缺少必要參數: ticker"}
    
    # 下載財報數據
    stock = yf.Ticker(ticker)
    
    try:
        income_stmt = stock.financials.T
        balance_sheet = stock.balance_sheet.T
        cash_flow = stock.cashflow.T
        
        if income_stmt.empty or balance_sheet.empty or cash_flow.empty:
            return {"error": f"無法獲取 {ticker} 的完整財報數據"}
        
        income_stmt = income_stmt.head(years)
        balance_sheet = balance_sheet.head(years)
        cash_flow = cash_flow.head(years)
        
    except Exception as e:
        return {"error": f"數據獲取失敗: {str(e)}"}
    
    
    def safe_get(df, key, default=0):
        """安全獲取財報數據"""
        try:
            val = df.get(key, pd.Series([default] * len(df)))
            return val.fillna(0)
        except:
            return pd.Series([default] * len(df))
    
    def calculate_volatility(series):
        """計算波動率（標準差/平均值）"""
        try:
            values = [v for v in series if v != 0 and not pd.isna(v)]
            if len(values) < 2:
                return 0
            return (np.std(values) / np.mean(values) * 100) if np.mean(values) != 0 else 0
        except:
            return 0
    
    
    risk_scores = {}
    risk_details = {}
    
    
    # ========== 1. 客戶集中度風險 (30%) ==========
    customer_risk_score = 0
    
    if major_customers:
        total_concentration = sum([c['revenue_pct'] for c in major_customers])
        top_customer_pct = max([c['revenue_pct'] for c in major_customers])
        
        # 評分邏輯（分數越高 = 風險越低）
        if total_concentration < 30:
            customer_risk_score = 30  # 低風險
            customer_risk_level = "低風險"
        elif total_concentration < 50:
            customer_risk_score = 20  # 中風險
            customer_risk_level = "中風險"
        else:
            customer_risk_score = 5  # 高風險
            customer_risk_level = "高風險 - 客戶過度集中"
        
        risk_details['customer_concentration'] = {
            "top_customers": major_customers,
            "total_concentration_pct": total_concentration,
            "top_customer_pct": top_customer_pct,
            "risk_level": customer_risk_level,
            "warning": "單一客戶 >20% 或前三大客戶 >50% 屬高風險" if total_concentration >= 50 else None
        }
    else:
        customer_risk_score = 15  # 無數據，給予中性分數
        risk_details['customer_concentration'] = {
            "warning": "缺少主要客戶資料，建議查閱年報"
        }
    
    risk_scores['customer_concentration'] = customer_risk_score
    
    
    # ========== 2. 供應商集中度風險 (20%) ==========
    supplier_risk_score = 0
    
    if major_suppliers:
        total_supplier_concentration = sum([s['cost_pct'] for s in major_suppliers])
        
        if total_supplier_concentration < 40:
            supplier_risk_score = 20
            supplier_risk_level = "低風險"
        elif total_supplier_concentration < 60:
            supplier_risk_score = 12
            supplier_risk_level = "中風險"
        else:
            supplier_risk_score = 5
            supplier_risk_level = "高風險 - 供應鏈脆弱"
        
        risk_details['supplier_concentration'] = {
            "major_suppliers": major_suppliers,
            "total_concentration_pct": total_supplier_concentration,
            "risk_level": supplier_risk_level
        }
    else:
        supplier_risk_score = 12
        risk_details['supplier_concentration'] = {
            "warning": "缺少供應商資料"
        }
    
    risk_scores['supplier_concentration'] = supplier_risk_score
    
    
    # ========== 3. 毛利率穩定性 (25%) ==========
    try:
        revenue = safe_get(income_stmt, 'Total Revenue')
        gross_profit = safe_get(income_stmt, 'Gross Profit')
        gross_margin_series = (gross_profit / revenue * 100)
        
        gross_margin_volatility = calculate_volatility(gross_margin_series)
        recent_margin = gross_margin_series.iloc[0]
        margin_trend = gross_margin_series.iloc[0] - gross_margin_series.iloc[-1]
        
        # 毛利率波動 < 5% 且趨勢向上 = 低風險
        if gross_margin_volatility < 5 and margin_trend >= 0:
            margin_risk_score = 25
            margin_risk_level = "低風險 - 毛利穩定"
        elif gross_margin_volatility < 10:
            margin_risk_score = 15
            margin_risk_level = "中風險"
        else:
            margin_risk_score = 5
            margin_risk_level = "高風險 - 議價力弱化"
        
        risk_details['gross_margin_stability'] = {
            "recent_margin_pct": float(recent_margin),
            "margin_history": gross_margin_series.tolist(),
            "volatility_pct": float(gross_margin_volatility),
            "trend": "上升" if margin_trend > 0 else "下降",
            "risk_level": margin_risk_level
        }
        
        risk_scores['gross_margin_stability'] = margin_risk_score
        
    except:
        risk_scores['gross_margin_stability'] = 10
        risk_details['gross_margin_stability'] = {"error": "數據不足"}
    
    
    # ========== 4. 營收波動性 (15%) ==========
    try:
        revenue_series = safe_get(income_stmt, 'Total Revenue')
        revenue_volatility = calculate_volatility(revenue_series)
        
        if revenue_volatility < 10:
            revenue_risk_score = 15
            revenue_risk_level = "低風險"
        elif revenue_volatility < 20:
            revenue_risk_score = 10
            revenue_risk_level = "中風險"
        else:
            revenue_risk_score = 3
            revenue_risk_level = "高風險 - 營收不穩定"
        
        risk_details['revenue_stability'] = {
            "revenue_history": revenue_series.tolist(),
            "volatility_pct": float(revenue_volatility),
            "risk_level": revenue_risk_level
        }
        
        risk_scores['revenue_stability'] = revenue_risk_score
        
    except:
        risk_scores['revenue_stability'] = 8
        risk_details['revenue_stability'] = {"error": "數據不足"}
    
    
    # ========== 5. 產業循環位置 (10%) ==========
    if industry_cycle == "up":
        cycle_risk_score = 10
        cycle_warning = None
    elif industry_cycle == "stable":
        cycle_risk_score = 8
        cycle_warning = None
    elif industry_cycle == "down":
        cycle_risk_score = 3
        cycle_warning = "⚠️ 產業下行週期，建議減倉或觀望"
    else:
        cycle_risk_score = 5
        cycle_warning = "未提供產業循環資訊"
    
    risk_scores['industry_cycle'] = cycle_risk_score
    risk_details['industry_cycle'] = {
        "position": industry_cycle,
        "warning": cycle_warning
    }
    
    
    # ========== 計算總風險分數 ==========
    total_risk_score = sum(risk_scores.values())
    max_score = 100
    
    # 風險等級判定（Henry資本保全原則）
    if total_risk_score >= 75:
        risk_rating = "低風險 - 可長期持有"
        capital_preservation_advice = "供應鏈結構健康，基本面穩定，適合作為核心持倉"
    elif total_risk_score >= 60:
        risk_rating = "中風險 - 需設停損"
        capital_preservation_advice = "存在一定風險，建議設定停損點（-10%~-15%），財報前減倉20%"
    elif total_risk_score >= 40:
        risk_rating = "中高風險 - 謹慎持有"
        capital_preservation_advice = "⚠️ 供應鏈或財務波動較大，建議財報前減倉50%，避免二元事件賭博"
    else:
        risk_rating = "高風險 - 不建議持有"
        capital_preservation_advice = "❌ 資本保全原則：客戶集中度過高或財務極不穩定，建議清倉或大幅減倉"
    
    
    # ========== Henry式風險檢查點 ==========
    henry_checklist = {
        "財報前檢查": {
            "是否處於高估值": "需人工判斷 PE/PS 是否 priced for perfection",
            "是否面臨二元事件": "若財報結果不確定性高（如產業下行），優先獲利了結",
            "關聯資產信號": "檢查供應鏈上下游公司財報表現，是否有預警信號"
        },
        "供應鏈紅旗": []
    }
    
    # 自動標記紅旗
    if risk_details.get('customer_concentration', {}).get('total_concentration_pct', 0) > 50:
        henry_checklist['供應鏈紅旗'].append("🚩 客戶過度集中 - 單一客戶流失風險")
    
    if risk_details.get('gross_margin_stability', {}).get('trend') == "下降":
        henry_checklist['供應鏈紅旗'].append("🚩 毛利率下滑 - 可能失去議價能力")
    
    if industry_cycle == "down":
        henry_checklist['供應鏈紅旗'].append("🚩 產業下行週期 - 避免逆勢加碼")
    
    if not henry_checklist['供應鏈紅旗']:
        henry_checklist['供應鏈紅旗'].append("✅ 無明顯紅旗")
    
    
    return {
        "ticker": ticker,
        "analysis_date": datetime.now().strftime("%Y-%m-%d"),
        "total_risk_score": round(total_risk_score, 2),
        "max_score": max_score,
        "risk_rating": risk_rating,
        "capital_preservation_advice": capital_preservation_advice,
        "risk_breakdown": {
            "客戶集中度風險 (30%)": risk_scores['customer_concentration'],
            "供應商集中度風險 (20%)": risk_scores['supplier_concentration'],
            "毛利率穩定性 (25%)": risk_scores['gross_margin_stability'],
            "營收波動性 (15%)": risk_scores['revenue_stability'],
            "產業循環位置 (10%)": risk_scores['industry_cycle']
        },
        "detailed_analysis": risk_details,
        "henry_checklist": henry_checklist
    }
