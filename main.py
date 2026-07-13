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
app.secret_key = os.urandom(24) # تأمين الجلسات بمفتاح تشفير قوي يمنع التلاعب

# قائمة المشتركين المعتمدين رسمياً (فقط آيديك أنت مضاف هنا حالياً)
# مستقبلاً لما يشتري عميل جديد، تضيف الآيدي حقه في هذه القائمة يدوياً أو برمجياً
APPROVED_USERS = {
    5432340735: {'expires_at': time.time() + 86400 * 30, 'current_ip': None}
}

# لتخزين أكواد الـ OTP الصالحة لكل آيدي
VERIFICATION_CODES = {} 

# تفعيل بوت الحماية (البوت فقط يرحب بالعميل المعتمد، ولا يضيفه تلقائياً لقائمة المشترين)
@protection_bot.message_handler(commands=['start'])
def welcome_protection(message):
    user_id = message.from_user.id
    if user_id in APPROVED_USERS:
        protection_bot.reply_to(message, f"🔒 أهلاً بك في بوت حماية متجر N7L.\n\nحسابك معتمد ومسجل لدينا.\nآيدي حسابك هو: `{user_id}`\n\nيمكنك الآن استخدامه للدخول للموقع الآمن.")
    else:
        protection_bot.reply_to(message, f"❌ أهلاً بك في بوت حماية متجر N7L.\n\nحسابك غير مسجل في النظام حتى الآن.\nلشراء اشتراك، يرجى التواصل مع الإدارة.")

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
        @media print { body { display: none; } }
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
        document.addEventListener('contextmenu', event => event.preventDefault());
        document.addEventListener('keydown', function(e) {
            if (e.key === "PrintScreen" || 
                (e.ctrlKey && e.shiftKey && e.key === "I") || 
                (e.ctrlKey && e.shiftKey && e.key === "C") || 
                (e.ctrlKey && e.key === "u") || 
                (e.metaKey && e.shiftKey && e.key === "4")) {
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
            <!-- الخطوة الأولى: إدخال الآيدي -->
            <form method="POST" action="/login_step1">
                <label>أدخل آيدي التليجرام الخاص بك المعتمد:</label>
                <input type="text" name="user_id" required placeholder="مثال: 5432340735">
                <button type="submit">إرسال كود التحقق 💬</button>
            </form>
        {% else %}
            <!-- الخطوة الثانية: إدخال كود OTP -->
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

# 3. صفحة عرض المودات والروابط المحمية
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
        
        <!-- روابط قنوات المودات المخفية حقتك -->
        <a href="https://t.me/+tPBT1R66qx43NGQ0" target="_blank">🔗 رابط المجموعة الأساسية</a>
        <a href="https://t.me/+Ha82GPmaPJ05Yzg0" target="_blank">🔗 رابط مودات محاكي الحوادث</a>
    </div>
</body>
</html>
"""

# 4. منطق عمل السيرفر والتحقق الصارم من الجلسات والـ IP والـ OTP
@app.route('/')
def index():
    if 'user_id' in session:
        user_id = session['user_id']
        if user_id in APPROVED_USERS and time.time() < APPROVED_USERS[user_id]['expires_at']:
            if APPROVED_USERS[user_id]['current_ip'] == request.remote_addr:
                return render_template_string(CONTENT_PAGE)
    # تنظيف الجلسات عند العودة للرئيسية دون صلاحيات
    session.clear()
    return render_template_string(HTML_PAGE, error=None, step_two=False)

@app.route('/login_step1', methods=['POST'])
def login_step1():
    user_id_str = request.form.get('user_id')
    if not user_id_str.isdigit():
        return render_template_string(HTML_PAGE, error="❌ الآيدي يجب أن يتكون من أرقام فقط.", step_two=False)
    
    user_id = int(user_id_str)
    
    # تحقق صارم: هل الآيدي معتمد وموجود في APPROVED_USERS؟
    if user_id not in APPROVED_USERS:
        return render_template_string(HTML_PAGE, error="❌ هذا الآيدي غير مسجل في النظام. تواصل مع الإدارة لتفعيل حسابك.", step_two=False)
    
    # توليد كود OTP مكون من 6 أرقام بشكل عشوائي تماماً
    otp = str(random.randint(100000, 999999))
    VERIFICATION_CODES[user_id] = {'code': otp, 'generated_at': time.time()}
    
    try:
        # إرسال الكود للعميل المعتمد عبر بوت الحماية
        protection_bot.send_message(user_id, f"🔒 كود التحقق لدخول موقع s1 هو:\n\n`{otp}`\n\n🕒 صالح للاستخدام لمدة 15 دقيقة فقط.")
        session['attempting_user_id'] = user_id
        return render_template_string(HTML_PAGE, error=None, step_two=True)
    except Exception:
        return render_template_string(HTML_PAGE, error="❌ فشل إرسال الكود. تأكد من أنك قمت بالدخول على بوت الحماية والضغط على /start أولاً.", step_two=False)

@app.route('/login_step2', methods=['POST'])
def login_step2():
    otp_input = request.form.get('otp_code')
    user_id = session.get('attempting_user_id')
    
    if not user_id or user_id not in VERIFICATION_CODES:
        return render_template_string(HTML_PAGE, error="❌ حدث خطأ في الجلسة. أعد إدخال الآيدي.", step_two=False)
    
    code_data = VERIFICATION_CODES[user_id]
    
    # 1. التحقق من صلاحية الوقت (15 دقيقة)
    if time.time() - code_data['generated_at'] > 900:
        VERIFICATION_CODES.pop(user_id, None)
        return render_template_string(HTML_PAGE, error="❌ انتهت صلاحية كود التحقق. أعد المحاولة.", step_two=False)
    
    # 2. التحقق الصارم من تطابق الكود (منع الدخول العشوائي تماماً)
    if otp_input != code_data['code']:
        return render_template_string(HTML_PAGE, error="❌ كود التحقق غير صحيح! يرجى إعادة التأكد.", step_two=True)
    
    # إذا كان الكود صحيحاً:
    client_ip = request.remote_addr
    
    # حماية ضد مشاركة الحساب (IP مختلفة)
    if APPROVED_USERS[user_id]['current_ip'] and APPROVED_USERS[user_id]['current_ip'] != client_ip:
        protection_bot.send_message(ADMIN_ID, f"🚨 محاولة تسريب أو دخول متعدد!\nالعميل: {user_id} حاول فتح الحساب من جهاز آخر.\nتم حظره تلقائياً لحمايتك.")
        APPROVED_USERS.pop(user_id, None)
        VERIFICATION_CODES.pop(user_id, None)
        session.clear()
        return render_template_string(HTML_PAGE, error="❌ تم رصد دخول من جهاز آخر. تم قفل حسابك لأسباب أمنية.", step_two=False)
    
    # تفعيل الجلسة للعميل بنجاح
    APPROVED_USERS[user_id]['expires_at'] = time.time() + 5400  # 90 دقيقة
    APPROVED_USERS[user_id]['current_ip'] = client_ip
    session['user_id'] = user_id
    
    # حذف الكود بعد الاستخدام مباشرة لضمان عدم استخدامه مرة أخرى
    VERIFICATION_CODES.pop(user_id, None)
    
    return render_template_string(CONTENT_PAGE)

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("⚡ S1 Protection Website & Bot is running...")
    protection_bot.infinity_polling()
