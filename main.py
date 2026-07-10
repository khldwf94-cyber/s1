import os
import threading
import telebot
import random
import time
from telebot import types
from flask import Flask, request, render_template_string, session, redirect, url_for

# 1. توكن بوت الحماية (تأكد من وضع توكن بوت الحماية الخاص بك هنا)
PROTECTION_BOT_TOKEN = "8346972966:AAGJpcm8XOroKT4VE-o38Ky4JEHXILsb1-k" 
ADMIN_ID = 5432340735  
protection_bot = telebot.TeleBot(PROTECTION_BOT_TOKEN)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# قاعدة بيانات العملاء المعتمدين (سيتم تفعيلها مؤقتاً لتجربة الدخول)
# ملحوظة: مستقبلاً يتم ربطها ببوت الشراء تلقائياً
APPROVED_USERS = {
    # 'ايدي_العميل': {'expires_at': time.time() + 86400, 'current_ip': None}
}
VERIFICATION_CODES = {} 

# تشغيل استقبال الرسائل لبوت الحماية (لو أرسل له العميل شيئاً)
@protection_bot.message_handler(commands=['start'])
def welcome_protection(message):
    # تسجيل تلقائي مبدئي للعميل عند تفعيل بوت الحماية لتسهيل الدخول والمحاكاة
    user_id = message.from_user.id
    if user_id not in APPROVED_USERS:
        APPROVED_USERS[user_id] = {'expires_at': time.time() + 86400 * 30, 'current_ip': None}
    protection_bot.reply_to(message, f"🔒 أهلاً بك في بوت الحماية الخاص بمتجر N7L.\nآيدي حسابك هو: `{user_id}`\nيمكنك الآن استخدام هذا الآيدي للدخول إلى موقع التحقق s1.")

# 2. واجهة موقع التحقق s1 الآمن (HTML + حماية ضد التصوير والنسخ)
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>N7L STORE - نظام التحقق s1</title>
    <style>
        body { user-select: none; -webkit-user-select: none; background-color: #121212; color: #ffffff; font-family: Arial, sans-serif; text-align: center; padding: 50px 20px; }
        @media print { body { display: none; } }
        .container { max-width: 400px; margin: 0 auto; background: #1e1e1e; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        input { width: 90%; padding: 10px; margin: 15px 0; border: 1px solid #333; border-radius: 5px; background: #2a2a2a; color: white; text-align: center; }
        button { background: #ffcc00; color: black; border: none; padding: 12px 25px; font-weight: bold; border-radius: 5px; cursor: pointer; width: 90%; }
        .error { color: #ff3333; margin-bottom: 15px; }
        .success { color: #00ff00; }
    </style>
    <script>
        document.addEventListener('contextmenu', event => event.preventDefault());
        document.addEventListener('keydown', function(e) {
            if (e.key === "PrintScreen" || (e.ctrlKey && e.shiftKey && e.key === "I") || (e.ctrlKey && e.key === "u")) {
                e.preventDefault();
                alert("الحماية نشطة: غير مسموح بالتصوير أو فحص الصفحة!");
            }
        });
    </script>
</head>
<body>
    <div class="container">
        <h2>🔒 بوابة التحقق s1</h2>
        <p>نظام حماية متجر نحل المشترك</p>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        {% if not step_two %}
            <form method="POST" action="/login_step1">
                <label>أدخل الآيدي الخاص بك:</label>
                <input type="text" name="user_id" required placeholder="مثال: 5432340735">
                <button type="submit">إرسال كود التحقق عبر بوت الحماية</button>
            </form>
        {% else %}
            <form method="POST" action="/login_step2">
                <p class="success">تم إرسال كود الـ OTP إلى حسابك عبر بوت الحماية.</p>
                <label>أدخل كود التحقق:</label>
                <input type="text" name="otp_code" required placeholder="X X X X X X">
                <button type="submit">دخول وتفعيل الجلسة</button>
            </form>
        {% endif %}
    </div>
</body>
</html>
"""

CONTENT_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>N7L STORE - المودات والروابط</title>
    <style> body { background: #121212; color: white; text-align: center; padding: 50px; user-select: none; } .box { background: #1e1e1e; padding: 30px; border-radius: 10px; display: inline-block; } a { color: #ffcc00; display: block; margin: 15px 0; font-size: 18px; } </style>
</head>
<body>
    <div class="box">
        <h2>🎁 مستودع المودات والروابط الآمن</h2>
        <p>جلسة الدخول الخاصة بك نشطة لمدة 90 دقيقة على هذا الجهاز.</p>
        <hr>
        <a href="https://t.me/+tPBT1R66qx43NGQ0" target="_blank">رابط الدخول للمجموعة الأساسية</a>
        <a href="https://t.me/+Ha82GPmaPJ05Yzg0" target="_blank">رابط مودات محاكي الحوادث المدفوعة</a>
    </div>
</body>
</html>
"""

# 3. مسارات ويب ومطابقة المدخلات وبوت الحماية
@app.route('/')
def index():
    if 'user_id' in session:
        user_id = session['user_id']
        if user_id in APPROVED_USERS and time.time() < APPROVED_USERS[user_id]['expires_at']:
            if APPROVED_USERS[user_id]['current_ip'] == request.remote_addr:
                return render_template_string(CONTENT_PAGE)
    return render_template_string(HTML_PAGE, error=None, step_two=False)

@app.route('/login_step1', methods=['POST'])
def login_step1():
    user_id_str = request.form.get('user_id')
    if not user_id_str.isdigit():
        return render_template_string(HTML_PAGE, error="الآيدي يجب أن يكون أرقاماً فقط.", step_two=False)
    
    user_id = int(user_id_str)
    
    if user_id not in APPROVED_USERS:
        return render_template_string(HTML_PAGE, error="هذا الآيدي غير معتمد في بوابة s1 حالياً.", step_two=False)
    
    otp = str(random.randint(100000, 999999))
    VERIFICATION_CODES[user_id] = {'code': otp, 'generated_at': time.time()}
    
    try:
        # هنا بوت الحماية هو الذي يرسل الكود وليس بوت الشراء
        protection_bot.send_message(user_id, f"🔒 كود التحقق لدخول موقع s1 هو:\n\n`{otp}`\n\n🕒 صالح لـ 15 دقيقة.")
        session['attempting_user_id'] = user_id
        return render_template_string(HTML_PAGE, error=None, step_two=True)
    except Exception:
        return render_template_string(HTML_PAGE, error="تأكد من بدء تشغيل بوت الحماية أولاً لإرسال الكود.", step_two=False)

@app.route('/login_step2', methods=['POST'])
def login_step2():
    otp_input = request.form.get('otp_code')
    user_id = session.get('attempting_user_id')
    
    if not user_id or user_id not in VERIFICATION_CODES:
        return redirect(url_for('index'))
    
    code_data = VERIFICATION_CODES[user_id]
    if time.time() - code_data['generated_at'] > 900:
        return render_template_string(HTML_PAGE, error="انتهت صلاحية الكود.", step_two=False)
    
    if otp_input == code_data['code']:
        client_ip = request.remote_addr
        
        if APPROVED_USERS[user_id]['current_ip'] and APPROVED_USERS[user_id]['current_ip'] != client_ip:
            protection_bot.send_message(ADMIN_ID, f"🚨 تحذير: محاولة دخول متعدد من آيدي العميل: {user_id}")
            APPROVED_USERS.pop(user_id, None)
            session.clear()
            return render_template_string(HTML_PAGE, error="تم رصد جهازين، تم قفل الحساب للحماية.", step_two=False)
        
        APPROVED_USERS[user_id]['expires_at'] = time.time() + 5400  # 90 دقيقة
        APPROVED_USERS[user_id]['current_ip'] = client_ip
        session['user_id'] = user_id
        return render_template_string(CONTENT_PAGE)
    else:
        return render_template_string(HTML_PAGE, error="الكود غير صحيح!", step_two=True)

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    protection_bot.infinity_polling()
