import time
import random
import uuid
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# توكن بوت الحماية الخاص بمتجرك N7L
BOT_TOKEN = "8346972966:AAGJpcm8XOroKT4VE-o38Ky4JEHXILsb1-k"

# قاعدة بيانات وهمية للمشتركين (الآيدي والفئة المسموحة: 3، 5، 6)
# يمكنك إضافة آيديات زبائنك هنا لاحقاً بنفس الطريقة
ALLOWED_USERS = {
    "123456789": {"group": 3},
    "987654321": {"group": 5},
    "555666777": {"group": 6}
}

# تخزين الأكواد المؤقتة (OTP) والجلسات (Sessions)
pending_otps = {}  
active_sessions = {} 

# متغيرات حماية الرابط (يتغير كل 15 دقيقة)
current_link_token = str(uuid.uuid4())[:8]
last_token_update = time.time()

def update_link_token():
    global current_link_token, last_token_update
    if time.time() - last_token_update > 900:  # 15 دقيقة
        current_link_token = str(uuid.uuid4())[:8]
        last_token_update = time.time()
    return current_link_token

@app.route('/get-current-token', methods=['GET'])
def get_token():
    token = update_link_token()
    return jsonify({"token": token})

# 1. خطوة فحص الآيدي وإرسال كود التحقق الفعلي عبر تليجرام
@app.route('/api/verify-id', methods=['POST'])
def verify_id():
    data = request.json
    user_id = str(data.get('user_id'))
    
    if user_id in ALLOWED_USERS and ALLOWED_USERS[user_id]["group"] in [3, 5, 6]:
        otp_code = str(random.randint(1000, 9999))
        pending_otps[user_id] = {
            "code": otp_code,
            "expire": time.time() + 60  # صلاحية دقيقة واحدة
        }
        
        # إرسال الكود الفعلي للمستخدم عبر البوت
        bot_response = send_otp_via_protection_bot(user_id, otp_code)
        
        return jsonify({"status": "success", "message": "تم إرسال كود التحقق إلى حسابك على تليجرام عبر بوت الحماية."})
    
    return jsonify({"status": "error", "message": "الآيدي غير مسجل أو ليس لديك صلاحية الدخول."})

# 2. خطوة فحص كود التحقق ودخول الموقع
@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    user_id = str(data.get('user_id'))
    user_code = str(data.get('code'))
    
    if user_id in pending_otps:
        otp_data = pending_otps[user_id]
        if time.time() <= otp_data["expire"]:
            if otp_data["code"] == user_code:
                session_token = str(uuid.uuid4())
                active_sessions[session_token] = {
                    "user_id": user_id,
                    "expire": time.time() + 3600  # ساعة كاملة
                }
                del pending_otps[user_id]
                return jsonify({"status": "success", "session_token": session_token, "redirect_token": current_link_token})
            else:
                return jsonify({"status": "error", "message": "كود التحقق غير صحيح."})
        else:
            return jsonify({"status": "error", "message": "انتهت صلاحية الكود (1 دقيقة)، اطلب كود جديد."})
            
    return jsonify({"status": "error", "message": "حدث خطأ، يرجى إعادة المحاولة."})

def send_otp_via_protection_bot(user_id, code):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": f"🔐 كود التحقق المؤقت الخاص بك لمتجر N7L هو: {code}\n⏱ الكود صالح لمدة دقيقة واحدة فقط."
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
