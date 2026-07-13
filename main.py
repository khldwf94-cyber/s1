import os
import time
import random
import threading
from flask import Flask, request, session, render_template_string, redirect, url_for
import telebot

# 1. إعداد البوت والتوكن الفعلي الخاص بك
BOT_TOKEN = "8346972966:AAGJpcm8XOroKT4VE-o38Ky4JEHXILsb1-k"
protection_bot = telebot.TeleBot(BOT_TOKEN)

# 👑 آيدي حسابك الأساسي (الأدمن) - يدخل دائماً ومستثنى من أي قيود
ADMIN_ID = 5432340735 

# 📢 آيدي قناتك الخاصة (تم استخراجه ليتوافق مع رابط قناتك الخاصة)
BUYERS_CHAT_ID = -1002360216668  # الآيدي الرقمي التابع لرابط قناتك (+YjIKDxJjhsw1MDY8)

app = Flask(__name__)
app.secret_key = os.urandom(24) 

# لحفظ جلسات المشتركين النشطة مؤقتاً لتجنب تكرار تسجيل الدخول
ACTIVE_SESSIONS = {}
VERIFICATION_CODES = {}

# 2. واجهة الدخول الموحدة (المودات تظهر فوراً في نفس الصفحة بعد إدخال الكود)
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>بوابة الحماية | متجر N7L</title>
    <style>
        body {
            background-color: #0b0c10;
            color: #c5c6c7;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
            padding: 50px 20px;
        }
        @media print { body { display: none; } }
        .container {
            max-width: 400px;
            margin: 0 auto;
            background-color: #1f2833;
            padding: 30px;
            border-radius: 10px;
            border: 1px solid #45f3ff;
            box-shadow: 0 0 15px rgba(69, 243, 255, 0.2);
        }
        h2 { color: #45f3ff; margin-bottom: 25px; }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 1px solid #45f3ff;
            background: #0b0c10;
            color: #fff;
            border-radius: 5px;
            box-sizing: border-box;
            text-align: center;
            font-size: 16px;
        }
        button {
            width: 100%;
            padding: 12px;
            background-color: #45f3ff;
            color: #0b0c10;
            border: none;
            border-radius: 5px;
            font-weight: bold;
            font-size: 16px;
            cursor: pointer;
            transition: 0.3s;
        }
        button:hover { background-color: #1f2833; color: #45f3ff; border: 1px solid #45f3ff; }
        .error { color: #ff3333; margin: 15px 0; font-weight: bold; }
        .success { color: #00ff00; }
        p { font-size: 14px; line-height: 1.6; }
        
        .links-section {
            margin-top: 20px;
            text-align: right;
        }
        .link-card {
            display: block;
            background: #0b0c10;
            color: #45f3ff;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            text-align: center;
            border: 1px solid #1f2833;
            transition: 0.3s;
        }
        .link-card:hover {
            border-color: #45f3ff;
            background: #1f2833;
            color: #fff;
        }
        .logout-btn {
            display: inline-block;
            margin-top: 20px;
            color: #ff3333;
            text-decoration: none;
            font-size: 14px;
        }
    </style>
    <script>
        document.addEventListener('contextmenu', event => event.preventDefault());
        document.onkeydown = function(e) {
            if (e.keyCode == 123 || 
                (e.ctrlKey && e.shiftKey && e.keyCode == 73) || 
                (e.ctrlKey && e.shiftKey && e.keyCode == 74) || 
                (e.ctrlKey && e.keyCode == 85)) {
                return false;
            }
        };
    </script>
</head>
<body>
    <div class="container">
        <h2>🔒 بوابة التحقق الثنائي</h2>
        
        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}

        {% if not logged_in %}
            {% if not step_two %}
                <form action="/login_step1" method="POST">
                    <p>أدخل آيدي التليجرام الخاص بك لتلقي رمز التحقق (OTP)</p>
                    <input type="text" name="user_id" placeholder="مثال: 5432340735" required autocomplete="off">
                    <button type="submit">إرسال كود التحقق</button>
                </form>
            {% else %}
                <form action="/login_step2" method="POST">
                    <p class="success">📩 أرسلنا كود التحقق إلى حسابك في تليجرام.</p>
                    <input type="text" name="otp_code" placeholder="أدخل كود التحقق (OTP)" required autocomplete="off">
                    <button type="submit">تأكيد ودخول</button>
                </form>
            {% endif %}
        {% else %}
            <p class="success" style="font-size: 18px; font-weight: bold;">🎉 تم التحقق بنجاح!</p>
            <div class="links-section">
                <a href="https://t.me/+tPBT1R66qx43NGQ0" target="_blank" class="link-card">🔗 رابط المجموعة الأساسية</a>
                <a href="https://t.me/+Ha82GPmaPJ05Yzg0" target="_blank" class="link-card">🔗 رابط مودات محاكي الحوادث</a>
            </div>
            <a href="/logout" class="logout-btn">تسجيل الخروج الآمن 🔓</a>
        {% endif %}
    </div>
</body>
</html>
"""

# ==================== مسارات Flask ====================
@app.route('/')
def index():
    user_id = session.get('user_id')
    if user_id in ACTIVE_SESSIONS:
        if time.time() < ACTIVE_SESSIONS[user_id]['expires_at']:
            return render_template_string(HTML_PAGE, error=None, step_two=False, logged_in=True)
            
    session.clear()
    return render_template_string(HTML_PAGE, error=None, step_two=False, logged_in=False)

@app.route('/login_step1', methods=['POST'])
def login_step1():
    user_id_str = request.form.get('user_id')
    
    if not user_id_str or not user_id_str.isdigit():
        return render_template_string(HTML_PAGE, error="❌ الآيدي يجب أن يتكون من أرقام فقط.", step_two=False, logged_in=False)
        
    user_id = int(user_id_str)
    
    # 🛡️ التحقق التلقائي: هل العميل مشترك في القناة؟
    is_buyer = False
    
    if user_id == ADMIN_ID:
        is_buyer = True
    else:
        try:
            member = protection_bot.get_chat_member(chat_id=BUYERS_CHAT_ID, user_id=user_id)
            if member.status in ['member', 'administrator', 'creator']:
                is_buyer = True
        except Exception as e:
            print(f"Verification Error: {e}")
            is_buyer = False

    if not is_buyer:
        return render_template_string(HTML_PAGE, error="❌ هذا الآيدي غير مسجل في النظام كـ (مشتري في القناة).", step_two=False, logged_in=False)
        
    otp = str(random.randint(100000, 999999))
    VERIFICATION_CODES[user_id] = {
        'code': otp,
        'generated_at': time.time()
    }
    
    try:
        protection_bot.send_message(
            user_id, 
            f"🔒 كود التحقق لدخول موقع s1 هو:\n\n"
            f"`{otp}`\n\n"
            f"⏰ صالح للاستخدام لمدة 15 دقيقة فقط."
        )
        session['attempting_user_id'] = user_id
        return render_template_string(HTML_PAGE, error=None, step_two=True, logged_in=False)
    except Exception:
        return render_template_string(
            HTML_PAGE, 
            error="❌ فشل إرسال الكود. تأكد من ضغط /start في البوت أولاً لكي يستطيع مراسلتك.", 
            step_two=False,
            logged_in=False
        )

@app.route('/login_step2', methods=['POST'])
def login_step2():
    otp_input = request.form.get('otp_code')
    user_id = session.get('attempting_user_id')
    
    if not user_id or user_id not in VERIFICATION_CODES:
        return render_template_string(HTML_PAGE, error="❌ حدث خطأ في الجلسة. أعد إدخال الآيدي.", step_two=False, logged_in=False)
        
    code_data = VERIFICATION_CODES[user_id]
    
    if time.time() - code_data['generated_at'] > 900:
        VERIFICATION_CODES.pop(user_id, None)
        return render_template_string(HTML_PAGE, error="❌ انتهت صلاحية كود التحقق. أعد المحاولة.", step_two=False, logged_in=False)
        
    if otp_input == code_data['code']:
        client_ip = request.remote_addr
        ACTIVE_SESSIONS[user_id] = {
            'expires_at': time.time() + 5400,
            'current_ip': client_ip
        }
        session['user_id'] = user_id
        VERIFICATION_CODES.pop(user_id, None)
        return render_template_string(HTML_PAGE, error=None, step_two=False, logged_in=True)
    else:
        return render_template_string(HTML_PAGE, error="❌ كود التحقق غير صحيح. أعد المحاولة.", step_two=True, logged_in=False)

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id in ACTIVE_SESSIONS:
        ACTIVE_SESSIONS.pop(user_id, None)
    session.clear()
    return redirect(url_for('index'))

def run_bot():
    print("⚡ Starting Telegram Bot...")
    try:
        protection_bot.infinity_polling()
    except Exception as e:
        print(f"❌ Bot error: {e}")

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    print("⚡ Starting Flask Web Server...")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
