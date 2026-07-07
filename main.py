import os
import random
import uuid
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import requests

app = FastAPI()

# --- إعدادات المالك والبوت (سيتم جلب التوكن من إعدادات Render تلقائياً) ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "ضع_التوكن_هنا_إذا_لم_تضعه_في_ريندر")
OWNER_CHAT_ID = "5432340735"  # آيدي حسابك لتلقي التنبيهات السرية

# --- قواعد البيانات المؤقتة في الذاكرة ---
allowed_buyers = {}  # قاعدة بيانات المشتركين للأغراض (3، 5، 6)
active_otps = {}      # أكواد التحقق المؤقتة (صلاحية دقيقتين)
active_sessions = {}  # الجلسات النشطة بالموقع (صلاحية 60 دقيقة)

# متغيرات الرابط الديناميكي (يتغير كل 15 دقيقة)
current_site_secret = str(uuid.uuid4())[:8]
last_link_rotation = time.time()

# --- دالة إرسال التنبيهات الفورية لك (المالك) ---
def send_owner_alert(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": OWNER_CHAT_ID, "text": f"🚨 [نظام N7L الآمن]:\n{message}"}
    try: requests.post(url, json=payload)
    except: pass

# --- دالة إرسال كود الـ OTP للمشترك عبر البوت ---
def send_otp_via_bot(telegram_id: str, code: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    msg = f"🔐 كود الدخول المؤقت للموقع هو: {code}\n⏳ الكود صالح لمدة دقيقتين (2 min) فقط!"
    payload = {"chat_id": telegram_id, "text": msg}
    try: requests.post(url, json=payload)
    except: pass

# --- نماذج البيانات (Data Models) ---
class BuyerActivation(BaseModel):
    telegram_id: str
    name: str
    product_number: int

class LoginRequest(BaseModel):
    telegram_id: str

class VerifyRequest(BaseModel):
    telegram_id: str
    code: str

# --- 1. نقطة استقبال المشتركين تلقائياً من بوت الشراء ---
@app.post("/api/activate-buyer")
async def activate_buyer(data: BuyerActivation):
    if data.product_number in [3, 5, 6]:
        allowed_buyers[str(data.telegram_id)] = {
            "name": data.name,
            "product": data.product_number,
            "activated_at": datetime.now().isoformat()
        }
        send_owner_alert(f"✅ تم تفعيل مشترك جديد تلقائياً:\nالاسم: {data.name}\nالأيدي: {data.telegram_id}\nالغرض: {data.product_number}")
        return {"status": "success"}
    return {"status": "ignored"}

# --- 2. طلب تسجيل الدخول (فحص الأيدي وإرسال كود دقيقتين) ---
@app.post("/api/request-login")
async def request_login(data: LoginRequest):
    tid = str(data.telegram_id)
    if tid not in allowed_buyers:
        raise HTTPException(status_code=403, detail="عذراً، هذا الأيدي غير مسجل أو لم يشترِ الأغراض المطلوبة.")
    
    # توليد كود عشوائي وصلاحية 120 ثانية (دقيقتين)
    otp_code = str(random.randint(100000, 999999))
    active_otps[tid] = {
        "code": otp_code,
        "expires_at": time.time() + 120,
        "attempts": 0
    }
    
    send_otp_via_bot(tid, otp_code)
    send_owner_alert(f"🔑 طلب كود تحقق جديد:\nالأيدي: {tid}\nالاسم: {allowed_buyers[tid]['name']}")
    return {"status": "otp_sent"}

# --- 3. التحقق من الكود وإنشاء جلسة 60 دقيقة + منع الدخول المتزامن ---
@app.post("/api/verify-otp")
async def verify_otp(data: VerifyRequest, request: Request):
    tid = str(data.telegram_id)
    user_ip = request.client.host

    if tid not in active_otps:
        raise HTTPException(status_code=400, detail="الرجاء طلب الكود أولاً.")
    
    otp_data = active_otps[tid]
    
    if otp_data["attempts"] >= 3:
        raise HTTPException(status_code=429, detail="تم حظرك مؤقتاً لتجاوز محاولات إدخال الكود الخاطئ.")

    if time.time() > otp_data["expires_at"]:
        raise HTTPException(status_code=400, detail="انتهت صلاحية الكود (دقيقتين). اطلب كوداً جديداً.")

    if data.code != otp_data["code"]:
        active_otps[tid]["attempts"] += 1
        send_owner_alert(f"❌ محاولة خاطئة لإدخال الكود من الأيدي: {tid}\nالمحاولة رقم: {active_otps[tid]['attempts']}")
        raise HTTPException(status_code=401, detail="كود التحقق غير صحيح!")

    # حظر الدخول المتزامن (منع حسابين شغالين بنفس الوقت)
    for token, session in list(active_sessions.items()):
        if session["telegram_id"] == tid and session["expires_at"] > time.time():
            if session["ip"] != user_ip:
                send_owner_alert(f"🚨🚨 إنذار تسريب! الأيدي {tid} حاول الدخول من جهازين بنفس الوقت!\nتم إلغاء تفعيله تلقائياً.")
                allowed_buyers.pop(tid, None)  # طرده نهائياً وقفل حسابه لحين تواصله معك
                active_sessions.pop(token, None)
                raise HTTPException(status_code=403, detail="تم رصد دخول متزامن وجلسات متعددة. تم قفل الحساب للحماية.")

    # إنشاء جلسة تصفح آمنة صالحة لمدة 60 دقيقة (3600 ثانية)
    session_token = str(uuid.uuid4())
    active_sessions[session_token] = {
        "telegram_id": tid,
        "expires_at": time.time() + 3600,
        "ip": user_ip
    }
    
    active_otps.pop(tid, None)  # حذف الكود بعد الاستخدام الناجح
    send_owner_alert(f"📥 دخل الموقع بنجاح:\nالأيدي: {tid}\nالاسم: {allowed_buyers[tid]['name']}")
    
    return {"status": "authenticated", "session_token": session_token, "secret_path": current_site_secret}

# --- 4. نظام حماية وتغيير الرابط كل 15 دقيقة تلقائياً ---
@app.middleware("http")
async def rotate_link_middleware(request: Request, call_next):
    global current_site_secret, last_link_rotation
    if time.time() - last_link_rotation > 900:  # 900 ثانية = 15 دقيقة
        current_site_secret = str(uuid.uuid4())[:8]
        last_link_rotation = time.time()
    return await call_next(request)
