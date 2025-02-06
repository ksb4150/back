from flask import Blueprint, request, jsonify
import jwt
import uuid
import hashlib
from urllib.parse import urlencode
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()

# Blueprint 생성
trading_bp = Blueprint('trading', __name__)

# 업비트 API 접근 키 설정
ACCESS_KEY = os.getenv('UPBIT_ACCESS_KEY')
SECRET_KEY = os.getenv('UPBIT_SECRET_KEY')
SERVER_URL = "https://api.upbit.com"

def create_jwt_token():
    payload = {
        'access_key': ACCESS_KEY,
        'nonce': str(uuid.uuid4()),
    }
    jwt_token = jwt.encode(payload, SECRET_KEY)
    return jwt_token

def get_headers(query=None):
    headers = {'Authorization': f'Bearer {create_jwt_token()}'}
    if query:
        query_string = urlencode(query).encode()
        m = hashlib.sha512()
        m.update(query_string)
        query_hash = m.hexdigest()
        payload = {
            'access_key': ACCESS_KEY,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
        }
        jwt_token = jwt.encode(payload, SECRET_KEY)
        headers['Authorization'] = f'Bearer {jwt_token}'
    return headers

@trading_bp.route('/trade', methods=['POST'])
def trade():
    try:
        data = request.get_json()
        action = data.get('action')  # 'buy', 'sell', 'hold'
        
        if action == 'hold':
            return jsonify({'message': '포지션 유지'}), 200
            
        market = "KRW-BTC"  # 비트코인 마켓
        
        if action == 'buy':
            # 매수 가능한 KRW 조회
            balance_url = f"{SERVER_URL}/v1/accounts"
            balance_resp = requests.get(balance_url, headers=get_headers())
            krw_balance = next((item['balance'] for item in balance_resp.json() 
                              if item['currency'] == 'KRW'), 0)
            
            # 현재가 조회
            price_url = f"{SERVER_URL}/v1/ticker?markets={market}"
            price_resp = requests.get(price_url)
            current_price = price_resp.json()[0]['trade_price']
            
            # 매수 주문
            query = {
                'market': market,
                'side': 'bid',
                'volume': str(float(krw_balance) / current_price * 0.9995),  # 수수료 고려
                'price': str(current_price),
                'ord_type': 'limit',
            }
            
            order_url = f"{SERVER_URL}/v1/orders"
            response = requests.post(order_url, json=query, headers=get_headers(query))
            
            return jsonify({'message': '매수 주문 완료', 'data': response.json()}), 200
            
        elif action == 'sell':
            # 보유 BTC 수량 조회
            balance_url = f"{SERVER_URL}/v1/accounts"
            balance_resp = requests.get(balance_url, headers=get_headers())
            btc_balance = next((item['balance'] for item in balance_resp.json() 
                              if item['currency'] == 'BTC'), 0)
            
            # 현재가 조회
            price_url = f"{SERVER_URL}/v1/ticker?markets={market}"
            price_resp = requests.get(price_url)
            current_price = price_resp.json()[0]['trade_price']
            
            # 매도 주문
            query = {
                'market': market,
                'side': 'ask',
                'volume': btc_balance,
                'price': str(current_price),
                'ord_type': 'limit',
            }
            
            order_url = f"{SERVER_URL}/v1/orders"
            response = requests.post(order_url, json=query, headers=get_headers(query))
            
            return jsonify({'message': '매도 주문 완료', 'data': response.json()}), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
