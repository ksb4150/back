from flask import Flask
from flask_cors import CORS
from api.upbit_connect import connect_bp
from api.upbit_trading import trading_bp
from api.openai_api import openai_bp
from api.upbit_crawling import crawling_bp

app = Flask(__name__)
CORS(app)  # React와의 CORS 이슈 해결

# Blueprint 등록
app.register_blueprint(connect_bp, url_prefix='/api-test/upbit')
app.register_blueprint(trading_bp, url_prefix='/api-test/trading')
app.register_blueprint(openai_bp, url_prefix='/api-test/openai')
app.register_blueprint(crawling_bp, url_prefix='/api-test/crawling')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
