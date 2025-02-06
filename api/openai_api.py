from flask import Blueprint, request, jsonify
import openai
from dotenv import load_dotenv
import os

# 환경 변수 로드
load_dotenv()

# Blueprint 생성
openai_bp = Blueprint('openai', __name__)

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

@openai_bp.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"error": "Invalid input"}), 400

        user_input = data["message"]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_input}]
        )
        reply = response["choices"][0]["message"]["content"]

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500 