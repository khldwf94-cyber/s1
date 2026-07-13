import os
import threading
import telebot
import random
import time
from telebot import types
from flask import Flask, request, render_template_string, session, redirect, url_for

# 1. توكن بوت الحماية الجديد الخاص بك
PROTECTION_BOT_TOKEN = "8346972966:AAGJpcm8XOroKT4VE-o38Ky4JEHXILsb1-k" 
ADMIN_ID = 5432340735  # آيديك لاستلام تنبيهات الدخول المتعدد
protection_bot = telebot.TeleBot(PROTECTION_BOT_TOKEN)

app = Flask(__name__)
app.secret_key = os.urandom(24) # لتشفير الجلسات وحماية الـ Cookies

# قائمة المشتركين (آيديك مضاف تلقائياً لتجربة الموقع مباشرة)
APPROVED_USERS = {
    5432340735: {'expires_at': time.time() + 86400 * 30, 'current_ip': None}
}
VERIFICATION_CODES = {} 

# تفعيل استقبال الرسائل لبوت الحماية
@protection_bot.message_handler(commands=['start'])
def welcome_protection(message):
    user_id = message.from_user.id
    if user_id not in APPROVED_USERS:
        APPROVED_USERS[user_id] = {'expires_at': time.time() + 86400 * 30, 'current_ip': None}
    protection_bot.reply_to(message, f"🔒 أهلاً بك في بوت حماية متجر N7L.\nآيدي حسابك هو: `{user_id}`\n\nيمكنك الآن استخدامه للدخول للموقع الآمن.")

# 2. تصميم صفحة التحقق s1 (مع حظر تصوير الشاشة والنسخ والـ DevTools)
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>N7L STORE - بوابة التحقق الآمن s1</title>
    <style>
        body { 
            user-select: none; 
            -webkit-user-select: none; 
            background-color: #121212; 
            color: #ffffff; 
            font-family: Arial, sans-serif; 
            text-align: center; 
            padding: 50px 20px; 
        }
        @media print { body { display: none; } } /* إخفاء الصفحة عند محاولة الحفظ كـ PDF أو الطباعة */
        .container { 
            max-width: 400px; 
            margin: 0 auto; 
            background: #1e1e1e; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.5); 
        }
        input { 
            width: 90%; 
            padding: 12px; 
            margin: 15px 0; 
            border: 1px solid #333; 
            border-radius: 5px; 
            background: #2a2a2a; 
            color: white; 
            text-align: center; 
            font-size: 16px;
        }
        button { 
            background: #ffcc00; 
            color: black; 
            border: none; 
            padding: 12px 25px; 
            font-weight: bold; 
            border-radius: 5px; 
            cursor: pointer; 
            width: 95%; 
            font-size: 16px;
        }
        button:hover { background: #e6b800; }
        .error { color: #ff3333; margin-bottom: 15px; font-weight: bold; }
        .success { color: #00ff00; }
    </style>
    <script>
        // تعطيل الزر الأيمن للماوس لمنع فحص العناصر
        document.addEventListener('contextmenu', event => event.preventDefault());
        
        // تعطيل اختصارات لوحة المفاتيح الشهيرة للتصوير أو فتح الـ DevTools
        document.addEventListener('keydown', function(e) {
            if (e.key === "PrintScreen" || 
                (e.ctrlKey && e.shiftKey && e.key === "I") || 
                (e.ctrlKey && e.shiftKey && e.key === "C") || 
                (e.ctrlKey && e.key === "u") || 
                (e.metaKey && e.shiftKey && e.key === "4")) { // للماك
                e.preventDefault();
                alert("🔒 عذراً، حماية المتجر نشطة. غير مسموح بالتصوير أو الفحص!");
            }
        });
    </script>
</head>
<body>
    <div class="container">
        <h2>🔒 بوابة التحقق s1</h2>
        <p>نظام حماية وتوزيع مودات متجر نحل</p>
        <hr style="border: 1px solid #333; margin: 20px 0;">
        
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        
        {% if not step_two %}
            <form method="POST" action="/login_step1">
                <label>أدخل آيدي التليجرام الخاص بك المعتمد:</label>
                <input type="text" name="user_id" required placeholder="مثال: 5432340735">
                <button type="submit">إرسال كود التحقق 💬</button>
            </form>
        {% else %}
            <form method="POST" action="/login_step2">
                <p class="success">📩 أرسلنا كود التحقق إلى حسابك في تليجرام.</p>
                <label>أدخل كود التحقق (OTP):</label>
                <input type="text" name="otp_code" required placeholder="X X X X X X">
                <button type="submit">دخول وتفعيل الجلسة 🔓</button>
            </form>
        {% endif %}
    </div>
</body>
</html>
"""

# 3. صفحة عرض المودات المحمية (عدّل الروابط هنا لتناسب قنواتك)
CONTENT_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>N7L STORE - المودات والروابط الآمنة</title>
    <style> 
        body { 
            background: #121212; 
            color: white; 
            text-align: center; 
            padding: 50px; 
            user-select: none; 
            -webkit-user-select: none;
        } 
        .box { 
            background: #1e1e1e; 
            padding: 40px; 
            border-radius: 10px; 
            display: inline-block; 
            max-width: 500px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        } 
        h2 { color: #ffcc00; }
        a { 
            color: #ffcc00; 
            display: block; 
            margin: 15px 0; 
            font-size: 18px; 
            text-decoration: none;
            padding: 10px;
            background: #2a2a2a;
            border-radius: 5px;
        } 
        a:hover { background: #3a3a3a; }
    </style>
    <script>
        document.addEventListener('contextmenu', event => event.preventDefault());
    </script>
</head>
<body>
    <div class="box">
        <h2>🎁 مستودع المودات والروابط الآمن (s1)</h2>
        <p>جلسة دخولك نشطة الآن لمدة 90 دقيقة فقط على هذا الجهاز.</p>
        <hr style="border: 1px solid #333; margin: 20px 0;">
        
        <a href="https://t.me/+tPBT1R66qx43NGQ0" target="_blank">🔗 رابط المجموعة الأساسية</a>
        <a href="https://t.me/+Ha82GPmaPJ05Yzg0" target="_blank">🔗 رابط مودات محاكي الحوادث</a>
    </div>
</body>
</html>
"""

# 4. منطق عمل السيرفر والتحقق من الجلسات والـ IP
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
        return render_template_string(HTML_PAGE, error="الآيدي يجب أن يتكون من أرقام فقط.", step_two=False)
    
    user_id = int(user_id_str)
    
    # التأكد أن العميل معتمد
    if user_id not in APPROVED_USERS:
        return render_template_string(HTML_PAGE, error="هذا الآيدي غير مسجل في النظام. تواصل مع الإدارة لتفعيل حسابك.", step_two=False)
    
    # توليد كود OTP من 6 أرقام
    otp = str(random.randint(100000, 999999))
    VERIFICATION_CODES[user_id] = {'code': otp, 'generated_at': time.time()}
    
    try:
        # إرسال الكود للعميل عبر بوت الحماية بالتوكن الجديد
        protection_bot.send_message(user_id, f"🔒 كود التحقق لدخول موقع s1 هو:\n\n`{otp}`\n\n🕒 صالح للاستخدام لمدة 15 دقيقة فقط.")
        session['attempting_user_id'] = user_id
        return render_template_string(HTML_PAGE, error=None, step_two=True)
    except Exception:
        return render_template_string(HTML_PAGE, error="فشل إرسال الكود. تأكد من أنك قمت بالدخول على بوت الحماية والضغط على /start أولاً لكي يستطيع مراسلتك.", step_two=False)

@app.route('/login_step2', methods=['POST'])
def login_step2():
    otp_input = request.form.get('otp_code')
    user_id = session.get('attempting_user_id')
    
    if not user_id or user_id not in VERIFICATION_CODES:
        return redirect(url_for('index'))
    
    code_data = VERIFICATION_CODES[user_id]
    
    if time.time() - code_data['generated_at'] > 900:
        return render_template_string(HTML_PAGE, error="انتهت صلاحية كود التحقق. أعد المحاولة.", step_two=False)
    
    if otp_input == code_data['code']:
        client_ip = request.remote_addr
        
        # حماية ضد مشاركة الحساب
        if APPROVED_USERS[user_id]['current_ip'] and APPROVED_USERS[user_id]['current_ip'] != client_ip:
            protection_bot.send_message(ADMIN_ID, f"🚨 محاولة تسريب أو دخول متعدد!\nالعميل: {user_id} حاول فتح الحساب من جهازين.\nتم حظره تلقائياً لحمايتك.")
            APPROVED_USERS.pop(user_id, None)
            session.clear()
            return render_template_string(HTML_PAGE, error="تم رصد دخول من جهاز آخر. تم قفل حسابك لأسباب أمنية، تواصل مع الدعم.", step_two=False)
        
        APPROVED_USERS[user_id]['expires_at'] = time.time() + 5400  # 90 دقيقة صلاحية الجلسة
        APPROVED_USERS[user_id]['current_ip'] = client_ip
        session['user_id'] = user_id
        return render_template_string(CONTENT_PAGE)
    else:
        return render_template_string(HTML_PAGE, error="كود التحقق غير صحيح!", step_two=True)

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("⚡ S1 Protection Website & Bot is running...")
    protection_bot.infinity_polling()
