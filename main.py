import os
import time
import random
import threading
from flask import Flask, request, session, render_template_string, redirect, url_for
import telebot

# 1. إعداد البوت والتوكن الخاص بك (تم استعادته بالكامل ليعمل بنجاح)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8346972966:AAGJpcm8XOroKT4VE-o38Ky4JEHXIsb1-k")
protection_bot = telebot.TeleBot(BOT_TOKEN)

# آيدي الحساب المسؤول الخاص بك
ADMIN_ID = 5432340735 

app = Flask(__name__)
app.secret_key = os.urandom(24) # تأمين الجلسات بمفتاح تشفير قوي يمنع التلاعب بالـ Cookies

# قائمة المشتركين المعتمدين رسمياً (آيديك مضاف تلقائياً مع صلاحية 30 يوم)
APPROVED_USERS = {
    5432340735: {
        'expires_at': time.time() + 86400 * 30, 
        'current_ip': None
    }
}

# لتخزين أكواد الـ OTP المؤقتة لكل آيدي
VERIFICATION_CODES = {}

# 2. تصميم صفحة التحقق s1 (مع حظر تصوير الشاشة، النسخ، الـ DevTools، والطباعة)
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
        @media print { body { display: none; } } /* إخفاء الصفحة عند محاولة الحفظ كـ PDF أو الطباعة */
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
    </style>
    <script>
        // تعطيل الزر الأيمن للماوس وعناصر فحص الصفحة DevTools حماية للأكواد
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

        {% if not step_two %}
            <!-- الخطوة الأولى: إدخال الآيدي -->
            <form action="/login_step1" method="POST">
                <p>أدخل آيدي التليجرام الخاص بك لتلقي رمز التحقق (OTP)</p>
                <input type="text" name="user_id" placeholder="مثال: 5432340735" required autocomplete="off">
                <button type="submit">إرسال كود التحقق</button>
            </form>
        {% else %}
            <!-- الخطوة الثانية: إدخال الرمز المرسل للبوت -->
            <form action="/login_step2" method="POST">
                <p class="success">📩 أرسلنا كود التحقق إلى حسابك في تليجرام.</p>
                <input type="text" name="otp_code" placeholder="أدخل كود التحقق (OTP)" required autocomplete="off">
                <button type="submit">تأكيد ودخول</button>
            </form>
        {% endif %}
    </div>
</body>
</html>
"""

# 3. صفحة عرض المودات والروابط المحمية بعد التحقق بنجاح
CONTENT_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>منطقة الأعضاء | متجر N7L</title>
    <style>
        body {
            background-color: #0b0c10;
            color: #c5c6c7;
            font-family: 'Segoe UI', sans-serif;
            text-align: center;
            padding: 50px 20px;
        }
        @media print { body { display: none; } }
        .container {
            max-width: 500px;
            margin: 0 auto;
            background-color: #1f2833;
            padding: 40px;
            border-radius: 10px;
            border: 1px solid #45f3ff;
            box-shadow: 0 0 15px rgba(69, 243, 255, 0.3);
        }
        h1 { color: #45f3ff; margin-bottom: 20px; }
        p { font-size: 16px; margin-bottom: 30px; }
        .link-card {
            display: block;
            background: #0b0c10;
            color: #45f3ff;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
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
            margin-top: 30px;
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
        <h1>🎉 أهلاً بك في المنطقة الخاصة</h1>
        <p>جلسة دخولك نشطة الآن لمدة 90 دقيقة فقط على هذا الجهاز.</p>
        <hr style="border: 1px solid #333; margin: 20px 0;">
        
        <!-- روابط قنوات المودات المخفية حقتك -->
        <a href="https://t.me/+tPBT1R66qx43NGQ0" target="_blank" class="link-card">🔗 رابط المجموعة الأساسية</a>
        <a href="https://t.me/+Ha82GPmaPJ05Yzg0" target="_blank" class="link-card">🔗 رابط مودات محاكي الحوادث</a>
        
        <a href="/logout" class="logout-btn">تسجيل الخروج الآمن 🔓</a>
    </div>
</body>
</html>
"""

# ==================== استقبال رسائل بوت الحماية ====================
@protection_bot.message_handler(commands=['start'])
def welcome_protection(message):
    user_id = message.from_user.id
    
    # تفعيل بوت الحماية (البوت فقط يرحب بالعميل المعتمد، ولا يضيفه تلقائياً لقائمة المشتركين)
    if user_id in APPROVED_USERS:
        protection_bot.reply_to(message, 
            f"🔒 أهلاً بك في بوت حماية متجر N7L.\n\n"
            f"حسابك معتمد ومسجل لدينا.\n"
            f"آيدي حسابك هو:\n`{user_id}`\n\n"
            f"يمكنك الآن استخدامه للدخول للموقع الآمن."
        )
    else:
        protection_bot.reply_to(message, 
            f"❌ أهلاً بك في بوت حماية متجر N7L.\n\n"
            f"حسابك غير مسجل في النظام حتى الآن.\n"
            f"لشراء اشتراك، يرجى التواصل مع الإدارة."
        )

# ==================== مسارات Flask (الموقع الإلكتروني) ====================
@app.route('/')
def index():
    user_id = session.get('user_id')
    if user_id in APPROVED_USERS:
        # التحقق من صلاحية وقت الجلسة والآيبي لمنع مشاركة الرابط
        if time.time() < APPROVED_USERS[user_id]['expires_at'] and APPROVED_USERS[user_id]['current_ip'] == request.remote_addr:
            return render_template_string(CONTENT_PAGE)
            
    # تنظيف الجلسات القديمة أو منتهية الصلاحية
    session.clear()
    return render_template_string(HTML_PAGE, error=None, step_two=False)

@app.route('/login_step1', methods=['POST'])
def login_step1():
    user_id_str = request.form.get('user_id')
    
    if not user_id_str or not user_id_str.isdigit():
        return render_template_string(HTML_PAGE, error="❌ الآيدي يجب أن يتكون من أرقام فقط.", step_two=False)
        
    user_id = int(user_id_str)
    
    # تحقق صارم: هل الآيدي موجود في APPROVED_USERS؟
    if user_id not in APPROVED_USERS:
        return render_template_string(HTML_PAGE, error="❌ هذا الآيدي غير مسجل في النظام. تواصل مع الإدارة لتفعيل حسابك.", step_two=False)
        
    # توليد كود OTP من 6 أرقام بشكل عشوائي تماماً
    otp = str(random.randint(100000, 999999))
    VERIFICATION_CODES[user_id] = {
        'code': otp,
        'generated_at': time.time()
    }
    
    try:
        # إرسال الكود للعميل عبر بوت الحماية المعتمد
        protection_bot.send_message(
            user_id, 
            f"🔒 كود التحقق لدخول موقع s1 هو:\n\n"
            f"`{otp}`\n\n"
            f"⏰ صالح للاستخدام لمدة 15 دقيقة فقط."
        )
        session['attempting_user_id'] = user_id
        return render_template_string(HTML_PAGE, error=None, step_two=True)
    except Exception:
        return render_template_string(
            HTML_PAGE, 
            error="❌ فشل إرسال الكود. تأكد من أنك قمت بالدخول على بوت الحماية والضغط على /start أولاً لكي يستطيع مراسلتك.", 
            step_two=False
        )

@app.route('/login_step2', methods=['POST'])
def login_step2():
    otp_input = request.form.get('otp_code')
    user_id = session.get('attempting_user_id')
    
    if not user_id or user_id not in VERIFICATION_CODES:
        return render_template_string(HTML_PAGE, error="❌ حدث خطأ في الجلسة. أعد إدخال الآيدي.", step_two=False)
        
    code_data = VERIFICATION_CODES[user_id]
    
    # التحقق من صلاحية وقت الكود (15 دقيقة = 900 ثانية)
    if time.time() - code_data['generated_at'] > 900:
        VERIFICATION_CODES.pop(user_id, None)
        return render_template_string(HTML_PAGE, error="❌ انتهت صلاحية كود التحقق. أعد المحاولة.", step_two=False)
        
    if otp_input == code_data['code']:
        client_ip = request.remote_addr
        
        # حماية ضد مشاركة الحساب وتغيير الأجهزة في نفس الوقت
        if APPROVED_USERS[user_id]['current_ip'] and APPROVED_USERS[user_id]['current_ip'] != client_ip:
            try:
                # إرسال بلاغ فوري للأدمن بوجود تسريب
                protection_bot.send_message(
                    ADMIN_ID, 
                    f"🚨 *محاولة تسريب أو دخول متعدد!*\n\n"
                    f"العميل: `{user_id}` حاول فتح الحساب من جهاز آخر.\n"
                    f"تم حظره وتصفير جلسته حمايةً لروابطك."
                )
            except Exception:
                pass
            
            APPROVED_USERS[user_id]['current_ip'] = None # إعادة تعيين الآي بي لإجبارهم على تسجيل جديد
            session.clear()
            return render_template_string(
                HTML_PAGE, 
                error="❌ تم رصد دخول من جهاز آخر. تم قفل حسابك لأسباب أمنية، تواصل مع الدعم.", 
                step_two=False
            )
            
        # تحديث صلاحية الجلسة إلى 90 دقيقة (5400 ثانية) وتثبيت آي بي العميل الحلي
        APPROVED_USERS[user_id]['expires_at'] = time.time() + 5400
        APPROVED_USERS[user_id]['current_ip'] = client_ip
        session['user_id'] = user_id
        
        # مسح كود التحقق لعدم إعادة استخدامه
        VERIFICATION_CODES.pop(user_id, None)
        return render_template_string(CONTENT_PAGE)
    else:
        return render_template_string(HTML_PAGE, error="❌ كود التحقق غير صحيح. أعد المحاولة.", step_two=True)

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id in APPROVED_USERS:
        APPROVED_USERS[user_id]['current_ip'] = None # مسح الآي بي عند تسجيل الخروج يدوياً ليتسنى له الدخول بجهاز أخر لاحقاً
    session.clear()
    return redirect(url_for('index'))

# ==================== تشغيل السيرفر والبوت بطريقة متوافقة مع Render ====================
def run_bot():
    print("⚡ Starting Telegram Bot...")
    try:
        protection_bot.infinity_polling()
    except Exception as e:
        print(f"❌ Bot error: {e}")

if __name__ == "__main__":
    # 1. تشغيل بوت التليجرام في الخلفية (Daemon Thread) لتجنب تعليق Render
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # 2. تشغيل سيرفر الـ Flask كعملية رئيسية ليستمع للـ Port المطلوب من Render بنجاح
    print("⚡ Starting Flask Web Server...")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
