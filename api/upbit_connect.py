from flask import Blueprint, jsonify, request
import jwt
import requests
import uuid
from dotenv import load_dotenv
import os
import logging

# 환경 변수 로드
load_dotenv()


# Blueprint 생성
connect_bp = Blueprint('connect', __name__)

class UpbitTrader:
    def __init__(self):
        self.access_key = os.getenv('UPBIT_ACCESS_KEY')
        self.secret_key = os.getenv('UPBIT_SECRET_KEY')
        
    def get_chart_data(self, ticker, interval, count):
        try:
            # 기본 URL
            base_url = "https://api.upbit.com/v1/candles"
            
            # interval에 따른 URL 생성
            if 'minute' in interval:
                minutes = interval.replace('minute', '')
                url = f"{base_url}/minutes/{minutes}"
            elif interval in ['day', 'days']:
                url = f"{base_url}/days"
            elif interval in ['week', 'weeks']:
                url = f"{base_url}/weeks"
            elif interval in ['month', 'months']:
                url = f"{base_url}/months"
            else:
                # 잘못된 interval이 전달된 경우 기본값으로 1시간 설정
                url = f"{base_url}/minutes/60"

            params = {
                "market": ticker,
                "count": count
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Error: {response.status_code}, {response.text}")
                return None
            
        except Exception as e:
            print(f"Error getting chart data: {e}")
            return None

    def get_balance(self):
        logging.info("잔고 조회 함수 실행")
        try:
            payload = {
                'access_key': self.access_key,
                'nonce': str(uuid.uuid4()),
            }
            logging.info("access_key: ${self.access_key}")
            jwt_token = jwt.encode(payload, self.secret_key)
            headers = {'Authorization': f'Bearer {jwt_token}'}
            url = "https://api.upbit.com/v1/accounts"
            response = requests.get(url, headers=headers)
            return response.json()
        except Exception as e:
            print(f"Error getting balance: {e}")
            return None

    def get_profit_loss(self):
        # 수익/손실 계산 로직 구현
        try:
            balance = self.get_balance()
            if balance:
                # 간단한 수익/손실 계산 예시
                return {
                    'total_balance': sum(float(asset['balance']) * float(asset['avg_buy_price']) for asset in balance),
                    'assets': balance
                }
            return None
        except Exception as e:
            print(f"Error calculating profit/loss: {e}")
            return None

# UpbitTrader 인스턴스 생성
trader = UpbitTrader()

# interval 받기위해서 parameter로 수정
@connect_bp.route('/chart', methods=['GET'])
def get_chart():
    """차트 데이터 API"""
    ticker = request.args.get('ticker', 'KRW-BTC')
    interval = request.args.get('interval', 'minute60')
    count = int(request.args.get('count', '24'))
    
    data = trader.get_chart_data(ticker, interval, count)
    if data is not None:
        return jsonify({
            'success': True,
            'data': data
        })
    return jsonify({'success': False, 'error': '차트 데이터 조회 실패'})

@connect_bp.route('/balance', methods=['GET'])
def get_balance():
    """잔고 조회 API"""
    logging.info("잔고 조회 API 실행")
    data = trader.get_balance()
    if data is not None:
        return jsonify({
            'success': True,
            'data': data
        })
    return jsonify({'success': False, 'error': '잔고 조회 실패'})

@connect_bp.route('/profit-loss', methods=['GET'])
def get_profit_loss():
    """수익/손실 현황 API"""
    data = trader.get_profit_loss()
    if data is not None:
        return jsonify({
            'success': True,
            'data': data
        })
    return jsonify({'success': False, 'error': '수익/손실 조회 실패'})
