import os
import time
import random
import threading
from flask import Flask, request, session, render_template_string, redirect, url_for
import telebot

# 1. إعداد البوت والتوكن الفعلي الخاص بك
BOT_TOKEN = "8346972966:AAGJpcm8XOroKT4VE-o38Ky4JEHXILsb1-k"
protection_bot = telebot.TeleBot(BOT_TOKEN)

# 👑 آيدي حسابك الأساسي (الأدمن)
ADMIN_ID = 5432340735 

# 📢 آيدي قناتك الخاصة بالعملاء المشتريين
BUYERS_CHAT_ID = -1002360216668  

app = Flask(__name__)
app.secret_key = os.urandom(24) 

# لحفظ جلسات المشتركين النشطة
ACTIVE_SESSIONS = {}
VERIFICATION_CODES = {}

# 2. واجهة التحكم المصممة كصفحة نصوص منسقة مع روابط مخفية داخل الكلمات بالكامل
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>N7L STORE | ControlC</title>
    <style>
        body {
            background-color: #0b0c10;
            color: #c5c6c7;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 40px 20px;
            margin: 0;
        }
        @media print { body { display: none; } }
        
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: #151a21;
            padding: 25px;
            border-radius: 8px;
            border: 1px solid #1f2833;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            text-align: right;
        }
        
        .title-bar {
            border-bottom: 1px solid #2d3748;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        .title-bar h2 {
            margin: 0;
            color: #ffffff;
            font-size: 20px;
        }
        .title-bar p {
            margin: 5px 0 0 0;
            font-size: 12px;
            color: #718096;
        }
        
        /* صندوق النص الشبيه بـ ControlC */
        .paste-box {
            background-color: #0d1117;
            border: 1px solid #21262d;
            border-radius: 6px;
            padding: 20px;
            font-family: monospace, 'Courier New', Courier;
            font-size: 14px;
            line-height: 1.8;
            white-space: pre-wrap;
            word-wrap: break-word;
            color: #c9d1d9;
        }

        /* تنسيق الروابط المخفية داخل النصوص */
        .paste-box a {
            color: #58a6ff;
            text-decoration: none;
            border-bottom: 1px dashed #58a6ff;
            transition: 0.2s;
            font-weight: bold;
        }
        .paste-box a:hover {
            color: #1f6feb;
            border-bottom-style: solid;
        }
        
        /* تنسيق التحذيرات */
        .warning-text {
            color: #ff7b72;
            font-weight: bold;
        }
        
        /* التبويبات والأقسام الرئيسية */
        .section-header {
            color: #aff5b4;
            font-size: 16px;
            margin-top: 25px;
            margin-bottom: 10px;
            font-weight: bold;
            display: block;
            border-bottom: 1px solid #21262d;
            padding-bottom: 5px;
        }

        /* فورم تسجيل الدخول */
        .login-form {
            text-align: center;
        }
        input[type="text"] {
            width: 100%;
            padding: 12px;
            margin: 15px 0;
            border: 1px solid #30363d;
            background: #0d1117;
            color: #fff;
            border-radius: 6px;
            box-sizing: border-box;
            text-align: center;
            font-size: 16px;
        }
        button {
            width: 100%;
            padding: 12px;
            background-color: #238636;
            color: #ffffff;
            border: 1px solid #2ea44f;
            border-radius: 6px;
            font-weight: bold;
            font-size: 16px;
            cursor: pointer;
            transition: 0.2s;
        }
        button:hover { 
            background-color: #2ea44f; 
        }
        
        .error { color: #f85149; text-align: center; margin-bottom: 15px; font-weight: bold; }
        .success { color: #56d364; text-align: center; margin-bottom: 15px; font-weight: bold; }
        
        .logout-btn {
            display: block;
            text-align: center;
            margin-top: 25px;
            color: #f85149;
            text-decoration: none;
            font-size: 13px;
            font-weight: bold;
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
        <div class="title-bar">
            <h2>N7L STORE | تجميعة المودات الأمنة</h2>
            <p>بوابة حماية وتوزيع الروابط الرقمية الخاصة بالعملاء المشتركين</p>
        </div>
        
        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}

        {% if not logged_in %}
            <div class="login-form">
                {% if not step_two %}
                    <form action="/login_step1" method="POST">
                        <p style="font-size: 14px; color: #8b949e;">أدخل آيدي التليجرام الخاص بك لتلقي رمز التحقق الثنائي (OTP)</p>
                        <input type="text" name="user_id" placeholder="مثال: 5432340735" required autocomplete="off">
                        <button type="submit">إرسال كود التحقق</button>
                    </form>
                {% else %}
                    <form action="/login_step2" method="POST">
                        <p class="success">📩 تم إرسال الرمز إلى حسابك بتليجرام.</p>
                        <input type="text" name="otp_code" placeholder="أدخل كود التحقق المستلم" required autocomplete="off">
                        <button type="submit">تأكيد ودخول</button>
                    </form>
                {% endif %}
            </div>
        {% else %}
            <div class="paste-box">
<span class="warning-text">‼️ ماراح مسامح اي شخص يسرب التجميعه او ياخذ المودات منها او ياخذ التجميعه بدون مايشتريها ‼️</span>

حقوق متجر : N7L

حقوق مالك المتجر : <a href="https://t.me/III888IIIII" target="_blank">اضغط هنا للتواصل</a>

حقوق متجر : <a href="https://t.me/pp32b" target="_blank">اضغط هنا</a>

Tik : <a href="https://www.tiktok.com/@ihf918" target="_blank">@ihf918</a>

Tik : <a href="https://www.tiktok.com/@b6a1_" target="_blank">@b6a1_</a>

<a href="https://www.mediafire.com/file_premium/0x03rnq40jntw4/vehicles.zip/file" target="_blank">الملف الشامل للمركبات (vehicles.zip)</a>

<span class="section-header">مواتر</span>

<a href="/logout" style="color: #ff7b72; font-weight: bold; text-decoration: none;">[ خروج آمن ]</a>
            </div>
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
        return render_template_string(HTML_PAGE, error="❌ هذا الآيدي غير مسجل في النظام كـ (مشتري).", step_two=False, logged_in=False)
        
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
