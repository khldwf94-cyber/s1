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

# 2. واجهة التحكم المصممة كصفحة نصوص منسقة
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>N7L STORE | ControlC</title>
    <style>
        body { background-color: #0b0c10; color: #c5c6c7; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 40px 20px; margin: 0; }
        .container { max-width: 600px; margin: 0 auto; background-color: #151a21; padding: 25px; border-radius: 8px; border: 1px solid #1f2833; box-shadow: 0 4px 15px rgba(0,0,0,0.5); text-align: right; }
        .title-bar { border-bottom: 1px solid #2d3748; padding-bottom: 15px; margin-bottom: 20px; }
        .title-bar h2 { margin: 0; color: #ffffff; font-size: 20px; }
        .paste-box { background-color: #0d1117; border: 1px solid #21262d; border-radius: 6px; padding: 20px; font-family: monospace; font-size: 14px; line-height: 1.8; color: #c9d1d9; }
        .paste-box a { color: #58a6ff; text-decoration: none; font-weight: bold; }
        input[type="text"], button { width: 100%; padding: 12px; margin: 15px 0; border: 1px solid #30363d; background: #0d1117; color: #fff; border-radius: 6px; box-sizing: border-box; }
        button { background-color: #238636; border: 1px solid #2ea44f; font-weight: bold; cursor: pointer; }
        .error { color: #f85149; text-align: center; font-weight: bold; }
        .success { color: #56d364; text-align: center; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="title-bar">
            <h2>N7L STORE | تجميعة المودات الأمنة</h2>
        </div>
        
        {% if error %}<p class="error">{{ error }}</p>{% endif %}

        {% if not logged_in %}
            <div class="login-form">
                {% if not step_two %}
                    <form action="/login_step1" method="POST">
                        <input type="text" name="user_id" placeholder="أدخل آيدي التليجرام" required>
                        <button type="submit">إرسال كود التحقق</button>
                    </form>
                {% else %}
                    <form action="/login_step2" method="POST">
                        <p class="success">📩 تم إرسال الرمز لتليجرام.</p>
                        <input type="text" name="otp_code" placeholder="أدخل كود التحقق" required>
                        <button type="submit">تأكيد ودخول</button>
                    </form>
                {% endif %}
            </div>
        {% else %}
            <div class="paste-box">
                حقوق مالك المتجر : <a href="https://t.me/III888IIIII" target="_blank">اضغط هنا للتواصل</a><br>
                حقوق متجر : <a href="https://t.me/pp32b" target="_blank">اضغط هنا</a><br>
                Tik : <a href="https://www.tiktok.com/@ihf918" target="_blank">@ihf918</a><br>
                Tik : <a href="https://www.tiktok.com/@b6a1_" target="_blank">@b6a1_</a>
                <br><br>
                <a href="/logout" style="color: #ff7b72;">[ خروج آمن ]</a>
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
    
    is_buyer = (user_id == ADMIN_ID)
    if not is_buyer:
        try:
            member = protection_bot.get_chat_member(chat_id=BUYERS_CHAT_ID, user_id=user_id)
            if member.status in ['member', 'administrator', 'creator']:
                is_buyer = True
        except: is_buyer = False

    if not is_buyer:
        return render_template_string(HTML_PAGE, error="❌ هذا الآيدي غير مسجل.", step_two=False, logged_in=False)
        
    otp = str(random.randint(100000, 999999))
    VERIFICATION_CODES[user_id] = {'code': otp, 'generated_at': time.time()}
    try:
        protection_bot.send_message(user_id, f"🔒 كود التحقق الخاص بك هو: `{otp}`")
        session['attempting_user_id'] = user_id
        return render_template_string(HTML_PAGE, error=None, step_two=True, logged_in=False)
    except:
        return render_template_string(HTML_PAGE, error="❌ فشل إرسال الكود.", step_two=False, logged_in=False)

@app.route('/login_step2', methods=['POST'])
def login_step2():
    otp_input = request.form.get('otp_code')
    user_id = session.get('attempting_user_id')
    if user_id and user_id in VERIFICATION_CODES and otp_input == VERIFICATION_CODES[user_id]['code']:
        ACTIVE_SESSIONS[user_id] = {'expires_at': time.time() + 5400, 'current_ip': request.remote_addr}
        session['user_id'] = user_id
        return render_template_string(HTML_PAGE, error=None, step_two=False, logged_in=True)
    return render_template_string(HTML_PAGE, error="❌ كود غير صحيح.", step_two=True, logged_in=False)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
