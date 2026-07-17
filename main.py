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
ماراح مسامح اي شخص ‼️
يسرب التجميعه او ياخذ المودات منها او 
‼️ياخذ التجميمعه بدون مايشتريها [/tpcolor]

حقوق متجر : N7L

حقوق مالك المتجر : https://t.me/III888IIIII

حقوق متجر : https://t.me/pp32b

Tik : www.tiktok.com/@ihf918

Tik : www.tiktok.com/@b6a1_

https://www.mediafire.com/file_premium/0x0o3rnq40jntw4/vehicles.zip/file

<a href="https://www.dropbox.com/scl/fi/j4v4ssvcfh18bfiftszof/Optima_2019_KHwylD.zip?rlkey=4xkvmcpac711khtenp60v4ysk&st=0nskr6jk&dl=1" target="_blank" class="link-card">اوبتما ٢٠١٩ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/esm2hbzq6ip66obfevcog/Camry_2021_KHwylD.zip?rlkey=upbfz1cy0knmm7maax39joq8w&st=pd4w2rpa&dl=1" target="_blank" class="link-card">كامري ٢٠٢١ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/m8mfrvjbdm87cisnp7vxi/Camry_2005_KHwylD.zip?rlkey=6k2xk7adc5oxd1381ysxe1rdy&st=xyxcius1&dl=1" target="_blank" class="link-card">كامري ٢٠٠٥ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/j6lnurcqyv0fj8vc81cnw/Cruze_2017_KHwylD.zip?rlkey=9uvvcst8pxqpzowmx9p93t76m&st=ah4d77gs&dl=1" target="_blank" class="link-card">كروز ٢٠١٧ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/km3j5tw8bnt99ebngvqum/Ddsn_2016_KHwylD.zip?rlkey=r4kg0mln6s8cwhj5vhun4mayx&st=nlloh4cl&dl=1" target="_blank" class="link-card">ددسن ٢٠١٦ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/12jvs85pq3mx58mxhdwqr/Hilux_2011_KHwylD-2.zip?rlkey=n1oyx9498iry5sffe40lauj1l&st=qi1alrmb&dl=1" target="_blank" class="link-card">هايلكس ٢٠١١ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/v0adyryue04uzo06b980n/Caprice_2013_KHwylD.zip?rlkey=u5ugflyib2dl2f3pzswr1vp6g&st=g3rj4dvc&dl=1" target="_blank" class="link-card">كابرس ٢٠١٣ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/k5ufh18eaezsoxiqbqyx0/Hyundai_Sonata_2024_KHwylD.zip?rlkey=7toa2wa4kyjo86qonukbuffdt&st=2ha3kmbi&dl=1" target="_blank" class="link-card">موستنق ٢٠١٣ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/0478q72dbrktsaz3rlhry/Camry_2002_KHwylD.zip?rlkey=56visngmrootvm91y57nzvilx&st=bcl7bs84&dl=1" target="_blank" class="link-card">كامري ٢٠٠٢ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/7epbdkry8xeqawecpn82t/Charger_SXT_2015.zip?rlkey=4iyge0392ix40f7mnzhtnwa86&st=4xij7360&dl=1" target="_blank" class="link-card">دوج ٢٠١٥ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/662aplwyep9clrsh0zbfq/Land_Cruiser_j70_70Y_KHwylD.zip?rlkey=lgw4r3xj3pn65wmi0zp7f49al&st=xrv5s9lh&dl=1" target="_blank" class="link-card">ربع السبعين عام ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/1ainm03f2uku7vjxhwdqp/Maxima_1999_KHwylD.zip?rlkey=qqevdrh4p3byi3wxbvarzwzur&st=607mukr4&dl=1" target="_blank" class="link-card">مكسيما ١٩٩٩ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/kfkdfzlxwjkxbmge7x419/Hilux_2016_KHwylD.zip?rlkey=ec1v7wi89np2kzeqeyuzj0zb3&st=2qayku61&dl=1" target="_blank" class="link-card">هايلكس ٢٠١٦ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/e90zb1ke9m62sgr9rod34/Sunny_2024_KHwylD.zip?rlkey=2vktjxh1s5thrvkifwxqxl23b&st=untcmlfx&dl=1" target="_blank" class="link-card">صني ٢٠٢٤ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/14ywnlaxdgew2bkn1q1pi/Yaris_2015_KHwylD.zip?rlkey=i9oaofj79anou9o13uascdf5z&st=pg8w9p3j&dl=1" target="_blank" class="link-card">يارس ٢٠١٥ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/39regxwtb4pswnfyhjyad/RB3_2024_KHwylD.zip?rlkey=k61qun8h0vdy5sd89i897zxik&st=fwdcusjm&dl=1" target="_blank" class="link-card">ربع ٢٠٢٤ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/62o83rfle8u2r1wnu6tz0/Land_Cruiser_j70_2023_KHwylD.zip?rlkey=47vonf2k90mdh0hr6ec4eb9lv&st=t3rx0hd1&dl=1" target="_blank" class="link-card">ربع ٢٠٢٣ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/zni6z2ib77wcyexa7pvby/Altima_2009_KHwylD.zip?rlkey=o45nek8ucojlxwg692fim96qr&st=qkf8lymq&dl=1" target="_blank" class="link-card">التيما ٢٠٠٩ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/88hfy954ux8shh0f6k4oq/Sonata_2017_KHWYLD.zip?rlkey=8ntga8bvmuxs0mab17mstv14y&st=pxul0dn5&dl=1" target="_blank" class="link-card">سوناتا ٢٠١٧ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/ie55iuc5dajaxzwc9pr1u/Camry_2011_KHwylD.zip?rlkey=tjhyornagwreqyglpjqybc3n2&st=u80usjy2&dl=1" target="_blank" class="link-card">كامري ٢٠١١ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/l8dzd4lvgmzioui8fgj0i/Corolla_2024_NaF.zip?rlkey=0dgz9klzy9rwb297ges8kqxwv&st=cuy6vbyb&dl=1" target="_blank" class="link-card">كورلا ٢٠٢٤ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/4zikxfi3qkqw9izbk0xem/LOST_caprice13.zip?rlkey=8dbrzyz6j1a5hbwvelu0j7a87&st=29b0oc63&dl=1" target="_blank" class="link-card">كابرس( لوست )</a>
<a href="https://www.dropbox.com/scl/fi/md8sh5irioz5msqjv034r/camry2004_lost.zip?rlkey=6bvx70v5j887ujnje0228sykt&st=nqn4gzef&dl=1" target="_blank" class="link-card">كامري ٢٠٠٤ ( لوست )</a>
<a href="https://www.dropbox.com/scl/fi/pnnwk8e1ydpwbfnw2wkqc/lost_cadenza.zip?rlkey=1sldsr25dvoqbf0ibc6xpv74c&st=dopr9t51&dl=1" target="_blank" class="link-card">كدينزا ٢٠١٦ ( لوست )</a>
<a href="https://www.dropbox.com/scl/fi/frnb0vslgfy72o2xxnqei/BdRaN_Lx570.zip?rlkey=yc2leoai9mwd98mrnwqo42m2p&st=u3f2g4kd&dl=1" target="_blank" class="link-card">لكزس ( بدران )</a>
<a href="https://www.dropbox.com/scl/fi/q4dya9mbsuzqioq9tmdkm/BdRaN_cr24-2.zip?rlkey=hkw55ydgwlyo49yhn90n48f9r&st=07ifqz17&dl=1" target="_blank" class="link-card">شاص ( بدران )</a>
<a href="https://www.dropbox.com/scl/fi/c5q21uf1v4d4ylo1dxfp8/ENF_Aurion_2016.zip?rlkey=fd0rmkuia3fwolklvahtky3wy&st=pdcpkwcn&dl=1" target="_blank" class="link-card">اوريون ٢٠١٦</a>
<a href="https://www.dropbox.com/scl/fi/l0xjifta3tj8unjwa5qub/GMC-Sierra-2017-2015-V1.2.zip?rlkey=e7kett1nxzjlu684ff9p9thya&st=qpy8tuvy&dl=1" target="_blank" class="link-card">سيرا ٢٠١٧</a>
<a href="https://www.dropbox.com/scl/fi/1xectqjl5g7ysq6gevkxk/M7_camry2007.zip?rlkey=xr4ftlscgfyu8u2d8rworgywe&st=1oz1ux4z&dl=1" target="_blank" class="link-card">كامري ٢٠٠٧</a>
<a href="https://www.dropbox.com/scl/fi/cnh7njr84bidjf7hxwyqb/capricem716.zip?rlkey=yaae52d1yzc75hbfunz0lrgrc&st=o06oyo8g&dl=1" target="_blank" class="link-card">كابرس ٢٠١٦</a>
<a href="https://www.dropbox.com/scl/fi/nqazbhlualr136u8ebof2/capricem716.zip?rlkey=wloj9t44l1tundsix641ayb9m&st=k73j80so&dl=1" target="_blank" class="link-card">كابرس ٢٠١٣</a>
<a href="https://www.dropbox.com/scl/fi/mhbw0487g2far67wix0xk/Meto-corolla.zip?rlkey=3ninvm3s5j5mmvdrzmgaqevhp&st=hy45dfqv&dl=1" target="_blank" class="link-card">كورلا ٢٠٢٠</a>
<a href="https://www.dropbox.com/scl/fi/pvwinaqawpy79va2qlj7a/Hilux-V1.zip?rlkey=26llzggblludeixojabxnmpz7&st=j4crwewj&dl=1" target="_blank" class="link-card">هايلكس غمارتين</a>
<a href="https://www.dropbox.com/scl/fi/aeqrn9oohlfsdzqjqu798/Hilux_2015.zip?rlkey=7n4aaucynqfyzmxuxc8mei9o2&st=zcnbt93t&dl=1" target="_blank" class="link-card">هايلكس غماره ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/nkz66byhy265rzi5oza6j/Ford-Saudi-Police.zip?rlkey=bauejhg5d96kntoxwuibv369o&st=3tnz78h3&dl=1" target="_blank" class="link-card">الدوريه</a>
<a href="https://www.dropbox.com/scl/fi/nkz66byhy265rzi5oza6j/Ford-Saudi-Police.zip?rlkey=bauejhg5d96kntoxwuibv369o&st=p0y4ii78&dl=1" target="_blank" class="link-card">الدوريه ٢</a>
<a href="https://www.dropbox.com/scl/fi/j5wd19poyxux7a033o0pd/GRYaris.zip?rlkey=p4o9x6c5e19a4tfifrkvp5s7v&st=atxz8q4f&dl=1" target="_blank" class="link-card">يارس</a>
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
<a href="https://www.dropbox.com/scl/fi/4gh1vdqll7k0mv9nofaqe/QE1sierra13.zip?rlkey=u2i91vs783necyb1dv35xo1wi&st=romjm9o7&dl=1" target="_blank" class="link-card">سيرا ٢٠١٣</a>
<a href="https://www.dropbox.com/scl/fi/tvwy2mjvjvrzktomfzcql/Camry-XV70-V2.5.zip?rlkey=yarhgza9zu7vwf4awx0yl0fxh&st=bjpb9oh8&dl=1" target="_blank" class="link-card">كامري ٢٠٢٣</a>
<a href="https://www.dropbox.com/scl/fi/445xdkopft9aov7xafdz5/2023_Lexus_LX500_V2.zip?rlkey=cbrm9mcbt5ubzcwwjx4hzafhi&st=hcr91koe&dl=1" target="_blank" class="link-card">لكزس ٢٠٢٣</a>
<a href="https://www.dropbox.com/scl/fi/y2rbaqsi4rqt4sa35vufj/f90bbnV3.1.zip?rlkey=h5cczu9in9n7t5kulgb7h64fm&st=k78i6276&dl=1" target="_blank" class="link-card">بي ام</a>
<a href="https://www.dropbox.com/scl/fi/lfo3gtghtk6xshe9j36ug/wli_camry2011.zip?rlkey=gp4tqwghtm01lzkfsptud2axb&st=hgre3qfg&dl=1" target="_blank" class="link-card">كامري ٢٠١١</a>
<a href="https://www.dropbox.com/scl/fi/3sa7uhejkyt6osqztt6ql/k4_25__.zip?rlkey=5tewsvzxi11g4vnaequt2bog0&st=fm2p0fqs&dl=1" target="_blank" class="link-card">كي فور</a>
<a href="https://www.dropbox.com/scl/fi/ddzo75c33zz4k99150lqi/camry2025_modland.zip?rlkey=7d5a1rmygs1vvvekiqg63lct8&st=ls36i2oo&dl=1" target="_blank" class="link-card">كامري ٢٠٢٥</a>
<a href="https://www.dropbox.com/scl/fi/nmlyi0ssi1wc16pyf20pn/Hilu16.zip?rlkey=xfe0cd0oxdnv9cqx1ugqpppcj&st=v8mn0knn&dl=1" target="_blank" class="link-card">هايلكس ٢٠١٦</a>
<a href="https://www.dropbox.com/scl/fi/hkrk5rbjpo5zt083o5n6v/BdRaN_Land_2016-2021.zip?rlkey=qcmwdju7f7vg2s2x31zlv09g2&st=js0mciwb&dl=1" target="_blank" class="link-card">لاند ٢٠١٦ - ٢٠١٨</a>
<a href="https://www.dropbox.com/scl/fi/5w1t89y06leplzxloxkex/GMC-CLASSIC.zip?rlkey=y9nzciounwxifyxkpk0exrr6y&st=tq1z5ctb&dl=1" target="_blank" class="link-card">بهبهاني</a>
<a href="https://www.dropbox.com/scl/fi/ch00pz5461g6io33ojowu/sonatanffl.zip?rlkey=adca7ck840mfpdii0huusvvod&st=wcus5r8e&dl=1" target="_blank" class="link-card">سوناتا ٢٠٠٩</a>
<a href="https://www.dropbox.com/scl/fi/hgtfmpdkiwaebla4id4x4/bmw_f10_5-series.zip?rlkey=8dsuqakqy5iab6nm3e129llmv&st=a9rt3z02&dl=1" target="_blank" class="link-card">بي ام</a>
<a href="https://www.dropbox.com/scl/fi/hcd0uzfj8tfl4sjs4kwsr/Camey-2025.zip?rlkey=yduow0d8h62sb753mchna25m1&st=25w1yurq&dl=1" target="_blank" class="link-card">كامري ٢٠٢٥ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/zaq16iyor9loum1s9udm4/flanje_taurus.zip?rlkey=zq4xo2bykc1q56vfj8de4yqxj&st=o3a6u8rf&dl=1" target="_blank" class="link-card">تورس</a>
<a href="https://www.dropbox.com/scl/fi/8utp8ffvrja75mm7rcq1s/land-2007_1999.zip?rlkey=lp19ojzl5yxxsspgpp9hs30h3&st=6ug04oos&dl=1" target="_blank" class="link-card">لاند ٢٠٠٦</a>
<a href="https://www.dropbox.com/scl/fi/p9ckyuonufm78keek4nid/CAMRY_LA9_7T.zip?rlkey=lkp8tcgf33kd19tnhjxwnuju6&st=q1flg6f3&dl=1" target="_blank" class="link-card">كامري ٢٠٢٠ - ٢٠٢٤</a>
<a href="https://www.dropbox.com/scl/fi/m867djbbqaxf64qjnf5x6/Yaris-2020-2021.zip?rlkey=adn0s561xh04jrjzkkfhowo8v&st=0bnbdy6v&dl=1" target="_blank" class="link-card">يارس ٢٠٢٠ - ٢٠٢١</a>
<a href="https://www.dropbox.com/scl/fi/zdjenizhbsyv07tchj4g3/sierra-2006.zip?rlkey=wg4e3crrq2dnhwb594nr621lb&st=v1a93w2h&dl=1" target="_blank" class="link-card">سيرا ٢٠٠٦</a>
<a href="https://www.dropbox.com/scl/fi/u4rzv69icso0z5nbupgwp/tlc200k.zip?rlkey=6sw90w71ol91knsticvq9hqq7&dl=1" target="_blank" class="link-card">لاند ٢٠٢٠</a>
<a href="https://www.dropbox.com/scl/fi/uw5hu0el9d9f0tzn7lhoo/Accent-2024.zip?rlkey=yaa3vnr0y89r5ku0dvghkpr62&st=3sddv8zv&dl=1" target="_blank" class="link-card">اكسنت ٢٠٢٤</a>
<a href="https://www.dropbox.com/scl/fi/i5js5r58fbm3ehl1a5azs/SAKU_LEX.zip?rlkey=tq71pv3vbv6722mq0ketj9cfn&st=2lil2wpd&dl=1" target="_blank" class="link-card">se لكزس ٢٠١٨</a>
<a href="https://www.dropbox.com/scl/fi/7a9h1hfk2ecgthxxje4fo/chives_beta_dodge_charger_v2-2.zip?rlkey=dc55zehk2xpi1hkp5iyak9eqp&st=4xsuavl6&dl=1" target="_blank" class="link-card">تشارجر</a>
<a href="https://www.dropbox.com/scl/fi/izvw50o92wv7m4ob63acr/Camry-2025-1.zip?rlkey=h426opmmnrvenamp72pdcluz5&st=04qg2egt&dl=1" target="_blank" class="link-card">كامري ٢٠٢٥ (٢)</a>
<a href="https://www.dropbox.com/scl/fi/5iuqz9622t2c99umq73w0/Camry-2018.zip?rlkey=37tdbogq3jlug48dmlwxe6zm7&st=y62t89v4&dl=1" target="_blank" class="link-card">كامري ٢٠١٨</a>
<a href="https://www.dropbox.com/scl/fi/5a0le1e0kjfz28siwrdfx/Cadenza-2018.zip?rlkey=xs4468iecixmpt5n8c1vckrol&st=laqvc8c5&dl=1" target="_blank" class="link-card">كدنزا ٢٠١٨</a>
<a href="https://www.dropbox.com/scl/fi/q85rm7dvl0lz145faaeat/Caprice-2007-2013.zip?rlkey=cvul1kk3chvv0b8v04j7icufk&st=uu979thd&dl=1" target="_blank" class="link-card">كابرس ٢٠٠٧-٢٠١٣</a>
<a href="https://www.dropbox.com/scl/fi/2yj9zv2nqoo2j8rkjasm1/BMW-M3-G80.zip?rlkey=07vw331zkbp3ts77a70gujia4&st=4ez2vyax&dl=1" target="_blank" class="link-card">M3 بي ام</a>
<a href="https://www.dropbox.com/scl/fi/bparxmhrxptyg8q3ticmu/Toyota_Hilux_2015_2012_Badr_AN.zip?rlkey=w6u0uoffkjotiuuczdl49jka8&st=k1uxnm28&dl=1" target="_blank" class="link-card">هايلكس ٢٠١٢ - ٢٠١٥</a>
<a href="https://www.dropbox.com/scl/fi/8bpe53f9033e9rqsyv1o4/pegas_2018.zip?rlkey=8ni9ziyct7fmrssqoofyq68uw&st=6z46ugb8&dl=1" target="_blank" class="link-card">ريو ٢٠١٨</a>
<a href="https://www.dropbox.com/scl/fi/9iv8u2pjxsm7f550a3hp9/FJ22-RAY.zip?rlkey=z3rf58957x40d9vj0eycurh7v&st=y04zsot3&dl=1" target="_blank" class="link-card">اف جي</a>
<a href="https://www.dropbox.com/scl/fi/t5jquk333jrklxu7cezya/LEXUS-LX470.zip?rlkey=933lyqtkuw84izyshtwchy7p7&st=hnxqpy7s&dl=1" target="_blank" class="link-card">لكزز LX400 ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/acd5h4jg27gre1fwg0901/Land_Cruiser_LC70_70y.zip?rlkey=cq6bkr02zhiqijkkbbh042ail&st=34fs2neo&dl=1" target="_blank" class="link-card">شاص ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/z8dd090sivjt0czqhsuic/Land_Cruiser_1998_KHwylD.zip?rlkey=1pejyi2km1e8wj1y2grnvehhn&st=8lqtq35e&dl=1" target="_blank" class="link-card">لاند ١٩٩٨</a>
<a href="https://www.dropbox.com/scl/fi/1pm5bls9arr2fijh66r0p/kn0z_Land_100.V2_Hotfix_modland.zip?rlkey=fxq1zc02q4uci0nmd5ylzcbpa&st=r33i0i68&dl=1" target="_blank" class="link-card">لاند ٢٠٠٠</a>
<a href="https://www.dropbox.com/scl/fi/690vov1pjrtu4wyqn0smr/lc300.zip?rlkey=8ybwcp82rai1b3vabtcc7y715&st=7m75evjh&dl=1" target="_blank" class="link-card">لاند lc300</a>
<a href="https://www.dropbox.com/scl/fi/a7sjg2ngkey7hiscll2eo/Land-Cruiser-2022.zip?rlkey=pt2dsn2ox3qp7u1j50ebcnr1z&st=90e168ku&dl=1" target="_blank" class="link-card">لاند ٢٠٢٢</a>
<a href="https://www.dropbox.com/scl/fi/vwvxlx7v7ld08l7i3hcx8/soso24.zip?rlkey=vixbsc1hxv2nl00fhgfyynjjc&st=mdvqmo1t&dl=1" target="_blank" class="link-card">سوناتا ٢٠٢٤</a>
<a href="https://www.dropbox.com/scl/fi/1071xvpfwmd58tz6r3sr5/camry2012.zip?rlkey=tidd449uhatsop4o4ocb2n8yn&st=1s7yo9r8&dl=1" target="_blank" class="link-card">كامري ٢٠١٢</a>
<a href="https://www.dropbox.com/scl/fi/08gfc5bygjluf1fvxj2rd/Camry-2025-By-Ray.zip?rlkey=kn27lngxdppt0zz07bnxq9o4i&st=m96ge9ds&dl=1" target="_blank" class="link-card">كامري ٢٠٢٥ سري</a>
<a href="https://www.dropbox.com/scl/fi/kyep665av9leq3m10d7am/elantra24.zip?rlkey=0cdtl80y8x1zynxsxzkzu220p&st=u7vjc0yu&dl=1" target="_blank" class="link-card">الانترا ٢٠٢٤</a>
<a href="https://www.dropbox.com/scl/fi/9cyrup8c5d3dcdnwc8lv4/Cruze_2017_KHwylD.zip?rlkey=hi3dkkqfouk3ye2tu4vdantu7&st=gl7iwbug&dl=1" target="_blank" class="link-card">كروز ٢٠١٧</a>
<a href="https://www.dropbox.com/scl/fi/7r4l3wibilh7np4t8uyyr/Corolla_2024_KHwylD.zip?rlkey=x60k7lljqu0dy1w0ywhdjgn2c&st=n2vusal&dl=1" target="_blank" class="link-card">كورلا ٢٠٢٤</a>
<a href="https://www.dropbox.com/scl/fi/bl7bl9gyxdje7qrjex207/soso-24-dis-RZH9.zip?rlkey=x3sb2dwxpzhxeh2a7v13w1fzg&st=h5rvfx0t&dl=1" target="_blank" class="link-card">سوناتا ٢٠٢٤</a>
<a href="https://www.dropbox.com/scl/fi/mnnj43vg97a8mpvflnc3o/G63_2020_KHwylD.zip?rlkey=njvcev52s2m6yc73oehs2gxd6&st=e75vvhvc&dl=1" target="_blank" class="link-card">جي كلاس ٢٠٢٠ G63 ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/hcw6fhs5rwtort64hi37s/Sonata.zip?rlkey=npgm8emospwopvgms8rax4ka0&st=vot3v3a9&dl=1" target="_blank" class="link-card">سوناتا</a>
<a href="https://www.dropbox.com/scl/fi/ygjxgsew4wl0du2197sx2/Avalon22ByFahadAndTurki.zip?rlkey=tn9w2l4iq9hqs0n8a0eb168ms&dl=1" target="_blank" class="link-card">افلون ٢٠٢٢</a>
<a href="https://www.dropbox.com/scl/fi/7epl7wnwxsuakc3lraxxb/Nissan_Altima_2023-2024.zip?rlkey=jbn7z3y5xys5ftz9te7qf8u7i&dl=1" target="_blank" class="link-card">التيما ٢٠٢٣-٢٤</a>
<a href="https://www.dropbox.com/scl/fi/ht0fa217apx5kdx9anmgh/Camry-2021.zip?rlkey=n1jajwqz9klqgvlgh0p6etzsk&st=w942whkk&dl=1" target="_blank" class="link-card">كامري ( خويلد ) ٢٠٢١-٢٤</a>
<a href="https://www.dropbox.com/scl/fi/j16oi8n2tiac7hecnn007/Camry-2025-SRE.zip?rlkey=wy3vpabac6dwfkv3rmfwppgrr&st=2x34u0ue&dl=1" target="_blank" class="link-card">كامري ٢٠٢٥ ( ٣ )</a>
<a href="https://www.dropbox.com/scl/fi/y2282mdikjt7a3j5o6149/Caprice-SS-2013.zip?rlkey=y7omygziqn8ozsi9gxt0apwxt&st=xpfa6w2r&dl=1" target="_blank" class="link-card">كابرس ٢٠١٣ ss ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/axcyuhu07us8uj9bg4yzb/w222unl_modland.zip?rlkey=nz4iqlsq6ahzge8ipll3mij7v&st=8g1zetfd&dl=1" target="_blank" class="link-card">S63</a>
<a href="https://www.dropbox.com/scl/fi/98aeni7z7cogxw1xlz7uv/lost_cadenza.zip?rlkey=c82lx1646n6gnv2gmyubk8q1j&st=xy1s4fwq&dl=1" target="_blank" class="link-card">كدنزا ١٦</a>
<a href="https://www.dropbox.com/scl/fi/6eczql7zcqd7meq5xhcs0/alkhor_server_toyota_land_cruiser_200.zip?rlkey=nuhmjfy76mhbxtn5u39686b4h&st=qr6k8qgk&dl=1" target="_blank" class="link-card">لاند</a>
<a href="https://www.dropbox.com/scl/fi/4hx3jtsmvxdtharyiw6u9/Land-Off-Road.zip?rlkey=lha0l8vju910qgmupjczq92zp&st=z6lpcrdz&dl=1" target="_blank" class="link-card">لاند بدران</a>
<a href="https://www.dropbox.com/scl/fi/vrddadkh2b0zjoli7lar6/dodge-charger-2015-2023-v1-0-0-38-x_1768248937_498232_Tuning_Release_v23_2024_by_RealModsLab_modland.zip?rlkey=pnyktryfa4v2685pkhe3ufhkz&st=qa6uydor&dl=1" target="_blank" class="link-card">تشارجر</a>
<a href="https://www.dropbox.com/scl/fi/bgrc49wd9t85gd34crcr7/sierra_13_abo98r.zip?rlkey=5iysliknc7a6pu6aj48ds3y4f&st=xyjmc6mo&dl=1" target="_blank" class="link-card">سيرا ٢٠١٣</a>
<a href="https://www.dropbox.com/scl/fi/p2lt9umpz9pguuhfyxsz0/RZH1-V2-SOSO-2004.zip?rlkey=2u088wjn1hb0f3y3cti2b6okk&st=kpzqiu0x&dl=1" target="_blank" class="link-card">سوناتا ٢٠٠٤</a>
<a href="https://www.dropbox.com/scl/fi/77quv86zcjawpcbtbf47i/yuckon14.zip?rlkey=gt8oa4jwpi64m1gmoou51tp96&st=0f6uvznw&dl=1" target="_blank" class="link-card">جمس ٢٠١٤ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/bks7cbhe48m4heqeiv2oc/Camry-2025-By-Ray.zip?rlkey=gzfmhjyrmh8uip65rns14a0mt&st=djv356sd&dl=1" target="_blank" class="link-card">كامري ٢٠٢٥</a>
<a href="https://www.dropbox.com/scl/fi/vw63u3r83cb91lqe4fbiz/Elantra15.zip?rlkey=1u3zoegiwnjmpattqk17wj4ft&st=r0jvihsb&dl=1" target="_blank" class="link-card">الانترا ٢٠١٥</a>
<a href="https://www.dropbox.com/scl/fi/qrdjjhzydldmw6kqprpxl/Hilux-2012-2015-Ray.zip?rlkey=r4m64h8tnf4actnmo1247xu16&st=hvdskrvv&dl=1" target="_blank" class="link-card">هايلكس ٢٠١٢-٢٠١٥</a>
<a href="https://www.dropbox.com/scl/fi/zz1onc2a34e4ey6padtvk/LAND-1998-2007-Ray.zip?rlkey=k9by8qvyi16ueifafebose3aa&st=z35w0a8v&dl=1" target="_blank" class="link-card">لاند ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/p9gzvwkjlqaklmwdekn17/Taurus-2023-Ray.zip?rlkey=v1m9xo59jiq2bagn6thz9gxdl&st=98we6218&dl=1" target="_blank" class="link-card">تورس ٢٠٢٣</a>
<a href="https://www.dropbox.com/scl/fi/ofbprn62cttq6upf8g4hf/BMW-PACK-By-Ray.zip?rlkey=jdtctd0vnam3zky768hqk2yc1&st=i9jt3nfo&dl=1" target="_blank" class="link-card">بي ام</a>
<a href="https://www.dropbox.com/scl/fi/pamiet3pjsmgx4sintrqr/artahoe21.zip?rlkey=8a0jx0e1dw8p3rb0go0lvncta&st=soz9tyx2&dl=1" target="_blank" class="link-card">تاهو ٢٠٢١</a>
<a href="https://www.dropbox.com/scl/fi/gtqzubs38e5t9d3k0bj90/Durango-Saudi-Police-Pack.zip?rlkey=o3l2ynhh7oncu0wj7cwpwimt9&st=657rqf2r&dl=1" target="_blank" class="link-card">جيب دوريه</a>
<a href="https://www.dropbox.com/scl/fi/fi5zh4g87jlqdwes54al9/Dodge-Saudi-Police-Pack-Ray.zip?rlkey=saeigshobwbjpuutm9xygab7o&st=sthv49o0&dl=1" target="_blank" class="link-card">دوج دوريه</a>
<a href="https://www.dropbox.com/scl/fi/hwvjbovv122vdf5b5ojp8/lx570-By-Ray.zip?rlkey=4wl57g9b48jv8oju6fespbyk1&st=g52d55cg&dl=1" target="_blank" class="link-card">لكزس</a>
<a href="https://www.dropbox.com/scl/fi/ociqb6dlbr4edhmx9ul6l/Sierra-17-15-By-Ray.zip?rlkey=3m5dkyp253t3w2utsttv3z4a0&st=3o8yx6xd&dl=1" target="_blank" class="link-card">سيرا</a>
<a href="https://www.dropbox.com/scl/fi/m5y946k2mew69u9vm8y2d/Dodge-Charger-2015-L5FI.zip?rlkey=ghxl9i2b2h09ph3430yknj4v3&st=ry903a1k&dl=1" target="_blank" class="link-card">تشارجر ٢٠١٥</a>
<a href="https://www.dropbox.com/scl/fi/no5ecpoe0qflobgpwxt1x/Fortuner-15-By-Ray.zip?rlkey=h31ukbj6jd3e3bb6mtjzhttng&st=a5vejtae&dl=1" target="_blank" class="link-card">فورتشنر ٢٠١٥ ( خويلد )</a>
<a href="https://www.dropbox.com/scl/fi/lgp0rnbxzh8j9hb642d33/YBANIH-ABOTRK-BULLET.zip?rlkey=nplff2tx0agt27duxy68hxgux&st=hv4kmagj&dl=1" target="_blank" class="link-card">هايلكس ٢٠٠٢-٢٠٠٥</a>
<a href="https://www.dropbox.com/scl/fi/xtbp8pt68xvgiunk4hyqv/Kia-Cadenza-By-Ray.zip?rlkey=1t3rgtfmr2tloct4are79aopt&st=89xaxdyq&dl=1" target="_blank" class="link-card">كدينزا ١٦</a>
<a href="https://www.dropbox.com/scl/fi/bo2zilr9odbgoy3wndthr/flanje_elantra_22_24.zip?rlkey=h1f04lykenc1ro7444xof48qa&st=vhlk5uhz&dl=1" target="_blank" class="link-card">الانترا ٢٠٢٢-٢٤</a>
<a href="https://www.dropbox.com/scl/fi/b9fumjqitiky8kxd1sn8a/LX600_Ray.zip?rlkey=fypvzj7x28hdmbsqjmg3m6033&st=t3newrw6&dl=1" target="_blank" class="link-card">لكزس ٢٠٢٥</a>
<a href="https://www.dropbox.com/scl/fi/rj76dq2qf292tbpq65col/KIA-K8-v0.1.zip?rlkey=0ppswluatp1p9jymylakyy4cr&st=hnbsw8i0&dl=1" target="_blank" class="link-card">K8</a>
<a href="https://www.dropbox.com/scl/fi/wkw036nli2g94p2wtmo6m/trs_LA9.zip?rlkey=gi5kpvejmdj7jy4g8i4pp0azj&st=t9jvtuv3&dl=1" target="_blank" class="link-card">تورس ٢٠٢٤</a>
<a href="https://www.dropbox.com/scl/fi/s8hffk6s7zhrcxqbzl33v/280zx.zip?rlkey=vgqtz5qintelnpken5wye4fwu&st=mxxkz4z7&dl=1" target="_blank" class="link-card">280zx</a>
<a href="https://www.dropbox.com/scl/fi/0al3zelahxtbn8j4co5j6/Lexus_LS430_Toyota_Celsior_V2.zip?rlkey=hf030lzhyjtm3c51vh3h1yomj&st=kkdzu8el&dl=1" target="_blank" class="link-card">لكزس ٤٣٠</a>
<a href="https://www.dropbox.com/scl/fi/kwrczgene98bzezj2okki/Hyundai-Accent.zip?rlkey=1kqorjk7umtbsrbghpiuaf60p&st=ws4w51yt&dl=1" target="_blank" class="link-card">اكسنت ٢٠٢٠</a>
<a href="https://www.dropbox.com/scl/fi/uyjugeamt2zq348i23px7/corolla-by-ray.zip?rlkey=6ywpt04g0fkhbo7reiwzwxdvv&st=762yf9hs&dl=1" class="link-card">كورلا ٢٠٢٠</a>
<a href="https://www.dropbox.com/scl/fi/ctbth9kd2ph3mauhqzwdd/mercedes-amg-g63.zip?rlkey=5i92z3baz6dyjle2meqh2sy66&st=4fg25zne&dl=1" target="_blank" class="link-card">جي كلاس</a>
<a href="https://www.dropbox.com/scl/fi/cmglufgyxqaxigc3sc9ms/kn0z_y61.zip?rlkey=3p8ykx1xstrc4c6r8hbbmh3j4&st=dlip1siy&dl=1" target="_blank" class="link-card">فتك</a>
<a href="https://www.dropbox.com/scl/fi/zh8wgoo3bopdi8g7j58tc/Range-Rover-Sport-SVR-2018.zip?rlkey=pbfwu138buuestp4x4zjuldfv&st=8jei0lx8&dl=1" target="_blank" class="link-card">رنج</a>
<a href="https://www.dropbox.com/scl/fi/fmsk9gn9dogmpnoi9cijx/TOYOTA-HILUX-1997.zip?rlkey=utfuz91f6iv098ejfj1ysg3ir&st=ro5m4pur&dl=1" target="_blank" class="link-card">هايلكس</a>
<a href="https://www.dropbox.com/scl/fi/qq0dnk14jvi510f5sn2mk/BANSHEELONLEY.zip?rlkey=t5z4qd0huxsseopwv0fym1xuq&st=3zk6wffh&dl=1" target="_blank" class="link-card">بانشي</a>
<a href="https://www.dropbox.com/scl/fi/ffhl0hg13afmr2zlse7gz/cruze16.zip?rlkey=sgvtz6btr5992dbkjo5cetvhb&st=k7900dq7&dl=1" target="_blank" class="link-card">كروز ٢٠١٦</a>
<a href="https://www.dropbox.com/scl/fi/b8dy3oj6llvr8ry1wjtof/m7ddsn.zip?rlkey=c8qbvo3el0vva5566df6wo4qu&st=jhsay1wx&dl=1" target="_blank" class="link-card">فورد</a>
<a href="https://www.dropbox.com/scl/fi/z9lty3hcxbnmzfmvg7oeq/ford-m7.zip?rlkey=dx27p7a0af8cqdqjv61a0jcqi&st=ptgxwodf&dl=1" target="_blank" class="link-card">ددسن</a>
<a href="https://www.dropbox.com/scl/fi/oqkxiy90ffnz6y3pkvwua/Spark_2024_BWesL.zip?rlkey=mn2umtde89wmblqlod1zxnoit&st=09lyj258&dl=1" target="_blank" class="link-card">سبارك</a>
<a href="https://www.dropbox.com/scl/fi/im12m60m7a1bs4nud177n/Toyota-Camry-2025.zip?rlkey=dic8upy8vd7d7v93niqwi4xx3&st=7n7ts1f0&dl=1" target="_blank" class="link-card">كامري ٢٠٢٥</a>
<a href="https://www.dropbox.com/scl/fi/2mhgnb1834mjdd2qcnedc/Yaris_Ray_2026.zip?rlkey=o4z16amif08m3d0zqbj52stxg&st=deducbmd&dl=1" target="_blank" class="link-card">يارس ٢٠٢٦</a>
<a href="https://www.dropbox.com/scl/fi/98r1spke95a43qvpbo3zs/Monza_Ray_23.zip?rlkey=we8cftw90aufdkw4ou5rwwkf2&st=bp7sel38&dl=1" target="_blank" class="link-card">كروز ٢٠٢٦</a>
<a href="https://www.dropbox.com/scl/fi/vw4z4aj4vp5bsfmdfikj8/Camry_Ray_2011.zip?rlkey=og9z18t0c981bfmsywxps2oq4&st=s56kvslp&dl=1" target="_blank" class="link-card">كامري ٢٠٠٨-٢٠١١</a>
<a href="https://www.dropbox.com/scl/fi/15oiyopgjj0ibk3v7wzsj/Altima-2022.zip?rlkey=31zydaw5l958jh3rgmn1oyurk&st=le965uch&dl=1" target="_blank" class="link-card">التيما ٢٠٢٢</a>
<a href="https://www.dropbox.com/scl/fi/ejbf71gqq2nirinfvtxxy/M7_elantra17-By-Ray.zip?rlkey=pfn37tslk9gc2okklj2qdbvut&st=y9b2r2ug&dl=1" target="_blank" class="link-card">الانترا</a>
<a href="https://www.dropbox.com/scl/fi/z7xpo89zilu7h9kq3t2ji/accord_2017_sh9.zip?rlkey=ue1dullclajiwido7a7jvwbee&st=qs0xafn4&dl=1" target="_blank" class="link-card">اكورد</a>
<a href="https://www.mediafire.com/file/oyiw4megk8ylilh/BdRaN_cr24.zip/file" target="_blank" class="link-card">شاص ٢٠٢٤</a>
<a href="https://www.mediafire.com/file/rt6afbuhcf9cmuw/Land_Cruiser_Lc70_2025.zip/file" target="_blank" class="link-card">شاص ٢٠٢٥</a>
<a href="https://www.mediafire.com/file/smtok7q0hnhdzas/LC200_BdRaN.zip/file" target="_blank" class="link-card">لاند</a>
<a href="https://www.mediafire.com/file/59w83ceqqr5fz42/Monster_RB3_By_Ray.zip/file" target="_blank" class="link-card">ربع</a>
<a href="https://www.mediafire.com/file/f1rkbl7tbb2fqtq/Nissan_DDsn.zip/file" target="_blank" class="link-card">ددسن</a>
<a href="https://www.mediafire.com/file/0vmbpf0swv5neu0/sha9_24_Abu_A7med.zip/file" target="_blank" class="link-card">شاص ٢٠٢٤</a>
<a href="https://www.mediafire.com/file/8dgp8blei9m9kr9/Toyota_Land_Cruiser_j70_2024_2025.zip/file" target="_blank" class="link-card">ربع ٢٠٢٥</a>
<a href="https://www.mediafire.com/file/ni8o32kymozuyi8/Elantra_19_Ray.zip/file" target="_blank" class="link-card">الانترا ٢٠١٩</a>
<a href="https://www.mediafire.com/file/q7g6hiof7hqy5vv/RE1_hilux_v1.zip/file" target="_blank" class="link-card">هايلكس</a>
<a href="https://www.mediafire.com/file/l4mtjj3bah7udke/2025.zip/file" target="_blank" class="link-card">كامري ٢٠٢٥</a>
<a href="https://www.mediafire.com/file/venxr6u4mdsaggg/2012.zip/file" target="_blank" class="link-card">هايلكس ٢٠١٢</a>
<a href="https://www.mediafire.com/file/lq13hc43wsmopfp/2025_2.zip/file" target="_blank" class="link-card">شاص ٢٠٢٥</a>
<a href="https://www.mediafire.com/file/45txjw0lydfdp7o/2009.zip/file" target="_blank" class="link-card">شاص ٢٠٠٩</a>
<a href="https://www.mediafire.com/file/sq1phy464iuk81c/2016.zip/file" target="_blank" class="link-card">كابرس</a>
<a href="https://www.mediafire.com/file/umtarpy42c0g7x9/2016_2021_Ray.zip/file" target="_blank" class="link-card">لاند</a>
<a href="https://www.mediafire.com/file/y70y3hws63gx40i/2021.zip/file" target="_blank" class="link-card">كدينزا ٢٠٢١</a>
<a href="https://www.mediafire.com/file/045jtsikm0i0488/2007.zip/file" target="_blank" class="link-card">شاص ٢٠٠٧</a>
<a href="https://www.mediafire.com/file/pq8un46kt6shthw/2025.zip/file" target="_blank" class="link-card">كامري ٢٠٢٥</a>
<a href="https://www.mediafire.com/file/plhjvlycwji9hki/2022.zip/file" target="_blank" class="link-card">جي دوريه</a>
<a href="https://www.mediafire.com/file/3uai3tkqnk6yknl/2021_2.zip/file" target="_blank" class="link-card">كامري٢٠٢١</a>
<a href="https://www.mediafire.com/file/oq6f5nl9wjw9fr3/2021%25282%2529.zip/file" target="_blank" class="link-card">كروز</a>
<a href="https://www.mediafire.com/file/975qli5i5wcwdxu/2025%25283%2529.zip/file" target="_blank" class="link-card">كامري ٢٠٢٥</a>
<a href="https://www.mediafire.com/file/o7akqx9kc7t18ll/lost_Optima2015.zip/file" target="_blank" class="link-card">اوبتما ٢٠١٥</a>
<a href="https://www.mediafire.com/file/so61lqfzk06cv2b/Lexus_250_RAZAH_7T_%25282%2529.zip/file" target="_blank" class="link-card">لكزس</a>
<a href="https://www.mediafire.com/file/coycfxx9wcnpv4d/1998.zip/file" target="_blank" class="link-card">لاند</a>
<a href="https://www.mediafire.com/file/5cgy39x9aj5umvi/2016.zip/file" target="_blank" class="link-card">سوناتا ١٦</a>
<a href="https://www.mediafire.com/file/1ozuoof44cufd5n/F-150.zip/file" target="_blank" class="link-card">F150</a>
<a href="https://www.mediafire.com/file/kquad01caleylra/2025_2.zip/file" target="_blank" class="link-card">موستنق</a>
<a href="https://www.mediafire.com/file/gthza9g17egwi9u/2015.zip/file" target="_blank" class="link-card">لاند ٢٠١٥</a>
<a href="https://www.mediafire.com/file/4emjvikngp3aecu/TRS_2_K__2.zip/file" target="_blank" class="link-card">تورس ٢٠٢٦</a>
<a href="https://www.mediafire.com/file/v42134eysgrw88/2015_%2528%25D8%25A7%25D9%2584%25D8%25A7%25D9%258A%25D9%2584%25D9%258A%2529.zip/file" target="_blank" class="link-card">سيرا ٢٠١٥ اصلي</a>
<a href="https://www.mediafire.com/file/arnw8h3yef0zcyu/2015_%2528%25AA%25D8%25AC%25D9%2585%25D9%258A%25D8%25B1%2529.zip/file" target="_blank" class="link-card">سيرا ٢٠١٥ تجمير</a>
<a href="https://www.mediafire.com/file/axesmrgyxt49mdl/2025_2%25283%2529.zip/file" target="_blank" class="link-card">سيرا ٢٠٢٥</a>
<a href="https://www.dropbox.com/scl/fi/ziogonph3qfhssr6663nl/N7.zip?rlkey=pvhkwe0i1oc65qndmc7gvre5a&st=tv4oxe3z&dl=1" target="_blank" class="link-card">هايلكس ١٩٩٧</a>
<a href="https://www.mediafire.com/file/i8bx2lzjj5s9d19/Dodge_Charger_SRT_Hellcat_2.zip/file" target="_blank" class="link-card">تشارجر</a>
<a href="https://www.mediafire.com/file/lvbornboukzoo22/Nolimts_Toyota_Hilux_2009-2011_2.zip/file" target="_blank" class="link-card">هايلكس غمارتين ٢٠٠٩-٢٠١١</a>
<a href="https://www.mediafire.com/file/exofs9nqx6w9v9o/tlc200k_2.zip/file" target="_blank" class="link-card">لاند</a>
<a href="https://www.mediafire.com/file/06wou7szoovtzd9/YBANIH-ABOTRK-BULLET_2.zip/file" target="_blank" class="link-card">هايلكس</a>
<a href="https://www.mediafire.com/file/lwaxk57a213rc4m/chevrolet_corvette_c7_2019_2.zip/file" target="_blank" class="link-card">كورفت ٢٠١٩</a>
<a href="https://www.mediafire.com/file/1581b7gzj4jn1rr/kn0z_y61_2.zip/file" target="_blank" class="link-card">فتك</a>
<a href="https://www.mediafire.com/file/cw8yie62o97uipi/vehicles.zip/file" target="_blank" class="link-card">اكسنت ٢٠20</a>
<a href="https://www.mediafire.com/file/ik3p2y1eelos0qh/1998_2.zip/file" target="_blank" class="link-card">لاند ١٩٩٨</a>
<a href="https://www.mediafire.com/file/vudbxfg9pe4ew7s/vehicles.zip/file" target="_blank" class="link-card">كامري ٢٠١٦</a>
<a href="https://www.mediafire.com/file/f90ixgwi24n9zff/2022.zip/file" target="_blank" class="link-card">تورس ٢٠٢٢</a>
<a href="https://www.mediafire.com/file/2s6186lvo7v71ic/abosaad_LX_2009.zip/file" target="_blank" class="link-card">شاص ٢٠٠٩</a>
<a href="https://www.mediafire.com/file/ui6qcaz4tzhrmxq/2025_2.zip/file" target="_blank" class="link-card">شاص ٢٠٢٥</a>
<a href="https://www.mediafire.com/file/ema3cfp6af8p7jx/2001.zip/file" target="_blank" class="link-card">لاند ٢٠٠١</a>
<a href="https://www.mediafire.com/file/2ahf7njdunjlse3/2007_2.zip/file" target="_blank" class="link-card">شاص ٢٠٠٧</a>
<a href="https://www.mediafire.com/file/gz1v2ycsachw6fj/abosaad_LX_2006.zip/file" target="_blank" class="link-card">شاص ٢٠٠٩</a>
<a href="https://www.mediafire.com/file/hgtutg0zs1fb8td/BO_AHMED_LC300.zip/file" target="_blank" class="link-card">لاند</a>
<a href="https://www.mediafire.com/file/8tef9ml8b2vte08/g80.zip/file" target="_blank" class="link-card">جنسس</a>
<a href="https://www.mediafire.com/file/tncf248mx9gs08w/CapriceFrAnSiScO.zip/file" target="_blank" class="link-card">كابرس</a>
<a href="https://www.mediafire.com/file/jtptgb3q94khgdu/Lonley_sierra_23_26.zip/file" target="_blank" class="link-card">سيرا ٢٠٢٥</a>
<a href="https://www.mediafire.com/file/xjibso9xax1yo02/Hyundai_Elantra_2025-2024_%25282%2529.zip/file" target="_blank" class="link-card">الانترا ٢٠٢٥</a>
<a href="https://www.mediafire.com/file/vpzmxjtvscgmpmw/soso_24_%257B_dis__RZH9_%257D_%25281%2529_2.zip/file" target="_blank" class="link-card">سوناتا</a>
<a href="https://www.mediafire.com/file/db7g6m4aqdna3re/SAKU_LEX_2.zip/file" target="_blank" class="link-card">لكزس</a>
<a href="https://www.mediafire.com/file/54ekwy9l8n0ccov/%25D9%258A%25D8%25A7%25D8%25B1%25D8%25B3_%25D9%25A2%25D9%25A0%25D9%25A2%25D9%25A6.zip/file" target="_blank" class="link-card">يارس ٢٠٢٦</a>
<a href="https://www.mediafire.com/file/fy8vqgmskblimef/%25D8%25A7%25D8%25B2%25D9%258A%25D8%25B1%25D8%25A7_%25D9%25A2%25D9%25A0%25D9%25A2%25D9%25A2.zip/file" target="_blank" class="link-card">ازيرا ٢٠٢٢</a>
<a href="https://www.mediafire.com/file/578emc4ckl4cmxs/%25D8%25A1%25D8%25B1%25D9%2586%25D8%25AC_%25D9%25A1.zip/file" target="_blank" class="link-card">رنج</a>
<a href="https://www.mediafire.com/file/ji9z0uh8bqz5e32/%25D8%25A1%25D8%25B1%25D9%2586%25D8%25AC_34.zip/file" target="_blank" class="link-card">رنج</a>
<a href="https://www.mediafire.com/file/o0wfa9x95ivafby/%25D9%2584%25D8%25A7%25D9%2586%25D8%25AF_%25D8%25BA%25D8%25A8%25D9%2586%25D9%2587_2.zip/file" target="_blank" class="link-card">لاند</a>
<a href="https://www.mediafire.com/file/up8chqdmmwln55q/%25D9%2584%25D9%2583%25D8%25B2%25D8%25B3_LS430.zip/file" target="_blank" class="link-card">لكزس</a>
<a href="https://www.mediafire.com/file/vnd4k2sp6ms29h1/DXTR_Caprice_2012.zip/file" target="_blank" class="link-card">كابرس ٢٠١٣</a>
<a href="https://www.mediafire.com/file/26cuv460l0h50hw/Mercedes_Benz_W222_AMG.zip/file" target="_blank" class="link-card">مرسيدس</a>
<a href="https://www.mediafire.com/file/07fo0f85frsxcog/G63_2020_KHwylD_2.zip/file" target="_blank" class="link-card">G63</a>
<a href="https://www.mediafire.com/file/b5vyzb9ose5rc24/w222unl_modland.zip/file" target="_blank" class="link-card">مرسيدس</a>
<a href="https://www.mediafire.com/file/fcv9dww1i9fi9z0/Dodge_Charger_2015-2020_2.zip/file" target="_blank" class="link-card">تشارجر</a>
<a href="https://www.mediafire.com/file/ovqby189j20h18v/ford-mustang-2021-v1-0-0-37-x_1760215977_425972_Pro_Build_v2.1_2025_by_BeamUploader.zip/file" target="_blank" class="link-card">موستنق</a>
<a href="https://www.mediafire.com/file/ndjubh0sc7mio8o/warning_cr_2.zip/file" target="_blank" class="link-card">شاص</a>
<a href="https://www.mediafire.com/file/hzr8u9powu0r7mb/hrh_y61_v1.zip/file" target="_blank" class="link-card">فتك</a>
<a href="https://www.mediafire.com/file/e00fvhctc9epmj4/M7corolla08_12.zip/file" target="_blank" class="link-card">كورلا ٢٠١٢</a>
<a href="https://www.mediafire.com/file/w0ypxra1wgu5lwb/La_K4_2.zip/file" target="_blank" class="link-card">K4</a>
<a href="https://www.mediafire.com/file/tsmosbxgev90fm8/Dodge_Challenger_SRT_Demon_170.zip/file" target="_blank" class="link-card">تشالنجر</a>
<a href="https://www.mediafire.com/file/ztws7gjqn580vdr/Chrysler_300_l5fi.zip/file" target="_blank" class="link-card">كلايزر</a>
<a href="https://www.mediafire.com/file/xk2c0zi59ia3rj1/Cadillac_CT5_V_Blackwing.zip/file" target="_blank" class="link-card">كدلك</a>
<a href="https://www.mediafire.com/file/k6i4b86fym7gmyx/yuckon14.zip/file" target="_blank" class="link-card">يوكن ٢٠١٤</a>
<a href="https://www.mediafire.com/file/a5uj67vo0ccuqy7/WSCX_Dream_Engines_Pack_Full_2.zip/file" target="_blank" class="link-card">مكينه يوكن</a>
<a href="https://www.mediafire.com/file/jdpx8ughxj88vn6/cadenza_2_K__2.zip/file" target="_blank" class="link-card">كدينزا ١٦</a>
<a href="https://www.mediafire.com/file/8b31t9c9l5pd1pf/BGX_cadenza_2018.zip/file" target="_blank" class="link-card">كدينزا ٢٠١٨</a>
<a href="https://www.mediafire.com/file/fpmfbqlywat9saz/Land_Cruiser_Lc70_2025_KHwylD.rar.zip/file" target="_blank" class="link-card">شاص ٢٠٢٥</a>
<a href="https://www.mediafire.com/file/4j8rxbmp2oi9tsb/BdRaN_cr24_2.zip/file" target="_blank" class="link-card">شاص ٢٠٢٤</a>
<a href="https://www.mediafire.com/file/u2rrilcr60jktx4/Land_Cruiser_Lc70_2025_2.zip/file" target="_blank" class="link-card">شاص ٢٠٢٥</a>
<a href="https://www.mediafire.com/file/8qzojiwotedu1tp/azera_2018_sh9.zip/file" target="_blank" class="link-card">ازيرا</a>
<a href="https://www.mediafire.com/file/8ppwomlb7ikoxxg/sh9_y61_v1.zip/file" target="_blank" class="link-card">فتك</a>
<a href="https://www.mediafire.com/file/vmgmtzf3qr2po6q/ali_camry_2.zip/file" target="_blank" class="link-card">كامري ٢٠٠٦</a>
<a href="https://www.mediafire.com/file/1jtiwctnus4uppb/bgx_sonata2024_2.zip/file" target="_blank" class="link-card">سوناتا</a>
<a href="https://www.mediafire.com/file/cxrp36loqrn93u9/Prado_2009_KHwylD_2.zip/file" target="_blank" class="link-card">برادو برادو ٢٠٠٩</a>
<a href="https://www.mediafire.com/file/d2fsrtttuhhoge1/vehicles_2.zip/file" target="_blank" class="link-card">سيرا ٢٠١٢</a>
<a href="https://www.mediafire.com/file/hu28y6hh5syexfy/vehicles.zip/file" target="_blank" class="link-card">سفلرادو ٢٠٠٧</a>
<a href="https://www.mediafire.com/file/ubw7dn1qrshy5bo/taurus_sh9_sko0by_2022.zip/file" target="_blank" class="link-card">تورس ٢٠٢٢</a>
<a href="https://www.mediafire.com/file/ib18e1yxpk10iym/M7_marq03-11.zip/file" target="_blank" class="link-card">ماركيز</a>
<a href="https://www.mediafire.com/file/u9ypt7g8c3mniyz/m7accent.zip/file" target="_blank" class="link-card">اكسنت</a>
<a href="https://www.mediafire.com/file/2weoikdsclxypdr/ford_m7.zip/file" target="_blank" class="link-card">فورد</a>
<a href="https://www.mediafire.com/file/17y50rn7p880c8p/vehicles%25282%2529.zip/file" target="_blank" class="link-card">كامري</a>
<a href="https://www.mediafire.com/file/raz5kaofv7tj9v0/lost_Optima2015_2.zip/file" target="_blank" class="link-card">اوبتما</a>
<a href="https://www.mediafire.com/file/mczl5xnltnhoh42/Sov_Corrola15_2.zip/file" target="_blank" class="link-card">كورلا</a>
<a href="https://www.mediafire.com/file/pvb4jzuvm2dlnck/LC300KEN_DA3S_2.zip/file" target="_blank" class="link-card">لاند</a>
<a href="https://www.mediafire.com/file/2cxwahkik539rqw/L5W_CERATO_SERVER.zip/file" target="_blank" class="link-card">سيراتو ٢٠٢٢</a>
<a href="https://www.mediafire.com/file/hryu3exm9zcttkt/L5FI_Altima_2010_2.zip/file" target="_blank" class="link-card">التيما ٢٠١٠</a>
<a href="https://www.mediafire.com/file/jue51w82cphqdz6/azera22.zip/file" target="_blank" class="link-card">ازيرا ٢٠٢٢</a>
<a href="https://www.mediafire.com/file/j141c466cwpxomr/malibu2015_meto.zip/file" target="_blank" class="link-card">ماليبو ٢٠١٥</a>
<a href="https://www.mediafire.com/file/znfu4iv7xmcl073/qifhilux2005.zip/file" target="_blank" class="link-card">هايلكس ٢٠٠٥</a>
<a href="https://www.mediafire.com/file/h7ellfjfpdezm1k/vehicles%25282%2529.zip/file" target="_blank" class="link-card">اف جي</a>
<a href="https://www.mediafire.com/file/7gpq5ui1557oqo0/2017.zip/file" target="_blank" class="link-card">اكسنت ٢٠١٧</a>
<a href="https://www.mediafire.com/file/uw2nwnze59xdbo9/2014.zip/file" target="_blank" class="link-card">سوناتا ٢٠١٤</a>
<a href="https://www.mediafire.com/file/ckpsr5ybk4yvpte/CQ8_Server_gmc_Clasic_2.zip/file" target="_blank" class="link-card">بهبهاني</a>
<a href="https://www.mediafire.com/file/54fwcohbl3ttmfq/S3o_elantra20.zip/file" target="_blank" class="link-card">الانترا ٢٠٢٠</a>
<a href="https://www.mediafire.com/file/3c9jw17iksvylv2/Sierra.zip/file" target="_blank" class="link-card">سيرا ٢٠٠٦</a>
<a href="https://www.mediafire.com/file/ryc68nem9qn3b22/2007.zip/file" target="_blank" class="link-card">اوريون</a>
<a href="https://www.mediafire.com/file/mx95o0kd4objq4p/2002.zip/file" target="_blank" class="link-card">كامري ٢٠٠٢</a>
<a href="https://www.mediafire.com/file/dhldf19mjujh9e7/2013.zip/file" target="_blank" class="link-card">موستنق ٢٠١٣</a>
<a href="https://www.mediafire.com/file/jn63m63ec2hwit0/2006.zip/file" target="_blank" class="link-card">جمس ٢٠٠٦</a>
<a href="https://www.mediafire.com/file/yjhuh811m0gt9yk/2024.zip/file" target="_blank" class="link-card">سبارك</a>
<a href="https://www.mediafire.com/file/zbc5u02p4cmy4l4/M7_CHARGER13_v2.zip/file" target="_blank" class="link-card">تشارجر ٢٠١٣</a>
<a href="https://www.mediafire.com/file/x3wlf2timgs4km7/2016.zip/file" target="_blank" class="link-card">بيقاس ٢٠١٦</a>
<a href="https://www.mediafire.com/file/3dvjy45l15aa1v6/2006_2.zip/file" target="_blank" class="link-card">لكزس</a>
<a href="https://www.mediafire.com/file/hx2urtwx6rvzelz/bullet_hilux_7t.zip/file" target="_blank" class="link-card">هايلكس ٢٠٠٥ غمارتين</a>
<a href="https://www.mediafire.com/file/421vx9cyxregb83/M7_HILUX16.zip/file" target="_blank" class="link-card">هايلكس غمارتين ٢٠١٦</a>
<a href="https://www.mediafire.com/file/5l0m3g7kb1b5px0/sh9_Camry_12-15.zip/file" target="_blank" class="link-card">كامري ٢٠١٥</a>
<a href="https://www.mediafire.com/file/fb19xopm61afczq/%25D8%25A7%25D9%2594%25D8%25B1%25D8%25B4%25D9%258A%25D9%2581.zip/file" target="_blank" class="link-card">لكزس</a>
<a href="https://www.mediafire.com/file/xhpsywfxhzn8pzb/CAMRY_24_21_sh9_hdyt_al3id.zip/file" target="_blank" class="link-card">كامري ٢٠٢٤</a>
<a href="https://www.mediafire.com/file/z92gbwg4uo3wjy4/%25D8%25A7%25D9%2594%25D8%25B1%25D8%25B4%25D9%258A%25D9%2581_2.zip/file" target="_blank" class="link-card">هايلكس</a>
<a href="https://www.mediafire.com/file/dhjz6w5lb1qqb87/2024.zip/file" target="_blank" class="link-card">الانترا</a>
<a href="https://www.mediafire.com/file/uth7eamrw6zp1jb/sha9_24_Abu_A7med.zip/file" target="_blank" class="link-card">شاص</a>
<a href="https://www.mediafire.com/file/40ai0f6edprhyis/camry_02_Abu_Zarha.zip/file" target="_blank" class="link-card">كامري</a>
<a href="https://www.mediafire.com/file/qyervlz0hfa00az/Tshalee7_Accent_2010_2.zip/file" target="_blank" class="link-card">اكسنت</a>
<a href="https://www.mediafire.com/file/hk9f8a6q3vznzqa/Silverado_2013_KHwylD%25282%2529.zip/file" target="_blank" class="link-card">سفلرادو</a>
<a href="https://www.mediafire.com/file/n368gieyg4xshwh/art.zip/file" target="_blank" class="link-card">حل مشكله صوت المكينه السفلرادو</a>
<a href="https://www.mediafire.com/file/w66i4sq2qwpv845/Camry_2025_KHwylD_2.zip/file" target="_blank" class="link-card">كامري ٢٠٢٥</a>
<a href="https://www.mediafire.com/file/vx5f7znc9ttzz6o/DXTR_caprice_2012_2.zip/file" target="_blank" class="link-card">كابرس ٢٠١٣</a>
<a href="https://www.mediafire.com/file/mttw2sf5lqw33zr/Nissan_Sunny_Sr12.zip/file" target="_blank" class="link-card">صني</a>
<a href="https://www.mediafire.com/file/b796c5wybf89bx6/BANSHEELONLEY_2.zip/file" target="_blank" class="link-card">دباب بانشي</a>
<a href="https://www.mediafire.com/file/gtpmw6o23wnlemv/M7_rio20.zip/file" target="_blank" class="link-card">ريو</a>
<a href="https://www.mediafire.com/file/ch3s59r3uuxigto/chevrolet_corvette_c7_2019.zip/file" target="_blank" class="link-card">كورفت ٢٠١٩</a>
<a href="https://www.mediafire.com/file/nn2057ctx2vpqli/JSD_chrysler_300.zip/file" target="_blank" class="link-card">كلايزر</a>
<a href="https://www.mediafire.com/file/2ji1w8ry6haol57/Dodge_Charger_2015-2020.zip/file" target="_blank" class="link-card">تشالنجر</a>
<a href="https://www.mediafire.com/file/ew20oi47735tqit/Dodge_Charger_2015-2020_2.zip/file" target="_blank" class="link-card">تشارجر</a>
<a href="https://www.mediafire.com/file/w5xhhkfuuu9kaqm/Porsche_911_992_TwiXeR.zip/file" target="_blank" class="link-card">بورش</a>
<a href="https://www.mediafire.com/file/9gsdh5co26tpd3r/escalade.zip/file" target="_blank" class="link-card">كدلك</a>
<a href="https://www.mediafire.com/file/nhk4ifzgbe8q9k9/M7_ddsn1.zip/file" target="_blank" class="link-card">ددسن</a>
<a href="https://www.mediafire.com/file/mhea4scfry96ma6/F150.zip/file" target="_blank" class="link-card">( ١ )F150</a>
<a href="https://www.mediafire.com/file/1epvf6d4cnj7uby/zmvFordF150%25281%2529.zip/file" target="_blank" class="link-card">( ٢ )F150 ضروري تحمل رقم واحد و رقم اثنين</a>
<a href="https://www.mediafire.com/file/zvazha853k9gicl/2_K_tahoe2025_2.zip/file" target="_blank" class="link-card">تاهو ٢٠٢٥</a>
<a href="https://www.mediafire.com/file/yc50cw998d1wf82/kn0z_y61_2.zip/file" target="_blank" class="link-card">فتك</a>
<a href="https://www.mediafire.com/file/rqgpwcmaeyobjvp/liwa_Y60_2.zip/file" target="_blank" class="link-card">فتك</a>
<a href="https://www.mediafire.com/file/uomlm2zf7lhqshd/patrol62_ALD.zip/file" target="_blank" class="link-card">باترول</a>
<a href="https://www.mediafire.com/file/jfyw6afrclkaxi8/kn0z_y61_03_2003_2.zip/file" target="_blank" class="link-card">فتك</a>
<a href="https://www.mediafire.com/file/qks6xy2s0ov6fs1/vehicles.zip/file" target="_blank" class="link-card">تاهو</a>
<a href="https://www.mediafire.com/file/xz61gj2a6yq5wpr/yaris17.zip/file" target="_blank" class="link-card">يارس ٢٠١٧</a>
<a href="https://www.mediafire.com/file/apxtqylx5ihagec/CAMRY_2004_SH9_V1.zip/file" target="_blank" class="link-card">كامري</a>
<a href="https://www.mediafire.com/file/krsaat0gg23woxy/Crash_GMC.zip/file" target="_blank" class="link-card">بهبهاني</a>
<a href="https://www.mediafire.com/file/j2e2drqbb7c4aw7/17silv.zip/file" target="_blank" class="link-card">سفلرادو ٢٠١٤</a>
<a href="https://www.mediafire.com/file/usjfw2hxwyr8yn4/Soma_Nissan_Datsun.zip/file" target="_blank" class="link-card">ددسن</a>
<a href="https://www.mediafire.com/file/wqdcju3y4zreyfr/Toyota_avalon_2014_Bader.zip/file" target="_blank" class="link-card">افلون ٢٠١٤</a>
<a href="https://www.mediafire.com/file/fpb1xqmbtv55i8p/Range_Rover.zip/file" target="_blank" class="link-card">رنج</a>
<a href="https://www.mediafire.com/file/25qjqtsr0cpxy5y/Lexus_SC300.zip/file" target="_blank" class="link-card">SC300 لكزس</a>
<a href="https://www.mediafire.com/file/aqnc1bwd9kzdcrl/land_cruiser_j100.zip/file" target="_blank" class="link-card">لاند</a>
<a href="https://www.mediafire.com/file/elz87xxu9ki6ska/overtimeperf_charger1.5V5_UNZIP_%25281%2529_2.zip/file" target="_blank" class="link-card">تشارجر</a>
<a href="https://www.mediafire.com/file/g0lb6eve7kleibh/Avalon22ByFahadAndTurki.zip/file" target="_blank" class="link-card">افلون ٢٠٢٢</a>
<a href="https://www.mediafire.com/file/8s4rlgax9d1o9n3/M7_accentV2.zip/file" target="_blank" class="link-card">اكسنت ٢٠١٧</a>
<a href="https://www.mediafire.com/file/xauc94p0gbxgkkt/soso24.zip/file" target="_blank" class="link-card">سوناتا ٢٠٢٤</a>
<a href="https://www.mediafire.com/file/9bhp9l5x9ekjajn/chives_beta_dodge_charger_v2.zip/file" target="_blank" class="link-card">تشارجر</a>
<a href="https://www.mediafire.com/file/y5lfu6xnap0txpj/vehicles.zip/file" target="_blank" class="link-card">مرسيدس ٢٠٢٢</a>
<a href="https://www.mediafire.com/file/cgssagt7ocy8i3g/ali_nissan_ddsen_1_cab_2.zip/file" target="_blank" class="link-card">ددسن</a>
<a href="https://www.mediafire.com/file/tgppy8rjs7couxp/vehicles%25282%2529.zip/file" target="_blank" class="link-card">كلايزر</a>
<a href="https://www.mediafire.com/file/b2gc6a2relyup0q/M7private_avalon.zip/file" target="_blank" class="link-card">افلون ٢٠١٠</a>
<a href="https://www.mediafire.com/file/1ivx9y1b2znex62/Land_Cruiser_LC70_70y_KHwylD.zip/file" target="_blank" class="link-card">شاص</a>
<a href="https://www.mediafire.com/file/vdoz30ysydciwxl/vehicles.zip/file" target="_blank" class="link-card">مرسيدس</a>
<a href="https://www.mediafire.com/file/6qpkhd3uqbfpq7y/k1ng_y61.zip/file" target="_blank" class="link-card">فتك</a>
<a href="https://www.mediafire.com/file/3r8fve4gn6j6zie/vehicles_2.zip/file" target="_blank" class="link-card">G63</a>
<a href="https://www.mediafire.com/file/gwl4hwqcw43dp8h/Tshalee7_Caprice.zip/file" target="_blank" class="link-card">كابرس ٢٠٠٧ - ٢٠١٦</a>
<a href="https://www.mediafire.com/file/epu4t9jngmhhxo5/camry_2018.zip/file" target="_blank" class="link-card">كامري مرور ٢٠١٨</a>
<a href="https://www.mediafire.com/file/xxpy38tqfgaq7mt/3tb_Hyndai_sonata_2018_2.zip/file" target="_blank" class="link-card">سوناتا ٢٠١٨</a>
<a href="https://www.mediafire.com/file/y9kn7jhayes427b/vehicles%25283%2529.zip/file" target="_blank" class="link-card">باترول ٢٠٢٥</a>
<a href="https://www.mediafire.com/file/990h9429wdhhcae/Sierra_2013_Crash_2.zip/file" target="_blank" class="link-card">سيرا ٢٠١٣</a>
<a href="https://www.mediafire.com/file/vehghvb8xolh7fs/hyundai_azera_21-23-SH9.zip/file" target="_blank" class="link-card">ازيرا ٢٠٢٢</a>
<a href="https://www.mediafire.com/file/rfzyh2iu1sl952f/Elantra_2015_2.zip/file" target="_blank" class="link-card">الانترا ٢٠١٥</a>
<a href="https://www.mediafire.com/file/mor0c945yhwxy8f/vehicles_2.zip/file" target="_blank" class="link-card">كامري ٢٠٠٢</a>
<a href="https://www.mediafire.com/file/rgeb7gbwpqdq32l/BoDuaij_Silverado13.zip/file" target="_blank" class="link-card">سفلرادو ٢٠١٣</a>
<a href="https://www.mediafire.com/file/uoz884238vwiqba/BoDuaij_F150.zip/file" target="_blank" class="link-card">2019 F150</a>
<a href="https://www.mediafire.com/file/h4wi28rl1w0a9im/Almutairi_Land_LC70.zip/file" target="_blank" class="link-card">شاص</a>
<a href="https://www.mediafire.com/file/wnt1feb1fgp58sd/meowtahoe.zip/file" target="_blank" class="link-card">تاهو</a>
<a href="https://www.mediafire.com/file/z4xaq5qhfdmpvv2/Crash_j70_2007.zip/file" target="_blank" class="link-card">شاص</a>
<a href="https://www.mediafire.com/file/epaoc52jffbdblf/3tb_kia_optima_2015.zip/file" target="_blank" class="link-card">اوبتما ٢٠١٥</a>
<a href="https://www.mediafire.com/file/2018t2fr3b4rdrr/W223BB_2.zip/file" target="_blank" class="link-card">مرسيدس زحف</a>
<a href="https://www.mediafire.com/file/9cavq2hzxb2pchu/506W_Hilux15_double_2.zip/file" target="_blank" class="link-card">عليلكس غمارتين ٢٠١٢-٢٠١٥</a>
<a href="https://www.mediafire.com/file/q1cdtp57a0qsvwi/accent_24-25_SH9_7t.zip/file" target="_blank" class="link-card">الاكسنت ٢٠٢٥</a>
<a href="https://www.mediafire.com/file/x7y8vcinbtdjl88/LX570_2017_KHwylD_2.zip/file" target="_blank" class="link-card">لكزس خويلد</a>
<a href="https://www.mediafire.com/file/5s0b90xqu48uzvu/Sonata_2010_AboRme7_2.zip/file" target="_blank" class="link-card">سوناتا ٢٠١٠</a>
<a href="https://www.mediafire.com/file/83q982eg71c8fgs/McLeod_Ddsn_2016%25282%2529.zip/file" target="_blank" class="link-card">ددسن غمارتين ٢٠٠٨-٢٠١٦</a>
<a href="https://www.mediafire.com/file/rrk66t9lppx4637/AltimaFrAnSiScO.zip/file" target="_blank" class="link-card">الاتيما ٢٠٢٢ حصريه</a>
<a href="https://www.mediafire.com/file/ddm9rpy9dpxxqeg/Echo_Team_cruze_2026.zip/file" target="_blank" class="link-card">كروز ٢٠٢٦</a>
<a href="https://www.mediafire.com/file/qp9topoupr1nfwn/Alve_Team_Accord_08_-_12.zip/file" target="_blank" class="link-card">اكورد ٢٠٠٨-٢٠١٢</a>
<a href="https://www.mediafire.com/file/le19d9o52e8gjpi/M7_CHARGER13.zip/file" target="_blank" class="link-card">تشارجر ٢٠١٣</a>
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
