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

# 2. الواجهة وتصميم أزرار التحميل
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>متجر N7L | تحميل المودات</title>
    <style>
        body {
            background-color: #0b0c10;
            color: #c5c6c7;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
            padding: 40px 20px;
            margin: 0;
        }
        @media print { body { display: none; } }
        
        .main-title {
            color: #45f3ff;
            font-size: 2.2rem;
            margin-bottom: 5px;
            text-shadow: 0 0 10px rgba(69, 243, 255, 0.3);
        }
        .main-subtitle {
            color: #c5c6c7;
            font-size: 1rem;
            margin-bottom: 40px;
        }

        .section-box {
            max-width: 500px;
            margin: 0 auto 30px auto;
            background-color: #1f2833;
            padding: 25px;
            border-radius: 10px;
            border: 1px solid #1f2833;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
            transition: 0.3s;
        }
        .section-box:hover {
            border-color: #45f3ff;
            box-shadow: 0 0 15px rgba(69, 243, 255, 0.15);
        }
        
        h3 { 
            color: #45f3ff; 
            margin-top: 0;
            margin-bottom: 20px;
            font-size: 1.3rem;
            border-bottom: 1px solid #45f3ff33;
            padding-bottom: 10px;
        }
        
        /* تصميم أزرار التحميل الممتازة */
        .link-card {
            display: block;
            background: #0b0c10;
            color: #45f3ff;
            padding: 14px;
            margin: 12px 0;
            border-radius: 6px;
            text-decoration: none;
            font-weight: bold;
            text-align: center;
            border: 1px solid #0b0c10;
            transition: 0.3s;
        }
        .link-card:hover {
            border-color: #45f3ff;
            background: #1f2833;
            color: #fff;
            box-shadow: 0 0 8px rgba(69, 243, 255, 0.3);
        }

        /* تصميم فورم التحقق والدخول */
        input[type="text"] {
            width: 100%;
            padding: 12px;
            margin: 12px 0;
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
        button:hover { 
            background-color: #1f2833; 
            color: #45f3ff; 
            border: 1px solid #45f3ff; 
        }
        
        .error { color: #ff3333; margin: 15px 0; font-weight: bold; font-size: 14px; }
        .success { color: #00ff00; margin: 15px 0; font-weight: bold; font-size: 14px; }
        p { font-size: 14px; line-height: 1.6; margin: 10px 0; }
        
        .logout-btn {
            display: inline-block;
            margin-top: 15px;
            color: #ff3333;
            text-decoration: none;
            font-size: 13px;
            font-weight: bold;
        }
    </style>
    <script>
        // حماية المحتوى
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

    <h1 class="main-title">🏎️ متجر N7L</h1>
    <p class="main-subtitle">بوابتك الخاصة لتحميل أقوى مودات محاكي الحوادث (BeamNG.drive)</p>

    <!-- صندوق الدخول والتحميل الموحد -->
    <div class="section-box" style="border-color: #45f3ff;">
        <h3>🔒 قسم المودات والروابط الخاصة</h3>
        
        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}

        {% if not logged_in %}
            <!-- واجهة التحقق بالتليجرام -->
            {% if not step_two %}
                <form action="/login_step1" method="POST">
                    <p>أدخل آيدي التليجرام الخاص بك لتلقي رمز التحقق (OTP):</p>
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
            <!-- هنا تظهر أزرار التحميل مباشرة بنفس الترتيب والصورة -->
            <p class="success" style="font-size: 16px;">🎉 تم التحقق بنجاح! حمل المودات الآن:</p>
            
            <a href="https://www.dropbox.com/scl/fi/j4v4ssvcfh18bfiftszof/Optima_2019_KHwylD.zip?rlkey=4xkvmcpac711khtenp60v4ysk&st=0nskr6jk&dl=1" target="_blank" class="link-card">⬇️ تحميل مود اوبتما ٢٠١٩ ( خويلد )</a>
            
            <a href="https://www.dropbox.com/scl/fi/esm2hbzq6ip66obfevcog/Camry_2021_KHwylD.zip?rlkey=upbfz1cy0knmm7maax39joq8w&st=pd4w2rpa&dl=1" target="_blank" class="link-card">⬇️ تحميل مود كامري ٢٠٢١ ( خويلد )</a>
            
            <a href="https://www.dropbox.com/scl/fi/m8mfrvjbdm87cisnp7vxi/Camry_2005_KHwylD.zip?rlkey=6k2xk7adc5oxd1381ysxe1rdy&st=xyxcius1&dl=1" target="_blank" class="link-card">⬇️ تحميل مود كامري ٢٠٠٥ ( خويلد )</a>
            
            <a href="https://www.dropbox.com/scl/fi/j6lnurcqyv0fj8vc81cnw/Cruze_2017_KHwylD.zip?rlkey=9uvvcst8pxqpzowmx9p93t76m&st=ah4d77gs&dl=1" target="_blank" class="link-card">⬇️ تحميل مود كروز ٢٠١٧ ( خويلد )</a>
            
            <a href="https://www.dropbox.com/scl/fi/km3j5tw8bnt99ebngvqum/Ddsn_2016_KHwylD.zip?rlkey=r4kg0mln6s8cwhj5vhun4mayx&st=nlloh4cl&dl=1" target="_blank" class="link-card">⬇️ تحميل مود ددسن ٢٠١٦ ( خويلد )</a>
            
            <a href="https://www.dropbox.com/scl/fi/12jvs85pq3mx58mxhdwqr/Hilux_2011_KHwylD-2.zip?rlkey=n1oyx9498iry5sffe40lauj1l&st=qi1alrmb&dl=1" target="_blank" class="link-card">⬇️ تحميل مود هايلكس ٢٠١١ ( خويلد )</a>
            
            <a href="https://www.dropbox.com/scl/fi/v0adyryue04uzo06b980n/Caprice_2013_KHwylD.zip?rlkey=u5ugflyib2dl2f3pzswr1vp6g&st=g3rj4dvc&dl=1" target="_blank" class="link-card">⬇️ تحميل مود كابرس ٢٠١٣ ( خويلد )</a>
            
            <a href="https://www.dropbox.com/scl/fi/k5ufh18eaezsoxiqbqyx0/Hyundai_Sonata_2024_KHwylD.zip?rlkey=7toa2wa4kyjo86qonukbuffdt&st=2ha3kmbi&dl=1" target="_blank" class="link-card">⬇️ تحميل مود موستنق ٢٠١٣ ( خويلد )</a>
            
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
