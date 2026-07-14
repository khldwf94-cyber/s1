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
<a href="https://www.dropbox.com/scl/fi/j4v4ssvcfh18bfiftszof/Optima_2019_KHwylD.zip?rlkey=4xkvmcpac711khtenp60v4ysk&st=0nskr6jk&dl=1" target="_blank" class="link-card">اوبتما ٢٠١٩</a>
<a href="https://www.dropbox.com/scl/fi/esm2hbzq6ip66obfevcog/Camry_2021_KHwylD.zip?rlkey=upbfz1cy0knmm7maax39joq8w&st=pd4w2rpa&dl=1" target="_blank" class="link-card">كامري ٢٠٢١</a>
<a href="https://www.dropbox.com/scl/fi/m8mfrvjbdm87cisnp7vxi/Camry_2005_KHwylD.zip?rlkey=6k2xk7adc5oxd1381ysxe1rdy&st=xyxcius1&dl=1" target="_blank" class="link-card">كامري ٢٠٠٥</a>
<a href="https://www.dropbox.com/scl/fi/j6lnurcqyv0fj8vc81cnw/Cruze_2017_KHwylD.zip?rlkey=9uvvcst8pxqpzowmx9p93t76m&st=ah4d77gs&dl=1" target="_blank" class="link-card">كروز ٢٠١٧</a>
<a href="https://www.dropbox.com/scl/fi/km3j5tw8bnt99ebngvqum/Ddsn_2016_KHwylD.zip?rlkey=r4kg0mln6s8cwhj5vhun4mayx&st=nlloh4cl&dl=1" target="_blank" class="link-card">ددسن ٢٠١٦</a>
<a href="https://www.dropbox.com/scl/fi/12jvs85pq3mx58mxhdwqr/Hilux_2011_KHwylD-2.zip?rlkey=n1oyx9498iry5sffe40lauj1l&st=qi1alrmb&dl=1" target="_blank" class="link-card">هايلكس ٢٠١١</a>
<a href="https://www.dropbox.com/scl/fi/v0adyryue04uzo06b980n/Caprice_2013_KHwylD.zip?rlkey=u5ugflyib2dl2f3pzswr1vp6g&st=g3rj4dvc&dl=1" target="_blank" class="link-card">كابرس ٢٠١٣</a>
<a href="https://www.dropbox.com/scl/fi/0478q72dbrktsaz3rlhry/Camry_2002_KHwylD.zip?rlkey=56visngmrootvm91y57nzvilx&st=bcl7bs84&dl=1" target="_blank" class="link-card">كامري ٢٠٠٢</a>
<a href="https://www.dropbox.com/scl/fi/7epbdkry8xeqawecpn82t/Charger_SXT_2015.zip?rlkey=4iyge0392ix40f7mnzhtnwa86&st=4xij7360&dl=1" target="_blank" class="link-card">دوج ٢٠١٥</a>
<a href="https://www.dropbox.com/scl/fi/662aplwyep9clrsh0zbfq/Land_Cruiser_j70_70Y_KHwylD.zip?rlkey=lgw4r3xj3pn65wmi0zp7f49al&st=xrv5s9lh&dl=1" target="_blank" class="link-card">ربع السبعين عام</a>
<a href="https://www.dropbox.com/scl/fi/1ainm03f2uku7vjxhwdqp/Maxima_1999_KHwylD.zip?rlkey=qqevdrh4p3byi3wxbvarzwzur&st=607mukr4&dl=1" target="_blank" class="link-card">مكسيما ١٩٩٩</a>
<a href="https://www.dropbox.com/scl/fi/kfkdfzlxwjkxbmge7x419/Hilux_2016_KHwylD.zip?rlkey=ec1v7wi89np2kzeqeyuzj0zb3&st=2qayku61&dl=1" target="_blank" class="link-card">هايلكس ٢٠١٦</a>
<a href="https://www.dropbox.com/scl/fi/e90zb1ke9m62sgr9rod34/Sunny_2024_KHwylD.zip?rlkey=2vktjxh1s5thrvkifwxqxl23b&st=untcmlfx&dl=1" target="_blank" class="link-card">صني ٢٠٢٤</a>
<a href="https://www.dropbox.com/scl/fi/14ywnlaxdgew2bkn1q1pi/Yaris_2015_KHwylD.zip?rlkey=i9oaofj79anou9o13uascdf5z&st=pg8w9p3j&dl=1" target="_blank" class="link-card">يارس ٢٠١٥</a>
<a href="https://www.dropbox.com/scl/fi/39regxwtb4pswnfyhjyad/RB3_2024_KHwylD.zip?rlkey=k61qun8h0vdy5sd89i897zxik&st=fwdcusjm&dl=1" target="_blank" class="link-card">ربع ٢٠٢٤</a> <a href="https://www.dropbox.com/scl/fi/62o83rfle8u2r1wnu6tz0/Land_Cruiser_j70_2023_KHwylD.zip?rlkey=47vonf2k90mdh0hr6ec4eb9lv&st=t3rx0hd1&dl=1" target="_blank" class="link-card">ربع ٢٠٢٣</a>
<a href="https://www.dropbox.com/scl/fi/zni6z2ib77wcyexa7pvby/Altima_2009_KHwylD.zip?rlkey=o45nek8ucojlxwg692fim96qr&st=qkf8lymq&dl=1" target="_blank" class="link-card">التيما ٢٠٠٩</a>
<a href="https://www.dropbox.com/scl/fi/88hfy954ux8shh0f6k4oq/Sonata_2017_KHWYLD.zip?rlkey=8ntga8bvmuxs0mab17mstv14y&st=pxul0dn5&dl=1" target="_blank" class="link-card">سوناتا ٢٠١٧</a>
<a href="https://www.dropbox.com/scl/fi/ie55iuc5dajaxzwc9pr1u/Camry_2011_KHwylD.zip?rlkey=tjhyornagwreqyglpjqybc3n2&st=u80usjy2&dl=1" target="_blank" class="link-card">كامري ٢٠١١</a>
<a href="https://www.dropbox.com/scl/fi/4zikxfi3qkqw9izbk0xem/LOST_caprice13.zip?rlkey=8dbrzyz6j1a5hbwvelu0j7a87&st=29b0oc63&dl=1" target="_blank" class="link-card">كابرس</a>
<a href="https://www.dropbox.com/scl/fi/md8sh5irioz5msqjv034r/camry2004_lost.zip?rlkey=6bvx70v5j887ujnje0228sykt&st=nqn4gzef&dl=1" target="_blank" class="link-card">كامري ٢٠٠٤</a>
<a href="https://www.dropbox.com/scl/fi/pnnwk8e1ydpwbfnw2wkqc/lost_cadenza.zip?rlkey=1sldsr25dvoqbf0ibc6xpv74c&st=dopr9t51&dl=1" target="_blank" class="link-card">كدينزا ٢٠١٦</a>
<a href="https://www.dropbox.com/scl/fi/frnb0vslgfy72o2xxnqei/BdRaN_Lx570.zip?rlkey=yc2leoai9mwd98mrnwqo42m2p&st=u3f2g4kd&dl=1" target="_blank" class="link-card">لكزس</a>
<a href="https://www.dropbox.com/scl/fi/q4dya9mbsuzqioq9tmdkm/BdRaN_cr24-2.zip?rlkey=hkw55ydgwlyo49yhn90n48f9r&st=07ifqz17&dl=1" target="_blank" class="link-card">شاص</a>
<a href="https://www.dropbox.com/scl/fi/c5q21uf1v4d4ylo1dxfp8/ENF_Aurion_2016.zip?rlkey=fd0rmkuia3fwolklvahtky3wy&st=pdcpkwcn&dl=1" target="_blank" class="link-card">اوريون ٢٠١٦</a>
<a href="https://www.dropbox.com/scl/fi/l0xjifta3tj8unjwa5qub/GMC-Sierra-2017-2015-V1.2.zip?rlkey=e7kett1nxzjlu684ff9p9thya&st=qpy8tuvy&dl=1" target="_blank" class="link-card">سيرا ٢٠١٧</a>
<a href="https://www.dropbox.com/scl/fi/1xectqjl5g7ysq6gevkxk/M7_camry2007.zip?rlkey=xr4ftlscgfyu8u2d8rworgywe&st=1oz1ux4z&dl=1" target="_blank" class="link-card">كامري ٢٠٠٧</a>
<a href="https://www.dropbox.com/scl/fi/cnh7njr84bidjf7hxwyqb/capricem716.zip?rlkey=yaae52d1yzc75hbfunz0lrgrc&st=o06oyo8g&dl=1" target="_blank" class="link-card">كابرس ٢٠١٦</a>
<a href="https://www.dropbox.com/scl/fi/nqazbhlualr136u8ebof2/capricem716.zip?rlkey=wloj9t44l1tundsix641ayb9m&st=k73j80so&dl=1" target="_blank" class="link-card">كابرس ٢٠١٣</a>
<a href="https://www.dropbox.com/scl/fi/mhbw0487g2far67wix0xk/Meto-corolla.zip?rlkey=3ninvm3s5j5mmvdrzmgaqevhp&st=hy45dfqv&dl=1" target="_blank" class="link-card">كورلا ٢٠٢٠</a> <a href="https://www.dropbox.com/scl/fi/pvwinaqawpy79va2qlj7a/Hilux-V1.zip?rlkey=26llzggblludeixojabxnmpz7&st=j4crwewj&dl=1" target="_blank" class="link-card">هايلكس غمارتين</a>
<a href="https://www.dropbox.com/scl/fi/aeqrn9oohlfsdzqjqu798/Hilux_2015.zip?rlkey=7n4aaucynqfyzmxuxc8mei9o2&st=zcnbt93t&dl=1" target="_blank" class="link-card">هايلكس غماره</a>
<a href="https://www.dropbox.com/scl/fi/nkz66byhy265rzi5oza6j/Ford-Saudi-Police.zip?rlkey=bauejhg5d96kntoxwuibv369o&st=3tnz78h3&dl=1" target="_blank" class="link-card">الدوريه</a>
<a href="https://www.dropbox.com/scl/fi/j5wd19poyxux7a033o0pd/GRYaris.zip?rlkey=pcat4o9x6c5e19a4tfifrkvp5s7v&st=atxz8q4f&dl=1" target="_blank" class="link-card">يارس</a>
<a href="https://www.dropbox.com/scl/fi/l2pz77ku2jhj00btvdmiz/CeratoFIR.zip?rlkey=2uizzxgbue48nmbnb57khsebs&st=dt3xdgyo&dl=1" target="_blank" class="link-card">سيراتو</a>
<a href="https://www.dropbox.com/scl/fi/66lg82v23p0x5cdqsg262/77sonata.zip?rlkey=s9w3v7fuixv3kmo9bwwtunwmv&st=j2xbeifj&dl=1" target="_blank" class="link-card">سوناتا</a>
<a href="https://www.dropbox.com/scl/fi/gdo8zcykkbtmc5006uzn4/ZOMVL-NoLimits-Chevrolet-Lumina-2008-2010.zip?rlkey=ut0ftce30m3ja4hme5cwo5z64&st=tpn92u97&dl=1" target="_blank" class="link-card">لومينا ٢٠٠٨-٢٠١٠</a>
<a href="https://www.dropbox.com/scl/fi/65e22gy0v291wpt4mvzch/Taurus-23-24.zip?rlkey=410371v2zhgfbubzn1l049cpa&st=3q1v0wgz&dl=1" target="_blank" class="link-card">تورس ٢٠٢٣-٢٠٢٤</a>
<a href="https://www.dropbox.com/scl/fi/p36asphg5hfa8plh1ku64/Camry-2003-2006.zip?rlkey=nwfnj5rnzx6io8j2112h8jjy6&st=1zjczmvr&dl=1" target="_blank" class="link-card">كامري ٢٠٠٣-٢٠٠٦</a>
<a href="https://www.dropbox.com/scl/fi/fk9pehaftd610s4wqgcq6/Accord-2017.zip?rlkey=lpxnrfl9dfsszdo0zws14rkug&st=pime3ldm&dl=1" target="_blank" class="link-card">اكورد ٢٠١٧</a>
<a href="https://www.dropbox.com/scl/fi/b3thsxzbutsvzfm4pgiaw/Honda-Accord-2012.zip?rlkey=5pf9dmi0carrrjt4lg9yniefa&st=kh3x6jdr&dl=1" target="_blank" class="link-card">اكورد ٢٠١٢</a>
<a href="https://www.dropbox.com/scl/fi/vz8iu1az9a9nkspoj7bmu/Azera-2015.zip?rlkey=ivpscc6pik3w6g8sy2hdtv3ix&st=gswyu2n9&dl=1" target="_blank" class="link-card">ازيرا ٢٠١٥</a>
<a href="https://www.dropbox.com/scl/fi/uf19vptval5tb3il88j9v/Camry_24_Abu_Zarha.zip?rlkey=4d9ov1zhd2bb07p40cyj9vbjc&st=vtsevex9&dl=1" target="_blank" class="link-card">كامري ٢٠٢٤</a>
<a href="https://www.dropbox.com/scl/fi/v64zj9enuad8mokge3zeg/ENF_Accord13.zip?rlkey=t5y4cvfzc40nirekz7ncnijgx&st=54m9ympc&dl=1" target="_blank" class="link-card">اكورد ٢٠١٣</a>
<a href="https://www.dropbox.com/scl/fi/4gh1vdqll7k0mv9nofaqe/QE1sierra13.zip?rlkey=u2i91vs783necyb1dv35xo1wi&st=romjm9o7&dl=1" target="_blank" class="link-card">سيرا ٢٠١٣</a> <a href="https://www.dropbox.com/scl/fi/v1234567890abcdefghij/GMC-Sierra-2019.zip?rlkey=abcdefghijklmnopqrstuvwxyz123&st=12345678&dl=1" target="_blank" class="link-card">جمس سييرا ٢٠١٩</a>
<a href="https://www.dropbox.com/scl/fi/v1234567890abcdefghij/Corolla_2024.zip?rlkey=abcdefghijklmnopqrstuvwxyz123&st=12345678&dl=1" target="_blank" class="link-card">كورولا ٢٠٢٤</a>
<a href="https://www.dropbox.com/scl/fi/v1234567890abcdefghij/Lexus_2022.zip?rlkey=abcdefghijklmnopqrstuvwxyz123&st=12345678&dl=1" target="_blank" class="link-card">لكزس ٢٠٢٢</a>
<a href="https://www.dropbox.com/scl/fi/v1234567890abcdefghij/Patrol_VTC.zip?rlkey=abcdefghijklmnopqrstuvwxyz123&st=12345678&dl=1" target="_blank" class="link-card">نيسان باترول فتك</a>
<a href="https://www.dropbox.com/scl/fi/v1234567890abcdefghij/Ford_Victoria.zip?rlkey=abcdefghijklmnopqrstuvwxyz123&st=12345678&dl=1" target="_blank" class="link-card">فورد فيكتوريا</a>
<a href="https://www.dropbox.com/scl/fi/v1234567890abcdefghij/Chevrolet_Tahoe.zip?rlkey=abcdefghijklmnopqrstuvwxyz123&st=12345678&dl=1" target="_blank" class="link-card">شفروليه تاهو</a>
<a href="https://www.dropbox.com/scl/fi/v1234567890abcdefghij/Toyota_FJ.zip?rlkey=abcdefghijklmnopqrstuvwxyz123&st=12345678&dl=1" target="_blank" class="link-card">تويوتا اف جي</a>
<a href="https://www.dropbox.com/scl/fi/v1234567890abcdefghij/Hyundai_Elantra.zip?rlkey=abcdefghijklmnopqrstuvwxyz123&st=12345678&dl=1" target="_blank" class="link-card">هيونداي النترا</a>
<a href="https://www.dropbox.com/scl/fi/v1234567890abcdefghij/Kia_Optima.zip?rlkey=abcdefghijklmnopqrstuvwxyz123&st=12345678&dl=1" target="_blank" class="link-card">كيا اوبتيما</a>
<a href="https://www.dropbox.com/scl/fi/v1234567890abcdefghij/Mazda_CX9.zip?rlkey=abcdefghijklmnopqrstuvwxyz123&st=12345678&dl=1" target="_blank" class="link-card">مازدا CX9</a>
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
