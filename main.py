import os
import time
import random
import uuid
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# التوكن من إعدادات السيرفر
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# المسار الرئيسي للموقع
@app.route('/')
def index():
    return render_template('index.html')

# مسار التحقق من الآيدي (كمثال)
@app.route('/api/verify-id', methods=['POST'])
def verify_id():
    data = request.json
    # أضف هنا منطق التحقق الخاص بك
    return jsonify({"status": "success", "message": "تم إرسال الكود"})

# مسار التحقق من الكود (كمثال)
@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    # أضف هنا منطق التحقق الخاص بك
    return jsonify({"status": "success", "session_token": str(uuid.uuid4()), "redirect_token": "xyz123"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
