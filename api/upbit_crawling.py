from flask import Blueprint, jsonify
import numpy as np
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import requests
import ta

# Blueprint 생성
crawling_bp = Blueprint('crawling', __name__)

# 스케줄러 생성
scheduler = BackgroundScheduler(daemon=True)

def calculate_heikin_ashi(df):
    ha_close = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    ha_open = (df['open'].shift(1) + df['close'].shift(1)) / 2
    ha_high = df[['high', 'open', 'close']].max(axis=1)
    ha_low = df[['low', 'open', 'close']].min(axis=1)
    
    return pd.DataFrame({
        'open': ha_open,
        'high': ha_high,
        'low': ha_low,
        'close': ha_close
    })

def calculate_ema_200(df):
    return ta.trend.ema_indicator(df['close'], window=200)

def calculate_stoch_rsi(df, period=14, smooth_k=3, smooth_d=3):
    stoch_rsi = ta.momentum.stochrsi(df['close'], window=period)
    k = stoch_rsi.rolling(window=smooth_k).mean()
    d = k.rolling(window=smooth_d).mean()
    return k, d

def fetch_market_data(market="KRW-BTC"):
    url = f"https://api.upbit.com/v1/candles/minutes/10"
    params = {
        "market": market,
        "count": 200  # EMA 200 계산을 위해 충분한 데이터 필요
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df = df[['opening_price', 'high_price', 'low_price', 'trade_price']]
            df.columns = ['open', 'high', 'low', 'close']
            return df
        return None
    except Exception as e:
        print(f"데이터 가져오기 실패: {e}")
        return None

def update_market_data():
    df = fetch_market_data()
    if df is not None:
        # 기술적 지표 계산
        ha_df = calculate_heikin_ashi(df)
        ema_200 = calculate_ema_200(df)
        stoch_k, stoch_d = calculate_stoch_rsi(df)
        
        # 최신 데이터 저장
        global latest_data
        latest_data = {
            'timestamp': datetime.now().isoformat(),
            'heikin_ashi': {
                'open': float(ha_df['open'].iloc[-1]),
                'high': float(ha_df['high'].iloc[-1]),
                'low': float(ha_df['low'].iloc[-1]),
                'close': float(ha_df['close'].iloc[-1])
            },
            'ema_200': float(ema_200.iloc[-1]),
            'stoch_rsi': {
                'k': float(stoch_k.iloc[-1]),
                'd': float(stoch_d.iloc[-1])
            }
        }

# 전역 변수로 최신 데이터 저장
latest_data = None

# 스케줄러 시작
scheduler.add_job(update_market_data, 'interval', minutes=10)
scheduler.start()

@crawling_bp.route('/technical-indicators', methods=['GET'])
def get_technical_indicators():
    """기술적 지표 조회 API"""
    if latest_data is not None:
        return jsonify({
            'success': True,
            'data': latest_data
        })
    return jsonify({'success': False, 'error': '데이터 없음'})