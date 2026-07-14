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

# 2. الواجهة المباشرة وبها كافة المودات والمابات مرتبة بأقسامها الأصلية
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
            padding: 50px 20px;
        }
        @media print { body { display: none; } }
        
        .container {
            max-width: 500px;
            margin: 0 auto;
            background-color: #1f2833;
            padding: 30px;
            border-radius: 10px;
            border: 1px solid #45f3ff;
            box-shadow: 0 0 15px rgba(69, 243, 255, 0.2);
        }
        h2 { color: #45f3ff; margin-bottom: 25px; }
        
        /* عناوين الأقسام داخل قائمة التحميل */
        .section-title {
            color: #45f3ff;
            font-size: 18px;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-bottom: 5px;
            border-bottom: 2px dashed #45f3ff;
            text-align: right;
            font-weight: bold;
        }
        
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
        button:hover { 
            background-color: #1f2833; 
            color: #45f3ff; 
            border: 1px solid #45f3ff; 
        }
        
        .error { color: #ff3333; margin: 15px 0; font-weight: bold; }
        .success { color: #00ff00; margin: 15px 0; font-weight: bold; }
        p { font-size: 14px; line-height: 1.6; }
        
        /* تصميم أزرار المودات */
        .link-card {
            display: block;
            background: #0b0c10;
            color: #ffffff;
            padding: 12px;
            margin: 8px 0;
            border-radius: 5px;
            text-decoration: none;
            font-weight: 500;
            text-align: right;
            border: 1px solid #1f2833;
            transition: 0.3s;
            font-size: 14px;
        }
        .link-card:hover {
            border-color: #45f3ff;
            background: #1f2833;
            color: #45f3ff;
            box-shadow: 0 0 8px rgba(69, 243, 255, 0.3);
        }
        .logout-btn {
            display: inline-block;
            margin-top: 30px;
            color: #ff3333;
            text-decoration: none;
            font-size: 14px;
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
        <h2>🔒 بوابة المودات الخاصة | N7L STORE</h2>
        
        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}

        {% if not logged_in %}
            {% if not step_two %}
                <!-- خطوة 1: إدخال الآيدي للتحقق -->
                <form action="/login_step1" method="POST">
                    <p>أدخل آيدي التليجرام الخاص بك لتلقي رمز التحقق (OTP)</p>
                    <input type="text" name="user_id" placeholder="مثال: 5432340735" required autocomplete="off">
                    <button type="submit">إرسال كود التحقق</button>
                </form>
            {% else %}
                <!-- خطوة 2: تأكيد الرمز -->
                <form action="/login_step2" method="POST">
                    <p class="success">📩 أرسلنا كود التحقق إلى حسابك في تليجرام.</p>
                    <input type="text" name="otp_code" placeholder="أدخل كود التحقق (OTP)" required autocomplete="off">
                    <button type="submit">تأكيد ودخول</button>
                </form>
            {% endif %}
        {% else %}
            <p class="success">🎉 تم التحقق بنجاح! حمل المودات من الروابط أدناه:</p>
            
            <!-- ================= قسم المواتر (السيارات) ================= -->
            <div class="section-title">._المواتر (السيارات)_. 🚘</div>
            <a href="https://www.dropbox.com/scl/fi/j4v4ssvcfh18bfiftszof/Optima_2019_KHwylD.zip?rlkey=4xkvmcpac711khtenp60v4ysk&st=0nskr6jk&dl=1" target="_blank" class="link-card">🚘 اوبتما ٢٠١٩ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/esm2hbzq6ip66obfevcog/Camry_2021_KHwylD.zip?rlkey=upbfz1cy0knmm7maax39joq8w&st=pd4w2rpa&dl=1" target="_blank" class="link-card">🚘 كامري ٢٠٢١ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/m8mfrvjbdm87cisnp7vxi/Camry_2005_KHwylD.zip?rlkey=6k2xk7adc5oxd1381ysxe1rdy&st=xyxcius1&dl=1" target="_blank" class="link-card">🚘 كامري ٢٠٠٥ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/j6lnurcqyv0fj8vc81cnw/Cruze_2017_KHwylD.zip?rlkey=9uvvcst8pxqpzowmx9p93t76m&st=ah4d77gs&dl=1" target="_blank" class="link-card">🚗 كروز ٢٠١٧ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/km3j5tw8bnt99ebngvqum/Ddsn_2016_KHwylD.zip?rlkey=r4kg0mln6s8cwhj5vhun4mayx&st=nlloh4cl&dl=1" target="_blank" class="link-card">🛻 ددسن ٢٠١٦ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/12jvs85pq3mx58mxhdwqr/Hilux_2011_KHwylD-2.zip?rlkey=n1oyx9498iry5sffe40lauj1l&st=qi1alrmb&dl=1" target="_blank" class="link-card">🛻 هايلكس ٢٠١١ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/v0adyryue04uzo06b980n/Caprice_2013_KHwylD.zip?rlkey=u5ugflyib2dl2f3pzswr1vp6g&st=g3rj4dvc&dl=1" target="_blank" class="link-card">🚘 كابرس ٢٠١٣ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/k5ufh18eaezsoxiqbqyx0/Hyundai_Sonata_2024_KHwylD.zip?rlkey=7toa2wa4kyjo86qonukbuffdt&st=2ha3kmbi&dl=1" target="_blank" class="link-card">🏎️ موستنق ٢٠١٣ - ملف سوناتا ٢٠٢٤ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/0478q72dbrktsaz3rlhry/Camry_2002_KHwylD.zip?rlkey=56visngmrootvm91y57nzvilx&st=bcl7bs84&dl=1" target="_blank" class="link-card">🚘 كامري ٢٠٠٢ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/7epbdkry8xeqawecpn82t/Charger_SXT_2015.zip?rlkey=4iyge0392ix40f7mnzhtnwa86&st=4xij7360&dl=1" target="_blank" class="link-card">🚘 دوج ٢٠١٥ SXT ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/662aplwyep9clrsh0zbfq/Land_Cruiser_j70_70Y_KHwylD.zip?rlkey=lgw4r3xj3pn65wmi0zp7f49al&st=xrv5s9lh&dl=1" target="_blank" class="link-card">🚙 ربع السبعين عام ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/1ainm03f2uku7vjxhwdqp/Maxima_1999_KHwylD.zip?rlkey=qqevdrh4p3byi3wxbvarzwzur&st=607mukr4&dl=1" target="_blank" class="link-card">🚘 مكسيما ١٩٩٩ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/kfkdfzlxwjkxbmge7x419/Hilux_2016_KHwylD.zip?rlkey=ec1v7wi89np2kzeqeyuzj0zb3&st=2qayku61&dl=1" target="_blank" class="link-card">🛻 هايلكس ٢٠١٦ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/e90zb1ke9m62sgr9rod34/Sunny_2024_KHwylD.zip?rlkey=2vktjxh1s5thrvkifwxqxl23b&st=untcmlfx&dl=1" target="_blank" class="link-card">🚘 صني ٢٠٢٤ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/14ywnlaxdgew2bkn1q1pi/Yaris_2015_KHwylD.zip?rlkey=i9oaofj79anou9o13uascdf5z&st=pg8w9p3j&dl=1" target="_blank" class="link-card">🚘 يارس ٢٠١٥ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/39regxwtb4pswnfyhjyad/RB3_2024_KHwylD.zip?rlkey=k61qun8h0vdy5sd89i897zxik&st=fwdcusjm&dl=1" target="_blank" class="link-card">🚙 ربع ٢٠٢٤ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/62o83rfle8u2r1wnu6tz0/Land_Cruiser_j70_2023_KHwylD.zip?rlkey=47vonf2k90mdh0hr6ec4eb9lv&st=t3rx0hd1&dl=1" target="_blank" class="link-card">🚙 ربع ٢٠٢٣ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/zni6z2ib77wcyexa7pvby/Altima_2009_KHwylD.zip?rlkey=o45nek8ucojlxwg692fim96qr&st=qkf8lymq&dl=1" target="_blank" class="link-card">🚘 التيما ٢٠٠٩ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/88hfy954ux8shh0f6k4oq/Sonata_2017_KHWYLD.zip?rlkey=8ntga8bvmuxs0mab17mstv14y&st=pxul0dn5&dl=1" target="_blank" class="link-card">🚘 سوناتا ٢٠١٧ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/ie55iuc5dajaxzwc9pr1u/Camry_2011_KHwylD.zip?rlkey=tjhyornagwreqyglpjqybc3n2&st=u80usjy2&dl=1" target="_blank" class="link-card">🚘 كامري ٢٠١١ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/hcd0uzfj8tfl4sjs4kwsr/Camey-2025.zip?rlkey=yduow0d8h62sb753mchna25m1&st=25w1yurq&dl=1" target="_blank" class="link-card">🚘 كامري ٢٠٢٥ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/mnnj43vg97a8mpvflnc3o/G63_2020_KHwylD.zip?rlkey=njvcev52s2m6yc73oehs2gxd6&st=e75vvhvc&dl=1" target="_blank" class="link-card"> SUV جي كلاس ٢٠٢٠ G63 ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/y2282mdikjt7a3j5o6149/Caprice-SS-2013.zip?rlkey=y7omygziqn8ozsi9gxt0apwxt&st=xpfa6w2r&dl=1" target="_blank" class="link-card">🚘 كابرس ٢٠١٣ ss ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/t5jquk333jrklxu7cezya/LEXUS-LX470.zip?rlkey=933lyqtkuw84izyshtwchy7p7&st=hnxqpy7s&dl=1" target="_blank" class="link-card">🚘 لكزز LX400 ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/acd5h4jg27gre1fwg0901/Land_Cruiser_LC70_70y.zip?rlkey=cq6bkr02zhiqijkkbbh042ail&st=34fs2neo&dl=1" target="_blank" class="link-card">🛻 شاص السبعين عام ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/z8dd090sivjt0czqhsuic/Land_Cruiser_1998_KHwylD.zip?rlkey=1pejyi2km1e8wj1y2grnvehhn&st=8lqtq35e&dl=1" target="_blank" class="link-card">🚙 لاندكروزر ١٩٩٨ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/77quv86zcjawpcbtbf47i/yuckon14.zip?rlkey=gt8oa4jwpi64m1gmoou51tp96&st=0f6uvznw&dl=1" target="_blank" class="link-card">🚙 جمس ٢٠١٤ ( خويلد )</a>
            <a href="https://www.dropbox.com/scl/fi/no5ecpoe0qflobgpwxt1x/Fortuner-15-By-Ray.zip?rlkey=h31ukbj6jd3e3bb6mtjzhttng&st=a5vejtae&dl=1" target="_blank" class="link-card">🚙 فورتشنر ٢٠١٥ ( خويلد )</a>
            <a href="https://www.mediafire.com/file/fpmfbqlywat9saz/Land_Cruiser_Lc70_2025_KHwylD.rar.zip/file" target="_blank" class="link-card">🛻 شاص ٢٠٢٥ ( خويلد )</a>
            <a href="https://www.mediafire.com/file/dqhdoa078733hx1/Prado_2009_KHwylD.zip/file" target="_blank" class="link-card">🚙 برادو ٢٠٠٩ - رابط 1 ( خويلد )</a>
            <a href="https://www.mediafire.com/file/cxrp36loqrn93u9/Prado_2009_KHwylD_2.zip/file" target="_blank" class="link-card">🚙 برادو ٢٠٠٩ - رابط 2 مكرر ( خويلد )</a>
            <a href="https://www.mediafire.com/file/x7y8vcinbtdjl88/LX570_2017_KHwylD_2.zip/file" target="_blank" class="link-card">🚘 لكزس خويلد</a>
            <a href="https://www.mediafire.com/file/07fo0f85frsxcog/G63_2020_KHwylD_2.zip" target="_blank" class="link-card">SUV G63 خويلد</a>

            <!-- ================= قسم مودات لوست (LOST) ================= -->
            <div class="section-title">._مودات لوست (LOST)_. 💎</div>
            <a href="https://www.dropbox.com/scl/fi/4zikxfi3qkqw9izbk0xem/LOST_caprice13.zip?rlkey=8dbrzyz6j1a5hbwvelu0j7a87&st=29b0oc63&dl=1" target="_blank" class="link-card">🚘 كابرس (لوست)</a>
            <a href="https://www.dropbox.com/scl/fi/md8sh5irioz5msqjv034r/camry2004_lost.zip?rlkey=6bvx70v5j887ujnje0228sykt&st=nqn4gzef&dl=1" target="_blank" class="link-card">🚘 كامري ٢٠٠٤ (لوست)</a>
            <a href="https://www.dropbox.com/scl/fi/pnnwk8e1ydpwbfnw2wkqc/lost_cadenza.zip?rlkey=1sldsr25dvoqbf0ibc6xpv74c&st=dopr9t51&dl=1" target="_blank" class="link-card">🚘 كدينزا ٢٠١٦ (لوست)</a>
            <a href="https://www.mediafire.com/file/o7akqx9kc7t18ll/lost_Optima2015.zip/file" target="_blank" class="link-card">🚘 اوبتيما ٢٠١٥ (لوست)</a>

            <!-- ================= قسم مودات بدران (BdRaN) ================= -->
            <div class="section-title">._مودات بدران (BdRaN)_. 💎</div>
            <a href="https://www.dropbox.com/scl/fi/frnb0vslgfy72o2xxnqei/BdRaN_Lx570.zip?rlkey=yc2leoai9mwd98mrnwqo42m2p&st=u3f2g4kd&dl=1" target="_blank" class="link-card">🚘 لكزس (بدران)</a>
            <a href="https://www.mediafire.com/file/oyiw4megk8ylilh/BdRaN_cr24.zip/file" target="_blank" class="link-card">🛻 شاص ٢٠٢٤ - رابط 1 (بدران)</a>
            <a href="https://www.mediafire.com/file/4j8rxbmp2oi9tsb/BdRaN_cr24_2.zip/file" target="_blank" class="link-card">🛻 شاص ٢٠٢٤ - رابط 2 (بدران)</a>
            <a href="https://www.dropbox.com/scl/fi/hkrk5rbjpo5zt083o5n6v/BdRaN_Land_2016-2021.zip?rlkey=qcmwdju7f7vg2s2x31zlv09g2&st=js0mciwb&dl=1" target="_blank" class="link-card">🚙 لاندكروزر ٢٠١٦-٢٠٢١ (بدران)</a>
            <a href="https://www.dropbox.com/scl/fi/bparxmhrxptyg8q3ticmu/Toyota_Hilux_2015_2012_Badr_AN.zip?rlkey=w6u0uoffkjotiuuczdl49jka8&st=k1uxnm28&dl=1" target="_blank" class="link-card">🛻 هايلكس ٢٠١٢-٢٠١٥ (بدران)</a>
            <a href="https://www.mediafire.com/file/smtok7q0hnhdzas/LC200_BdRaN.zip/file" target="_blank" class="link-card">🚙 لاندكروزر LC200 (بدران)</a>
            <a href="https://www.dropbox.com/scl/fi/4hx3jtsmvxdtharyiw6u9/Land-Off-Road.zip?rlkey=lha0l8vju910qgmupjczq92zp&st=z6lpcrdz&dl=1" target="_blank" class="link-card">⛰️ لاند اوف رود (بدران)</a>

            <!-- ================= قسم مودات راي (Ray) ================= -->
            <div class="section-title">._مودات راي (Ray)_. 💎</div>
            <a href="https://www.dropbox.com/scl/fi/08gfc5bygjl7f1fvxj2rd/Camry-2025-By-Ray.zip?rlkey=kn27lngxdppt0zz07bnxq9o4i&st=m96ge9ds&dl=1" target="_blank" class="link-card">🚘 كامري ٢٠٢٥ سري (راي)</a>
            <a href="https://www.dropbox.com/scl/fi/2mhgnb1834mjdd2qcnedc/Yaris_Ray_2026.zip?rlkey=o4z16amif08m3d0zqbj52stxg&st=deducbmd&dl=1" target="_blank" class="link-card">🚘 يارس ٢٠٢٦ (راي)</a>
            <a href="https://www.dropbox.com/scl/fi/98r1spke95a43qvpbo3zs/Monza_Ray_23.zip?rlkey=we8cftw90aufdkw4ou5rwwkf2&st=bp7sel38&dl=1" target="_blank" class="link-card">🚗 كروز ٢٠٢٦ (راي)</a>
            <a href="https://www.dropbox.com/scl/fi/vw4z4aj4vp5bsfmdfikj8/Camry_Ray_2011.zip?rlkey=og9z18t0c981bfmsywxps2oq4&st=s56kvslp&dl=1" target="_blank" class="link-card">🚘 كامري ٢٠٠٨-٢٠١١ (راي)</a>
            <a href="https://www.dropbox.com/scl/fi/qrdjjhzydldmw6kqprpxl/Hilux-2012-2015-Ray.zip?rlkey=r4m64h8tnf4actnmo1247xu16&st=hvdskrvv&dl=1" target="_blank" class="link-card">🛻 هايلكس ٢٠١٢-٢٠١٥ (راي)</a>
            <a href="https://www.dropbox.com/scl/fi/zz1onc2a34e4ey6padtvk/LAND-1998-2007-Ray.zip?rlkey=k9by8qvyi16ueifafebose3aa&st=z35w0a8v&dl=1" target="_blank" class="link-card">🚙 لاندكروزر خويلد ١٩٩٨-٢٠٠٧ (راي)</a>
            <a href="https://www.dropbox.com/scl/fi/p9gzvwkjlqaklmwdekn17/Taurus-2023-Ray.zip?rlkey=v1m9xo59jiq2bagn6thz9gxdl&st=98we6218&dl=1" target="_blank" class="link-card">🚘 تورس ٢٠٢٣ (راي)</a>
            <a href="https://www.dropbox.com/scl/fi/ofbprn62cttq6upf8g4hf/BMW-PACK-By-Ray.zip?rlkey=jdtctd0vnam3zky768hqk2yc1&st=i9jt3nfo&dl=1" target="_blank" class="link-card">📦 بكج بي ام (راي)</a>
            <a href="https://www.dropbox.com/scl/fi/fcb3c8f8bnt5bmu7bdf9o/Sierra-17-15-By-Ray.zip?rlkey=3m5dkyp253t3w2utsttv3z4a0&st=3o8yx6xd&dl=1" target="_blank" class="link-card">🛻 سيرا (راي)</a>
            <a href="https://www.dropbox.com/scl/fi/xtbp8pt68xvgiunk4hyqv/Kia-Cadenza-By-Ray.zip?rlkey=1t3rgtfmr2tloct4are79aopt&st=89xaxdyq&dl=1" target="_blank" class="link-card">🚘 كدينزا ١٦ (راي)</a>
            <a href="https://www.dropbox.com/scl/fi/b9fumjqitiky8kxd1sn8a/LX600_Ray.zip?rlkey=fypvzj7x28hdmbsqjmg3m6033&st=t3newrw6&dl=1" target="_blank" class="link-card">🚘 لكزس ٢٠٢٥ (راي)</a>
            <a href="https://www.mediafire.com/file/ni8o32kymozuyi8/Elantra_19_Ray.zip/file" target="_blank" class="link-card">🚘 الانترا ٢٠١٩ (راي)</a>
            <a href="https://www.dropbox.com/scl/fi/fi5zh4g87jlqdwes54al9/Dodge-Saudi-Police-Pack-Ray.zip?rlkey=saeigshobwbjpuutm9xygab7o&st=sthv49o0&dl=1" target="_blank" class="link-card">🚓 دوج دورية (راي)</a>

            <!-- ================= قسم تويوتا (Toyota) المتنوعة ================= -->
            <div class="section-title">._بقية المواتر المتنوعة - تويوتا (Toyota)_. 🚘</div>
            <a href="https://www.dropbox.com/scl/fi/c5q21uf1v4d4ylo1dxfp8/ENF_Aurion_2016.zip?rlkey=fd0rmkuia3fwolklvahtky3wy&st=pdcpkwcn&dl=1" target="_blank" class="link-card">🚘 أوريون ٢٠١٦</a>
            <a href="https://www.dropbox.com/scl/fi/l8dzd4lvgmzioui8fgj0i/Corolla_2024_NaF.zip?rlkey=0dgz9klzy9rwb297ges8kqxwv&st=cuy6vbyb&dl=1" target="_blank" class="link-card">🚘 كورلا ٢٠٢٤ - رابط 1</a>
            <a href="https://www.dropbox.com/scl/fi/7r4l3wibilh7np4t8uyyr/Corolla_2024_KHwylD.zip?rlkey=x60k7lljqu0dy1w0ywhdjgn2c&st=n2vusali&dl=1" target="_blank" class="link-card">🚘 كورلا ٢٠٢٤ - رابط 2</a>
            <a href="https://www.dropbox.com/scl/fi/mhbw0487g2far67wix0xk/Meto-corolla.zip?rlkey=3ninvm3s5j5mmvdrzmgaqevhp&st=hy45dfqv&dl=1" target="_blank" class="link-card">🚘 كورلا ٢٠٢٠ - رابط 1</a>
            <a href="https://www.dropbox.com/scl/fi/uyjugeamt2zq348i23px7/corolla-by-ray.zip?rlkey=6ywpt04g0fkhbo7reiwzwxdvv&st=762yf9hs&dl=1" target="_blank" class="link-card">🚘 كورلا ٢٠٢٠ - رابط 2</a>
            <a href="https://www.dropbox.com/scl/fi/1xectqjl5g7ysq6gevkxk/M7_camry2007.zip?rlkey=xr4ftlscgfyu8u2d8rworgywe&st=1oz1ux4z&dl=1" target="_blank" class="link-card">🚘 كامري ٢٠٠٧</a>
            <a href="https://www.dropbox.com/scl/fi/pvwinaqawpy79va2qlj7a/Hilux-V1.zip?rlkey=26llzggblludeixojabxnmpz7&st=j4crwewj&dl=1" target="_blank" class="link-card">🛻 هايلكس غمارتين</a>
            <a href="https://www.dropbox.com/scl/fi/aeqrn9oohlfsdzqjqu798/Hilux_2015.zip?rlkey=7n4aaucynqfyzmxuxc8mei9o2&st=zcnbt93t&dl=1" target="_blank" class="link-card">🛻 هايلكس غمارة</a>
            <a href="https://www.dropbox.com/scl/fi/j5wd19poyxux7a033o0pd/GRYaris.zip?rlkey=p4o9x6c5e19a4tfifrkvp5s7v&st=atxz8q4f&dl=1" target="_blank" class="link-card">🚘 يارس سبورت GR</a>
            <a href="https://www.dropbox.com/scl/fi/p36asphg5hfa8plh1ku64/Camry-2003-2006.zip?rlkey=nwfnj5rnzx6io8j2112h8jjy6&st=1zjczmvr&dl=1" target="_blank" class="link-card">🚘 كامري ٢٠٠٣-٢٠٠٦</a>
            <a href="https://www.dropbox.com/scl/fi/uf19vptval5tb3il88j9v/Camry_24_Abu_Zarha.zip?rlkey=4d9ov1zhd2bb07p40cyj9vbjc&st=vtsevex9&dl=1" target="_blank" class="link-card">🚘 كامري ٢٠٢٤ - رابط أبو جرحة</a>
            <a href="https://www.mediafire.com/file/xhpsywfxhzn8pzb/CAMRY_24_21_sh9_hdyt_al3id.zip/file" target="_blank" class="link-card">🚘 كامري ٢٠٢٤ - رابط sh9 عيد</a>
            <a href="https://www.dropbox.com/scl/fi/tvwy2mjvjvrzktomfzcql/Camry-XV70-V2.5.zip?rlkey=yarhgza9zu7vwf4awx0yl0fxh&st=bjpb9oh8&dl=1" target="_blank" class="link-card">🚘 كامري ٢٠٢٣</a>
            <a href="https://www.mediafire.com/file/ddzo75c33zz4k99150lqi/camry2025_modland.zip" target="_blank" class="link-card">🚘 كامري ٢٠٢٥ - رابط 1</a>
            <a href="https://www.mediafire.com/file/izvw50o92wv7m4ob63acr/Camry-2025-1.zip" target="_blank" class="link-card">🚘 كامري ٢٠٢٥ - رابط 2</a>
            <a href="https://www.mediafire.com/file/w66i4sq2qwpv845/Camry_2025_KHwylD_2.zip/file" target="_blank" class="link-card">🚘 كامري ٢٠٢٥ - رابط خويلد</a>
            <a href="https://www.dropbox.com/scl/fi/nmlyi0ssi1wc16pyf20pn/Hilu16.zip?rlkey=xfe0cd0oxdnv9cqx1ugqpppcj&st=v8mn0knn&dl=1" target="_blank" class="link-card">🛻 هايلكس ٢٠١٦</a>
            <a href="https://www.dropbox.com/scl/fi/8utp8ffvrja75mm7rcq1s/land-2007_1999.zip?rlkey=lp19ojzl5yxxsspgpp9hs30h3&st=6ug04oos&dl=1" target="_blank" class="link-card">🚙 لاندكروزر ٢٠٠٦</a>
            <a href="https://www.dropbox.com/scl/fi/p9ckyuonufm78keek4nid/CAMRY_LA9_7T.zip?rlkey=lkp8tcgf33kd19tnhjxwnuju6&st=q1flg6f3&dl=1" target="_blank" class="link-card">🚘 كامري ٢٠٢٠ - ٢٠٢٤</a>
            <a href="https://www.dropbox.com/scl/fi/m867djbbqaxf64qjnf5x6/Yaris-2020-2021.zip?rlkey=adn0s561xh04jrjzkkfhowo8v&st=0bnbdy6v&dl=1" target="_blank" class="link-card">🚘 يارس ٢٠٢٠ - ٢٠٢١</a>
            <a href="https://www.dropbox.com/scl/fi/u4rzv69icso0z5nbupgwp/tlc200k.zip?rlkey=6sw90w71ol91knsticvq9hqq7&dl=1" target="_blank" class="link-card">🚙 لاندكروزر ٢٠٢٠</a>
            <a href="https://www.dropbox.com/scl/fi/5iuqz9622t2c99umq73w0/Camry-2018.zip?rlkey=37tdbogq3jlug48dmlwxe6zm7&st=y62t89v4&dl=1" target="_blank" class="link-card">🚘 كامري ٢٠١٨</a>
            <a href="https://www.dropbox.com/scl/fi/9iv8u2pjxsm7f550a3hp9/FJ22-RAY.zip?rlkey=z3rf58957x40d9vj0eycurh7v&st=y04zsot3&dl=1" target="_blank" class="link-card">🚙 اف جي</a>
            <a href="https://www.dropbox.com/scl/fi/690vov1pjrtu4wyqn0smr/lc300.zip?rlkey=8ybwcp82rai1b3vabtcc7y715&st=7m75evjh&dl=1" target="_blank" class="link-card">🚙 لاند lc300</a>
            <a href="https://www.dropbox.com/scl/fi/a7sjg2ngkey7hiscll2eo/Land-Cruiser-2022.zip?rlkey=pt2dsn2ox3qp7u1j50ebcnr1z&st=90e168ku&dl=1" target="_blank" class="link-card">🚙 لاند ٢٠٢٢</a>
            <a href="https://www.dropbox.com/scl/fi/ygjxgsew4wl0du2197sx2/Avalon22ByFahadAndTurki.zip?rlkey=tn9w2l4iq9hqs0n8a0eb168ms&dl=1" target="_blank" class="link-card">🚘 افلون ٢٠٢٢</a>
            <a href="https://www.dropbox.com/scl/fi/ht0fa217apx5kdx9anmgh/Camry-2021.zip?rlkey=n1jajwqz9klqgvlgh0p6etzsk&st=w942whkk&dl=1" target="_blank" class="link-card">🚘 كامري خويلد ٢٠٢١-٢٤</a>
            <a href="https://www.dropbox.com/scl/fi/awive3e1mbn61b9hm76rh/Avalon22ByFahadAndTurki-1.zip?rlkey=tdgfdmtpwpk7xz02io0dfyhto&st=4ikzhtkr&dl=1" target="_blank" class="link-card">🚘 افلون ٢٠٢٢ - مكرر معدل</a>
            <a href="https://www.dropbox.com/scl/fi/6eczql7zcqd7meq5xhcs0/alkhor_server_toyota_land_cruiser_200.zip?rlkey=nuhmjfy76mhbxtn5u39686b4h&st=qr6k8qgk&dl=1" target="_blank" class="link-card">🚙 لاندكروزر ٢٠٠</a>
            <a href="https://www.mediafire.com/file/rt6afbuhcf9cmuw/Land_Cruiser_Lc70_2025.zip/file" target="_blank" class="link-card">🛻 شاص ٢٠٢٥ - آخر</a>
            <a href="https://www.mediafire.com/file/59w83ceqqr5fz42/Monster_RB3_By_Ray.zip/file" target="_blank" class="link-card">🚙 ربع وحش Ray</a>
            <a href="https://www.mediafire.com/file/0vmbpf0swv5neu0/sha9_24_Abu_A7med.zip/file" target="_blank" class="link-card">🛻 شاص ٢٠٢٤ - أبو أحمد</a>
            <a href="https://www.mediafire.com/file/8dgp8blei9m9kr9/Toyota_Land_Cruiser_j70_2024_2025.zip/file" target="_blank" class="link-card">🚙 ربع ٢٠٢٥</a>
            <a href="https://www.mediafire.com/file/q7g6hiof7hqy5vv/RE1_hilux_v1.zip/file" target="_blank" class="link-card">🛻 هايلكس RE1</a>
            <a href="https://www.mediafire.com/file/l4mtjj3bah7udke/2025.zip/file" target="_blank" class="link-card">🚘 كامري ٢٠٢٥ - رابط أول</a>
            <a href="https://www.mediafire.com/file/pq8un46kt6shthw/2025.zip/file" target="_blank" class="link-card">🚘 كامري ٢٠٢٥ - رابط ثاني</a>
            <a href="https://www.mediafire.com/file/975qli5i5wcwdxu/2025%25283%2529.zip/file" target="_blank" class="link-card">🚘 كامري ٢٠٢٥ - رابط ثالث</a>
            <a href="https://www.mediafire.com/file/45txjw0lydfdp7o/2009.zip/file" target="_blank" class="link-card">🛻 شاص ٢٠٠٩ - رابط 1</a>
            <a href="https://www.mediafire.com/file/2s6186lvo7v71ic/abosaad_LX_2009.zip/file" target="_blank" class="link-card">🛻 شاص ٢٠٠٩ - رابط أبو سعد LX</a>
            <a href="https://www.mediafire.com/file/coycfxx9wcnpv4d/1998.zip/file" target="_blank" class="link-card">🚙 لاند ١٩٩٨ - ميديافاير</a>
            <a href="https://www.mediafire.com/file/gthza9g17egwi9u/2015.zip/file" target="_blank" class="link-card">🚙 لاندكروزر ٢٠١٥</a>

            <!-- ================= قسم كيا وهيونداي ================= -->
            <div class="section-title">._كيا وهيونداي (Kia & Hyundai)_. 🚘</div>
            <a href="https://www.dropbox.com/scl/fi/l2pz77ku2jhj00btvdmiz/CeratoFIR.zip?rlkey=2uizzxgbue48nmbnb57khsebs&st=dt3xdgyo&dl=1" target="_blank" class="link-card">🚘 سيراتو</a>
            <a href="https://www.dropbox.com/scl/fi/66lg82v23p0x5cdqsg262/77sonata.zip?rlkey=s9w3v7fuixv3kmo9bwwtunwmv&st=j2xbeifj&dl=1" target="_blank" class="link-card">🚘 سوناتا ٧٧</a>
            <a href="https://www.dropbox.com/scl/fi/vz8iu1az9a9nkspoj7bmu/Azera-2015.zip?rlkey=ivpscc6pik3w6g8sy2hdtv3ix&st=gswyu2n9&dl=1" target="_blank" class="link-card">🚘 ازيرا ٢٠١٥</a>
            <a href="https://www.dropbox.com/scl/fi/3sa7uhejkyt6osqztt6ql/k4_25__.zip?rlkey=5tewsvzxi11g4vnaequt2bog0&st=fm2p0fqs&dl=1" target="_blank" class="link-card">🚘 كي فور (K4)</a>
            <a href="https://www.dropbox.com/scl/fi/ch00pz5461g6io33ojowu/sonatanffl.zip?rlkey=adca7ck840mfpdii0huusvvod&st=wcus5r8e&dl=1" target="_blank" class="link-card">🚘 سوناتا ٢٠٠٩</a>
            <a href="https://www.dropbox.com/scl/fi/uw5hu0el9d9f0tzn7lhoo/Accent-2024.zip?rlkey=yaa3vnr0y89r5ku0dvghkpr62&st=3sddv8zv&dl=1" target="_blank" class="link-card">🚘 اكسنت ٢٠٢٤</a>
            <a href="https://www.dropbox.com/scl/fi/5a0le1e0kjfz28siwrdfx/Cadenza-2018.zip?rlkey=xs4468iecixmpt5n8c1vckrol&st=laqvc8c5&dl=1" target="_blank" class="link-card">🚘 كدنزة ٢٠١٨</a>
            <a href="https://www.dropbox.com/scl/fi/8bpe53f9033e9rqsyv1o4/pegas_2018.zip?rlkey=8ni9ziyct7fmrssqoofyq68uw&st=6z46ugb8&dl=1" target="_blank" class="link-card">🚘 ريو ٢٠١٨ - بيغاس</a>
            <a href="https://www.dropbox.com/scl/fi/vwvxlx7v7ld08l7i3hcx8/soso24.zip?rlkey=vixbsc1hxv2nl00fhgfyynjjc&st=mdvqmo1t&dl=1" target="_blank" class="link-card">🚘 سوناتا ٢٠٢٤ - رابط 1</a>
            <a href="https://www.dropbox.com/scl/fi/bl7bl9gyxdje7qrjex207/soso-24-dis-RZH9.zip?rlkey=x3sb2dwxpzhxeh2a7v13w1fzg&st=h5rvfx0t&dl=1" target="_blank" class="link-card">🚘 سوناتا ٢٠٢٤ - رابط 2</a>
            <a href="https://www.dropbox.com/scl/fi/kyep665av9leq3m10d7am/elantra24.zip?rlkey=0cdtl80y8x1zynxsxzkzu220p&st=u7vjc0yu&dl=1" target="_blank" class="link-card">🚘 الانترا ٢٠٢٤</a>
            <a href="https://www.dropbox.com/scl/fi/hcw6fhs5rwtort64hi37s/Sonata.zip?rlkey=npgm8emospwopvgms8rax4ka0&st=vot3v3a9&dl=1" target="_blank" class="link-card">🚘 سوناتا (عام)</a>
            <a href="https://www.dropbox.com/scl/fi/rj76dq2qf292tbpq65col/KIA-K8-v0.1.zip?rlkey=0ppswluatp1p9jymylakyy4cr&st=hnbsw8i0&dl=1" target="_blank" class="link-card">🚘 كيا K8</a>
            <a href="https://www.dropbox.com/scl/fi/kwrczgene98bzezj2okki/Hyundai-Accent.zip?rlkey=1kqorjk7umtbsrbghpiuaf60p&st=ws4w51yt&dl=1" target="_blank" class="link-card">🚘 اكسنت ٢٠٢٠</a>
            <a href="https://www.mediafire.com/file/y70y3hws63gx40i/2021.zip/file" target="_blank" class="link-card">🚘 كدينزا ٢٠٢١</a>
            <a href="https://www.mediafire.com/file/5cgy39x9aj5umvi/2016.zip/file" target="_blank" class="link-card">🚘 سوناتا ٢٠١٦</a>

            <!-- ================= قسم الأمريكي والجي ام سي ================= -->
            <div class="section-title">._شيفروليه وفورد وجي إم سي (GMC / Chevy / Ford)_. 🛻</div>
            <a href="https://www.dropbox.com/scl/fi/l0xjifta3tj8unjwa5qub/GMC-Sierra-2017-2015-V1.2.zip?rlkey=e7kett1nxzjlu684ff9p9thya&st=qpy8tuvy&dl=1" target="_blank" class="link-card">🛻 سيرا ٢٠١٧</a>
            <a href="https://www.dropbox.com/scl/fi/gdo8zcykkbtmc5006uzn4/ZOMVL-NoLimits-Chevrolet-Lumina-2008-2010.zip?rlkey=ut0ftce30m3ja4hme5cwo5z64&st=tpn92u97&dl=1" target="_blank" class="link-card">🚘 لومينا ٢٠٠٨-٢٠١٠</a>
            <a href="https://www.dropbox.com/scl/fi/65e22gy0v291wpt4mvzch/Taurus-23-24.zip?rlkey=410371v2zhgfbubzn1l049cpa&st=3q1v0wgz&dl=1" target="_blank" class="link-card">🚘 تورس ٢٠٢٣-٢٠٢٤</a>
            <a href="https://www.dropbox.com/scl/fi/4gh1vdqll7k0mv9nofaqe/QE1sierra13.zip?rlkey=u2i91vs783necyb1dv35xo1wi&st=romjm9o7&dl=1" target="_blank" class="link-card">🛻 سيرا ٢٠١٣</a>
            <a href="https://www.dropbox.com/scl/fi/zdjenizhbsyv07tchj4g3/sierra-2006.zip?rlkey=wg4e3crrq2dnhwb594nr621lb&st=v1a93w2h&dl=1" target="_blank" class="link-card">🛻 سيرا ٢٠٠٦</a>
            <a href="https://www.dropbox.com/scl/fi/zaq16iyor9loum1s9udm4/flanje_taurus.zip?rlkey=zq4xo2bykc1q56vfj8de4yqxj&st=o3a6u8rf&dl=1" target="_blank" class="link-card">🚘 تورس (عام)</a>
            <a href="https://www.dropbox.com/scl/fi/nkz66byhy265rzi5oza6j/Ford-Saudi-Police.zip?rlkey=bauejhg5d96kntoxwuibv369o&st=3tnz78h3&dl=1" target="_blank" class="link-card">🚓 فورد دورية شرطة سعودية - رابط 1</a>
            <a href="https://www.dropbox.com/scl/fi/nkz66byhy265rzi5oza6j/Ford-Saudi-Police.zip?rlkey=bauejhg5d96kntoxwuibv369o&st=p0y4ii78&dl=1" target="_blank" class="link-card">🚓 فورد دورية شرطة سعودية - رابط ٢ مكرر</a>
            <a href="https://www.dropbox.com/scl/fi/cnh7njr84bidjf7hxwyqb/capricem716.zip?rlkey=yaae52d1yzc75hbfunz0lrgrc&st=o06oyo8g&dl=1" target="_blank" class="link-card">🚘 كابرس ٢٠١٦</a>
            <a href="https://www.dropbox.com/scl/fi/nqazbhlualr136u8ebof2/capricem716.zip?rlkey=wloj9t44l1tundsix641ayb9m&st=k73j80so&dl=1" target="_blank" class="link-card">🚘 كابرس ٢٠١٣</a>
            <a href="https://www.dropbox.com/scl/fi/5w1t89y06leplzxloxkex/GMC-CLASSIC.zip?rlkey=y9nzciounwxifyxkpk0exrr6y&st=tq1z5ctb&dl=1" target="_blank" class="link-card">🛻 بهبهاني GMC</a>
            <a href="https://www.dropbox.com/scl/fi/q85rm7dvl0lz145faaeat/Caprice-2007-2013.zip?rlkey=cvul1kk3chvv0b8v04j7icufk&st=uu979thd&dl=1" target="_blank" class="link-card">🚘 كابرس ٢٠٠٧-٢٠١٣</a>
            <a href="https://www.dropbox.com/scl/fi/wkw036nli2g94p2wtmo6m/trs_LA9.zip?rlkey=gi5kpvejmdj7jy4g8i4pp0azj&st=t9jvtuv3&dl=1" target="_blank" class="link-card">🚘 تورس ٢٠٢٤</a>
            <a href="https://www.dropbox.com/scl/fi/oqkxiy90ffnz6y3pkvwua/Spark_2024_BWesL.zip?rlkey=mn2umtde89wmblqlod1zxnoit&st=09lyj258&dl=1" target="_blank" class="link-card">🚘 سبارك</a>
            <a href="https://www.mediafire.com/file/oq6f5nl9wjw9fr3/2021%25282%2529.zip/file" target="_blank" class="link-card">🚘 شفروليه كروز</a>
            <a href="https://www.mediafire.com/file/1ozuoof44cufd5n/F-150.zip/file" target="_blank" class="link-card">🛻 فورد F-150</a>
            <a href="https://www.mediafire.com/file/4emjvikngp3aecu/TRS_2_K__2.zip/file" target="_blank" class="link-card">🚘 تورس ٢٠٢٦</a>
            <a href="https://www.mediafire.com/file/v42134eysgrw88/2015_%2528%25D8%25A7%25D9%2584%25D8%25A7%25D8%25B5%25D9%2584%25D9%258I%2529.zip/file" target="_blank" class="link-card">🛻 سيرا ٢٠١٥ أصلي</a>
            <a href="https://www.mediafire.com/file/arnw8h3yef0zcyu/2015_%2528%25D8%25AA%25D8%25AC%25D9%2585%25D9%258A%25D8%25B1%2529.zip/file" target="_blank" class="link-card">🛻 سيرا ٢٠١٥ تجمير</a>
            <a href="https://www.mediafire.com/file/axesmrgyxt49mdl/2025_2%25283%2529.zip/file" target="_blank" class="link-card">🛻 سيرا ٢٠٢٥</a>

            <!-- ================= قسم ياباني ومنوع وألماني ================= -->
            <div class="section-title">._نيسان وهوندا ودوج والماركات الألمانية_. 🚗</div>
            <a href="https://www.dropbox.com/scl/fi/fk9pehaftd610s4wqgcq6/Accord-2017.zip?rlkey=lpxnrfl9dfsszdo0zws14rkug&st=pime3ldm&dl=1" target="_blank" class="link-card">🚘 اكورد ٢٠١٧</a>
            <a href="https://www.dropbox.com/scl/fi/b3thsxzbutsvzfm4pgiaw/Honda-Accord-2012.zip?rlkey=5pf9dmi0carrrjt4lg9yniefa&st=kh3x6jdr&dl=1" target="_blank" class="link-card">🚘 اكورد ٢٠١٢</a>
            <a href="https://www.dropbox.com/scl/fi/v64zj9enuad8mokge3zeg/ENF_Accord13.zip?rlkey=t5y4cvfzc40nirekz7ncnijgx&st=54m9ympc&dl=1" target="_blank" class="link-card">🚘 اكورد ٢٠١٣</a>
            <a href="https://www.dropbox.com/scl/fi/y2rbaqsi4rqt4sa35vufj/f90bbnV3.1.zip?rlkey=h5cczu9in9n7t5kulgb7h64fm&st=k78i6276&dl=1" target="_blank" class="link-card">🚗 بي ام دبليو f90bb V3.1</a>
            <a href="https://www.dropbox.com/scl/fi/hgtfmpdkiwaebla4id4x4/bmw_f10_5-series.zip?rlkey=8dsuqakqy5iab6nm3e129llmv&st=a9rt3z02&dl=1" target="_blank" class="link-card">🚗 بي ام دبليو f10</a>
            <a href="https://www.dropbox.com/scl/fi/7a9h1hfk2ecgthxxje4fo/chives_beta_dodge_charger_v2-2.zip?rlkey=dc55zehk2xpi1hkp5iyak9eqp&st=4xsuavl6&dl=1" target="_blank" class="link-card">🚘 تشارجر</a>
            <a href="https://www.dropbox.com/scl/fi/2yj9zv2nqoo2j8rkjasm1/BMW-M3-G80.zip?rlkey=07vw331zkbp3ts77a70gujia4&st=4ez2vyax&dl=1" target="_blank" class="link-card">🚗 بي ام دبليو M3 G80</a>
            <a href="https://www.dropbox.com/scl/fi/7epl7wnwxsuakc3lraxxb/Nissan_Altima_2023-2024.zip?rlkey=jbn7z3y5xys5ftz9te7qf8u7i&dl=1" target="_blank" class="link-card">🚘 التيما ٢٠٢٣-٢٤</a>
            <a href="https://www.dropbox.com/scl/fi/axcyuhu07us8uj9bg4yzb/w222unl_modland.zip?rlkey=nz4iqlsq6ahzge8ipll3mij7v&st=8g1zetfd&dl=1" target="_blank" class="link-card">🚗 مرسيدس S63 W222</a>
            <a href="https://www.dropbox.com/scl/fi/z2tfi25c8z4lcpp13f7ej/IS350_modland.zip?rlkey=q5f0mwgzrics6gv89hr4kkncx&st=b5b04sfk&dl=1" target="_blank" class="link-card">🚘 لكزس IS350 - رابط 1</a>
            <a href="https://www.dropbox.com/scl/fi/3pm4dbb5jflfzj5ka1ukz/Lexus_IS350.zip?rlkey=mz9i9eibttvwh45y5g1wh7ia9&st=0ru6qdv4&dl=1" target="_blank" class="link-card">🚘 لكزس IS350 - رابط 2</a>
            <a href="https://www.dropbox.com/scl/fi/vrddadkh2b0zjoli7lar6/dodge-charger-2015-2023-v1-0-0-38-x_1768248937_498232_Tuning_Release_v23_2024_by_RealModsLab_modland.zip?rlkey=pnyktryfa4v2685pkhe3ufhkz&st=qa6uydor&dl=1" target="_blank" class="link-card">🚘 دوج تشارجر ٢٠١٥-٢٠٢٣</a>
            <a href="https://www.mediafire.com/file/plhjvlycwji9hki/2022.zip/file" target="_blank" class="link-card">🚙 جيب دورية قراند شيروكي ٢٠٢٢</a>
            <a href="https://www.mediafire.com/file/tsmosbxgev90fm8/Dodge_Challenger_SRT_Demon_170.zip/file" target="_blank" class="link-card">🚘 دوج تشالنجر</a>
            <a href="https://www.mediafire.com/file/ztws7gjqn580vdr/Chrysler_300_l5fi.zip/file" target="_blank" class="link-card">🚘 كرايسلر</a>
            <a href="https://www.mediafire.com/file/xk2c0zi59ia3rj1/Cadillac_CT5_V_Blackwing.zip/file" target="_blank" class="link-card">🚘 كاديلاك CT5-V</a>
            <a href="https://www.dropbox.com/scl/fi/s8hffk6s7zhrcxqbzl33v/280zx.zip?rlkey=vgqtz5qintelnpken5wye4fwu&st=mxxkz4z7&dl=1" target="_blank" class="link-card">🚗 نيسان داتسون 280zx</a>
            <a href="https://www.dropbox.com/scl/fi/0al3zelahxtbn8j4co5j6/Lexus_LS430_Toyota_Celsior_V2.zip?rlkey=hf030lzhyjtm3c51vh3h1yomj&st=kkdzu8el&dl=1" target="_blank" class="link-card">🚘 لكزس LS430</a>
            <a href="https://www.dropbox.com/scl/fi/ctbth9kd2ph3mauhqzwdd/mercedes-amg-g63.zip?rlkey=5i92z3baz6dyjle2meqh2sy66&st=4fg25zne&dl=1" target="_blank" class="link-card">🚙 مرسيدس جي كلاس</a>
            <a href="https://www.dropbox.com/scl/fi/cmglufgyxqaxigc3sc9ms/kn0z_y61.zip?rlkey=3p8ykx1xstrc4c6r8hbbmh3j4&st=dlip1siy&dl=1" target="_blank" class="link-card">🚙 نيسان فتك y61</a>
            <a href="https://www.dropbox.com/scl/fi/zh8wgoo3bopdi8g7j58tc/Range-Rover-Sport-SVR-2018.zip?rlkey=pbfwu138buuestp4x4zjuldfv&st=8jei0lx8&dl=1" target="_blank" class="link-card">🚙 رنج روفر سبورت ٢٠١٨</a>
            <a href="https://www.dropbox.com/scl/fi/qq0dnk14jvi510f5sn2mk/BANSHEELONLEY.zip?rlkey=t5z4qd0huxsseopwv0fym1xuq&st=3zk6wffh&dl=1" target="_blank" class="link-card">🏍️ دباب بانشي</a>
            <a href="https://www.mediafire.com/file/kquad01caleylra/2025_2.zip/file" target="_blank" class="link-card">🏎️ موستنق ٢٠٢٥</a>

            <!-- ================= قسم المابات ================= -->
            <div class="section-title">._المابات (هجولة وتطعيس وواقعية)_. 🗺️</div>
            <a href="https://www.dropbox.com/scl/fi/gshi21vvm75tlrmhm5sd6/Dayiri-Al-Tishalih-Al-Qassim.zip?rlkey=uadv0ju0oo0aci6o3t6ybfhiq&st=pfdsz9ll&dl=1" target="_blank" class="link-card">🗺️ ماب الدايري تشاليح القصيم (خويلد)</a>
            <a href="https://www.dropbox.com/scl/fi/qt3wnl3m7iapu0e1nnpem/Mustawdaeat_KHwylD.zip?rlkey=29j4jfvex52fcelpjvlq0l7oi&st=g3c1byi2&dl=1" target="_blank" class="link-card">🗺️ ماب مستودعات (خويلد)</a>
            <a href="https://www.dropbox.com/scl/fi/ft3oox4yud491qdwpyg39/Al_Jaradiah_Riyadh.zip?rlkey=82b1s78qd04o0palbgxbz1ldc&st=nvuxewtm&dl=1" target="_blank" class="link-card">🗺️ حي الجرادية الرياض</a>
            <a href="https://www.dropbox.com/scl/fi/6vj81nsko9xorjne9fb70/riyadh-map.zip?rlkey=ed9t1rw1wb22d609tpgi69juy&st=lslzhef7&dl=1" target="_blank" class="link-card">🗺️ ماب الرياض الأساسي</a>
            <a href="https://www.mediafire.com/file/rgentdfl7u4r30v/HighWay_KHwylD.zip/file" target="_blank" class="link-card">🗺️ ماب خويلد هجول هايواي</a>
            <a href="https://www.dropbox.com/scl/fi/gwmsy4nxosnn1jtnixlt5/0Toxic_Street_v1_1.zip?rlkey=vgm3hm6uycbh2s2dnpxjo393x&st=grdcf29m&dl=1" target="_blank" class="link-card">🗺️ ماب توكسك v1.1</a>
            <a href="https://www.dropbox.com/scl/fi/5sypgg4ur1a5sfi8k9y3o/_QE1_V1.zip?rlkey=bgom75g44yauvp2837jo0n60r&st=6by0b64a&dl=1" target="_blank" class="link-card">🗺️ ماب QE1 هجولة وتطعيس</a>
            <a href="https://www.dropbox.com/scl/fi/9otv83tcdsyhzzzez2fl3/alshfa_NaF.zip?rlkey=drsjkqeh7c6fqnqf3mcn5lxnn&st=kn2u00lc&dl=1" target="_blank" class="link-card">🗺️ ماب الشفا ميتو هجولة</a>
            <a href="https://www.dropbox.com/scl/fi/f0b9luo16uwtoz13u1eak/al_yasmin_3ks_3.zip?rlkey=9tgcr9am6h68600lndxyl3rt5&st=rbc1bzg2&dl=1" target="_blank" class="link-card">🗺️ ماب الياسمين عكس هجولة ٢</a>
            <a href="https://www.dropbox.com/scl/fi/jozf86rp6lfymc7ymqqie/ali_kuwait_city_c1_modland.zip?rlkey=j8afooj6amvkr3m6e9tmpf8yl&st=kfel0kyp&dl=1" target="_blank" class="link-card">🗺️ ماب مدينة الكويت</a>
            <a href="https://www.dropbox.com/scl/fi/2zi0k06k8p7o5lujhc9e6/0Toxic_Street_v1_1_edit_S6B.zip?rlkey=mng43mdy92hlmb346su79woe9&st=wx0lc6n1&dl=1" target="_blank" class="link-card">🗺️ ماب توكسك ٢ معدل S6B</a>
            <a href="https://www.dropbox.com/scl/fi/w2oe3pyipujzf11rapu7h/Alshfa-Map.zip?rlkey=c6voqm4idaroigcpxv6srh886&st=gq0gjm8c&dl=1" target="_blank" class="link-card">🗺️ ماب الشفا هجولة ١</a>
            <a href="https://www.dropbox.com/scl/fi/95fju6qt943m9q9tjpgha/ALQWAT_By_M6Noo5.zip?rlkey=d1qaq2r8wvzi63uen1mic35x4&st=6nyes3yq&dl=1" target="_blank" class="link-card">🗺️ ماب القوات بواسطة مطنوخ</a>
            <a href="https://www.dropbox.com/scl/fi/093ntcda5u0jzrvzn6s4f/m7highway2.zip?rlkey=jc408q73aobq85q8ksd6w0uqx&st=fusjs0w7&dl=1" target="_blank" class="link-card">🗺️ ماب هايواي m7 هجولة ٣</a>
            <a href="https://www.dropbox.com/scl/fi/8r6p0evuwms0i20rdgu2t/HighWay_KHwylD.zip?rlkey=az81ythwzcasvd02e868je7c7&st=6gb3yx7e&dl=1" target="_blank" class="link-card">🗺️ ماب هايواي تصوير خويلد</a>
            <a href="https://www.dropbox.com/scl/fi/5bdujrf945fkk2scj9b5k/HighWay.zip?rlkey=kg31rsp0w1rti9qf7snmexeer&st=0mmrcgpo&dl=1" target="_blank" class="link-card">🗺️ ماب دايري هايواي</a>
            <a href="https://www.dropbox.com/scl/fi/9be5h062y6q2zipjzoabp/sonic_2025_v1.zip?rlkey=uv6wz7re96tqyf1govbimtkys&st=k0afno00&dl=1" target="_blank" class="link-card">🗺️ ماب سونيك ٢٠٢٥ هجولة واستراحات</a>
            <a href="https://www.dropbox.com/scl/fi/840e4vexgm1a6dsbl4am1/river_highway.zip?rlkey=tl7t908nnt8ykbtxyu4g8zdxj&st=8b0a5s56&dl=1" target="_blank" class="link-card">🗺️ ماب خط النهر السريع</a>
            <a href="https://www.dropbox.com/scl/fi/2ie4uc1td0sdllt8erhyb/Map-By-Ray.zip?rlkey=2x2mfctnwxsyw2nbrwf1yyi64&st=fo4r4sgn&dl=1" target="_blank" class="link-card">🗺️ ماب هجولة واستراحات ٢ Ray</a>
            <a href="https://www.dropbox.com/scl/fi/b324bzpyxk2x9lecs702v/grille_autobahn_loop.zip?rlkey=u7ie7gbmb6z0120ebtwmvzy09&st=tvskagmd&dl=1" target="_blank" class="link-card">🗺️ ماب صلالة الخريف والخط السريع الألماني</a>
            <a href="https://www.dropbox.com/scl/fi/vmp85m0roldkw5x2rd66k/Al_Suwaidi_Crach-1.zip?rlkey=m8ryq26ggrw9jj6fwrfqkp04b&st=eg8tnozq&dl=1" target="_blank" class="link-card">🗺️ ماب السويدي كراش</a>
            <a href="https://www.dropbox.com/scl/fi/w8grti5h4tfbbmvx5knd6/8nooz_City_By_Moov.zip?rlkey=feohr4lebhvgh8h42nn3utl1k&st=la7j786q&dl=1" target="_blank" class="link-card">🗺️ ماب مدينة عنوز</a>
            <a href="https://www.dropbox.com/scl/fi/vehtmq1u3k1r7wdn60e6q/ShowRoom-v1.zip?rlkey=f87zerdf8bj3ef5nidvb8oiml&st=6oim4flq&dl=1" target="_blank" class="link-card">📸 ماب بيت تصوير ShowRoom v1</a>
            <a href="https://www.mediafire.com/file/8ck9yya1nghiy44/Grnada.zip/file" target="_blank" class="link-card">🗺️ غرناطة Grnada</a>
            <a href="https://www.mediafire.com/file/7no4x9aqoq8jsam/M7_AND_FRINCE.zip/file" target="_blank" class="link-card">🗺️ ماب كينج هجولة</a>
            <a href="https://www.mediafire.com/file/ha0cqc0c7osqiq1/Al_Suwaidi.zip/file" target="_blank" class="link-card">🗺️ ماب السويدي الأساسي</a>
            <a href="https://www.mediafire.com/file/yw2j7e78slgjqjm/GlamisOldsmobile_modland.zip/file" target="_blank" class="link-card">🗺️ ماب البر الطعوس الواقعية</a>
            <a href="https://www.mediafire.com/file/eopby10c1hwz1tw/2K-Irohazaka_modland.zip/file" target="_blank" class="link-card">⛰️ ماب درفت + تصوير جبل إيروها</a>
            <a href="https://www.mediafire.com/file/jxhvjkdok87hwc2/MSKAT_50_aln9em.zip/file" target="_blank" class="link-card">🗺️ ماب مسكات النظيم ٥٠ - رابط 1</a>
            <a href="https://www.mediafire.com/file/p2n3qn1eidu7oy1/MSKAT_50_aln9em.zip/file" target="_blank" class="link-card">🗺️ ماب مسكات النظيم ٥٠ - رابط 2</a>
            <a href="https://www.mediafire.com/file/ikpcnblrmoscsvf/Abo_SrooR_Sasko_2.zip/file" target="_blank" class="link-card">⛽ ماب محطة ساسكو أبو سرور</a>
            <a href="https://www.mediafire.com/file/drpl1n9rlkvxltq/%25D9%2585%25D8%25A7%25D8%25B8_%25D8%25B7%25D9%2588%25D9%258ايق_.zip/file" target="_blank" class="link-card">🗺️ ماب طويق هجولة</a>
            <a href="https://www.mediafire.com/file/j1oa45vcpz1mo1i/Meto_2.zip/file" target="_blank" class="link-card">🗺️ غروب التشاليح + خريص النظيم ميتو - رابط 1</a>
            <a href="https://www.mediafire.com/file/ocd6popwp604edr/Meto.zip/file" target="_blank" class="link-card">🗺️ غروب التشاليح + خريص النظيم ميتو - رابط 2</a>
            <a href="https://www.mediafire.com/file/nnykyd7k6pj87b7/sandy_mountain.zip/file" target="_blank" class="link-card">⛰️ ماب عقبة الهدا ساندي ماونتن</a>
            <a href="https://www.mediafire.com/file/0wf40iw2zt7fajy/Drive_Jubail_By_iiMoov.zip/file" target="_blank" class="link-card">🏭 ماب الجبيل للواقعية</a>
            <a href="https://www.mediafire.com/file/r91ttz0kb0jl42r/salada.zip/file" target="_blank" class="link-card">⛰️ ماب البر الواقعي صلالة</a>
            <a href="https://www.mediafire.com/file/erb3zq1zwj4ez9n/Al_Suwan_liwa.zip/file" target="_blank" class="link-card">🏜️ ماب ليوا الطعوس الطائرة</a>
            <a href="https://gofile.io/d/7avgRg" target="_blank" class="link-card">🏝️ ماب جزيرة يونيون</a>
            <a href="https://gofile.io/d/TEJS1h" target="_blank" class="link-card">🏰 قصر إيطاليا الرائع</a>
            <a href="https://gofile.io/d/8ZdIPQ" target="_blank" class="link-card">🎯 ماب هوم رينج باربنت</a>
            <a href="https://gofile.io/d/DWJrKk" target="_blank" class="link-card">🌆 مدينة يوكوهاما اليابان الشهيرة</a>
            <a href="https://gofile.io/d/HEECgj" target="_blank" class="link-card">🏝️ ماب جزيرة كاسل روك</a>

            <!-- ================= قسم الملحقات والإضافات ================= -->
            <div class="section-title">._مودات التركيب والملحقات والإضافات_. 🛠️</div>
            <a href="https://www.dropbox.com/scl/fi/ud743al0fshny1plsyfcs/cktodbox.zip?rlkey=m6y1pch00o7dhshs4mryjs9cl&st=dgqswq4y&dl=1" target="_blank" class="link-card">☁️ مود الغيوم الواقعي</a>
            <a href="https://www.mediafire.com/file/rohkc6xy14wqfb1/cktodbox_eveningmorning.zip/file" target="_blank" class="link-card">☁️ مود الغيوم المسائي والصباحي</a>
            <a href="https://www.mediafire.com/file/1og54e2dl9p1x2t/f70v3_%25281%2529_%25281%2529.ini.zip/file" target="_blank" class="link-card">🌅 مود جرافيكس جبار</a>
            <a href="https://www.mediafire.com/file/0h862m3oqyqubqr/ttweaks.zip/file" target="_blank" class="link-card">⚙️ مود تحسين جودة وتنعيم تفاصيل اللعبة</a>
            <a href="https://www.mediafire.com/file/l0i0wgjriaq8u8q/dynamic_weather_mk_repo_v1.zip/file" target="_blank" class="link-card">🌧️ مود المطر الواقعي والطقس الديناميكي</a>
            <a href="https://www.dropbox.com/scl/fi/wupoqju41ovtul6vuef5v/change_ground_grip_angelo234-2.zip?rlkey=jrm42gegle0i5gpkqqios5km0&st=poo46eec&dl=1" target="_blank" class="link-card">🛣️ مود تنعيم الشوارع وتعديل تماسك الأرضيات للهجولة</a>
            <a href="https://www.dropbox.com/scl/fi/90fy3ebrbyzqyi1wredvh/kn0zmaxxis900.zip?rlkey=i89avzgcoxckar77o2gspv4g4&st=6it0dkkq&dl=1" target="_blank" class="link-card">🛞 تواير ماكسس البوالين الشهيرة</a>
            <a href="https://www.dropbox.com/scl/fi/fvil4b7n25ry52ric9ziq/maxxis900.zip?rlkey=mzov1vn96i8cv6uy7my9gg1qk&st=2rj546pm&dl=1" target="_blank" class="link-card">🛞 كفرات البوالين العامة</a>
            <a href="https://www.dropbox.com/scl/fi/avfffge1oi2gz0ow4ef1l/BO_AHMED_Maxxis900_V3.zip?rlkey=mh5jpxnj6ijlgzthvxns3gu0g&st=pndrpgpp&dl=1" target="_blank" class="link-card">🛞 بوالين ماكسس الإصدار الثالث V3</a>
            <a href="https://www.mediafire.com/file/khwte1d6x2lqaqa/AM_%2528wxht%2529_-_common_V2_2.zip/file" target="_blank" class="link-card">📦 بكج جنوط وكفرات معدلة - رابط أول</a>
            <a href="https://www.mediafire.com/file/s4x2eu2zdzsnsmy/AM_%2528wxht%2529_-_common.zip/file" target="_blank" class="link-card">📦 بكج جنوط وكفرات معدلة - رابط ثاني</a>
            <a href="https://www.mediafire.com/file/5tduetyl3epszkb/Bridgestone_KHwylD.zip/file" target="_blank" class="link-card">🛞 مجسم كفرات بريدجستون (خويلد)</a>
            <a href="https://www.mediafire.com/file/n368gieyg4xshwh/art.zip/file" target="_blank" class="link-card">🔊 حل مشكلة صوت مكينة السيلفرادو والسيرا</a>
            <a href="https://www.mediafire.com/file/dt7by0shrvbdh/WSCX_Dream_Engines_Pack_Full.zip/file" target="_blank" class="link-card">⚙️ بكج مكائن الأحلام الرهيب بالتعديل الشامل</a>
            <a href="https://www.mediafire.com/file/6uhvj8bjz2fi5n9/pgp_engine_pack_%2528AAM%2529_2.zip/file" target="_blank" class="link-card">⚙️ تجميع المكائن القوية PGP</a>
            <a href="https://www.dropbox.com/scl/fi/liu6dqj97l44err21epp4/fakeheadlights.zip?rlkey=2bw7wxtnrpg0ylrdex9goxodg&st=nye3demz&dl=1" target="_blank" class="link-card">💡 مود الأنوار الفيك لزيادة الجمالية</a>
            <a href="https://www.mediafire.com/file/ywfmcdkicuk53m9/ksaplate_v14.zip/file" target="_blank" class="link-card">💳 لوحات سعودية كلاسيكية وحديثة</a>
            <a href="https://www.mediafire.com/file/mgmqbuwp0n02hwi/uaeplate.zip/file" target="_blank" class="link-card">💳 لوحات إماراتية وخليجية مميزة</a>
            <a href="https://www.dropbox.com/scl/fi/c59gns17056ksjy5505g5/sh9_tkih_7T.zip?rlkey=xt5xbk2msoe44mel8knnswaky&st=xjeafvc7&dl=1" target="_blank" class="link-card">⛺ مود الجلسة العربية الفخمة للتصوير (التكية)</a>
            <a href="https://www.dropbox.com/scl/fi/xitayg2rhtarvwxrji5qw/yb_working_winch_trailer.zip?rlkey=k2pvl9p9d3t32mtk1rkwczkqd&st=qb5dlk1x&dl=1" target="_blank" class="link-card">🚛 قلص سحب المواتر ونش شغال بالكامل</a>
            <a href="https://www.mediafire.com/file/yqxw03b9fitpswi/CharactersSingleSlot.zip/file" target="_blank" class="link-card">👤 مجسم شخصيات لوضع ركاب داخل السيارات</a>
            <a href="https://www.mediafire.com/file/c77wn2yrfs2n6df/sunburst2_2.zip/file" target="_blank" class="link-card">✨ مود الكتم والنيكل لإعطاء السيارة مظهر هيبة</a>
            <a href="https://www.mediafire.com/file/i84fw02rrrv6kvj/agent_traffic_mod.zip/file" target="_blank" class="link-card">🚦 مود المواطنين والسيارات الواقعية في الشارع Traffic - رابط 1</a>
            <a href="https://www.mediafire.com/file/bmld8ubx0iezu3l/nfstrafficpack-1.zip/file" target="_blank" class="link-card">🚦 مود المواطنين والسيارات الواقعية في الشارع Traffic - رابط 2 نيد فور سبيد</a>

            <!-- ================= قسم البكجات المجمعة ================= -->
            <div class="section-title">._بكجات تجميعية ضخمة جاهزة_. 📦</div>
            <a href="https://mega.nz/file/6pwSRY6L#QAf8kgvl1FrFLQPtp5xnlKey39Jy78cPj1DG669MQ70" target="_blank" class="link-card">📦 بكج مواتر الميجا الأول</a>
            <a href="https://mega.nz/file/G0AR0LoL#mn_lqPlCV9B78qljiw4_F20Nt1TiFOazupSo81Nequs" target="_blank" class="link-card">📦 بكج مواتر الميجا الثاني</a>
            <a href="https://mega.nz/file/f3oyhIaR#-25F17zgFj8dIIRaIjXXg7b8oEht-F2HJ-e1sRreBAk" target="_blank" class="link-card">📦 بكج المابات المجمعة كاملة</a>

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
