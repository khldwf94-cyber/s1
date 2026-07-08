import time
import random
import uuid
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# قاعدة بيانات وهمية للمشتركين (الآيدي والفئة المسموحة: 3، 5، 6)
# يمكنك تعديل الأرقام هنا أو ربطها ببوت الشراء لاحقاً
ALLOWED_USERS = {
    "123456789": {"group": 3},
    "987654321": {"group": 5},
    "555666777": {"group": 6}
}

# تخزين الأكواد المؤقتة (OTP) والجلسات (Sessions)
pending_otps = {}  # { user_id: {"code": "1234", "expire": timestamp} }
active_sessions = {} # { session_token: {"user_id": "...", "expire": timestamp} }

# متغيرات حماية الرابط (يتغير كل 15 دقيقة)
current_link_token = str(uuid.uuid4())[:8]
last_token_update = time.time()

def update_link_token():
    global current_link_token, last_token_update
    # إذا مرت 15 دقيقة (900 ثانية)، غيّر الرابط
    if time.time() - last_token_update > 900:
        current_link_token = str(uuid.uuid4())[:8]
        last_token_update = time.time()
    return current_link_token

@app.route('/get-current-token', methods=['GET'])
def get_token():
    token = update_link_token()
    return jsonify({"token": token})

# 1. خطوة فحص الآيدي وإرسال كود التحقق
@app.route('/api/verify-id', methods=['POST'])
def verify_id():
    data = request.json
    user_id = str(data.get('user_id'))
    
    # التأكد من وجود الآيدي ومن فئة المجموعات المسموحة (3، 5، 6)
    if user_id in ALLOWED_USERS and ALLOWED_USERS[user_id]["group"] in [3, 5, 6]:
        # توليد كود تحقق عشوائي من 4 أرقام
        otp_code = str(random.randint(1000, 9999))
        # ينتهي بعد دقيقة واحدة (60 ثانية)
        pending_otps[user_id] = {
            "code": otp_code,
            "expire": time.time() + 60
        }
        
        # [هنا يتم إرسال الكود عبر بوت الحماية إلى التليجرام]
        print(send_otp_via_protection_bot(user_id, otp_code))
        
        return jsonify({"status": "success", "message": "تم إرسال كود التحقق إلى بوت الحماية الخاص بك على تليجرام."})
    
    return jsonify({"status": "error", "message": "الآيدي غير مسجل أو ليس لديك صلاحية الدخول."})

# 2. خطوة فحص كود التحقق ودخول الموقع
@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    user_id = str(data.get('user_id'))
    user_code = str(data.get('code'))
    
    if user_id in pending_otps:
        otp_data = pending_otps[user_id]
        # التأكد أن الكود لم تنتهِ مدته (دقيقة) وأن الكود صحيح
        if time.time() <= otp_data["expire"]:
            if otp_data["code"] == user_code:
                # توليد توكن جلسة للدخول لمدة ساعة (60 دقيقة)
                session_token = str(uuid.uuid4())
                active_sessions[session_token] = {
                    "user_id": user_id,
                    "expire": time.time() + 3600  # ساعة كاملة
                }
                # حذف كود الـ OTP بعد الاستخدام
                del pending_otps[user_id]
                return jsonify({"status": "success", "session_token": session_token, "redirect_token": current_link_token})
            else:
                return jsonify({"status": "error", "message": "كود التحقق غير صحيح."})
        else:
            return jsonify({"status": "error", "message": "انتهت صلاحية الكود (1 دقيقة)، اطلب كود جديد."})
            
    return jsonify({"status": "error", "message": "حدث خطأ، يرجى إعادة المحاولة."})

def send_otp_via_protection_bot(user_id, code):
    # محاكاة إرسال بوت الحماية للكود (هنا تربط توكن البوت حقك لاحقاً)
    return f"[بوت الحماية] تم إرسال الكود {code} إلى المستخدم {user_id} بنجاح."

if __name__ == '__main__':
    app.run(port=5000, debug=True)
