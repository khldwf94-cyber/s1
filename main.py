import os, time, random
from flask import Flask, request, session, render_template_string, redirect, url_for
import telebot

# --- إعدادات البوت ---
BOT_TOKEN = "8346972966:AAGJpcm8XOroKT4VE-o38Ky4JEHXILsb1-k"
protection_bot = telebot.TeleBot(BOT_TOKEN)
ADMIN_ID = 5432340735
app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- قائمة المودات (أضف روابطك هنا) ---
MODS_LIST = [
    {"name": "اوبتما ٢٠١٩", "url": "https://www.dropbox.com/scl/fi/xxxxxxxx"},
    {"name": "سيارة شرطة", "url": "https://www.dropbox.com/scl/fi/xxxxxxxx"},
    # أضف باقي الـ 200 رابط بنفس هذا التنسيق
]

# --- واجهة الموقع مع الحماية المدمجة ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>N7L STORE | Secure Access</title>
    <style>
        body { background: #0b0c10; color: #c5c6c7; font-family: sans-serif; padding: 20px; user-select: none; -webkit-user-select: none; }
        .container { max-width: 600px; margin: auto; background: #151a21; padding: 25px; border-radius: 8px; border: 1px solid #1f2833; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .search-box { width: 100%; padding: 12px; margin-bottom: 20px; background: #0d1117; border: 1px solid #30363d; color: white; border-radius: 6px; box-sizing: border-box; }
        .list-item { padding: 12px; border-bottom: 1px solid #2d3748; }
        .list-item a { color: #58a6ff; text-decoration: none; font-weight: bold; cursor: pointer; }
        input[type="text"], button { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; border: 1px solid #30363d; background: #0d1117; color: white; }
        button { background: #238636; cursor: pointer; border: 1px solid #2ea44f; }
    </style>
    <script>
        document.addEventListener('contextmenu', e => e.preventDefault());
        document.addEventListener('copy', e => e.preventDefault());
        document.addEventListener('keydown', e => {
            if (e.ctrlKey && (e.key === 'c' || e.key === 'u' || e.key === 's' || e.key === 'p')) e.preventDefault();
        });
        document.addEventListener("visibilitychange", () => {
            document.body.style.display = document.hidden ? "none" : "block";
        });
        function filterList() {
            let input = document.getElementById('search').value.toLowerCase();
            let items = document.getElementsByClassName('list-item');
            for (let i = 0; i < items.length; i++) {
                items[i].style.display = items[i].innerText.toLowerCase().includes(input) ? "" : "none";
            }
        }
    </script>
</head>
<body>
    <div class="container">
        {% if not logged_in %}
            <h2>N7L STORE | تسجيل الدخول</h2>
            <form action="/login_step1" method="POST">
                <input type="text" name="user_id" placeholder="أدخل آيدي التليجرام" required>
                <button type="submit">إرسال كود التحقق</button>
            </form>
        {% else %}
            <h3>قائمة المودات المتاحة</h3>
            <input type="text" id="search" class="search-box" onkeyup="filterList()" placeholder="🔍 ابحث عن مود...">
            <div id="modsList">
                {% for mod in mods %}
                    <div class="list-item"><a href="{{ mod.url }}" target="_blank">{{ mod.name }}</a></div>
                {% endfor %}
            </div>
            <a href="/logout" style="color: #ff7b72; display:block; margin-top:20px; text-align:center;">[ خروج آمن ]</a>
        {% endif %}
    </div>
</body>
</html>
"""

# --- المسارات البرمجية ---
@app.route('/')
def index():
    logged_in = session.get('logged_in', False)
    return render_template_string(HTML_PAGE, logged_in=logged_in, mods=MODS_LIST)

@app.route('/login_step1', methods=['POST'])
def login_step1():
    session['logged_in'] = True
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
