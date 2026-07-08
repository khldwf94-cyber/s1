import os
import random
import uuid
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import requests

app = FastAPI()

# إعداد مجلد الصفحات
templates = Jinja2Templates(directory="templates")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OWNER_CHAT_ID = "5432340735"

allowed_buyers = {}  
active_otps = {}      
active_sessions = {}  

current_site_secret = str(uuid.uuid4())[:8]
last_link_rotation = time.time()

def send_owner_alert(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": OWNER_CHAT_ID, "text": f"🚨 [نظام N7L الآمن]:\n{message}"}
    try: requests.post(url, json=payload)
    except: pass

def send_otp_via_bot(telegram_id: str, code: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    msg = f"🔐 كود الدخول المؤقت للموقع هو: {code}\n⏳ الكود صالح لمدة دقيقتين فقط!"
    payload = {"chat_id": telegram_id, "text": msg}
    try: requests.post(url, json=payload)
    except: pass

class BuyerActivation(BaseModel):
    telegram_id: str
    name: str
    product_number: int

class LoginRequest(BaseModel):
    telegram_id: str

class VerifyRequest(BaseModel):
    telegram_id: str
    code: str

# عرض صفحة تسجيل الدخول أول ما يفتح الموقع
@app.get("/", response_class=HTMLResponse)
async def get_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# عرض صفحة الأغراض والمودات المحمية (ممنوع دخولها إلا بتوكن الجلسة)
@app.get("/store-content", response_class=HTMLResponse)
async def get_content_page(request: Request, token: str = ""):
    if token in active_sessions and active_sessions[token]["expires_at"] > time.time():
        return templates.TemplateResponse("index.html", {"request": request})
    return HTMLResponse(content="<h2>عذراً، الجلسة غير صالحة أو انتهت الـ 60 دقيقة. ارجع سجل دخول مجدداً.</h2>", status_code=403)

@app.post("/api/activate-buyer")
async def activate_buyer(data: BuyerActivation):
    if data.product_number in [3, 5, 6]:
        allowed_buyers[str(data.telegram_id)] = {
            "name": data.name,
            "product": data.product_number,
            "activated_at": datetime.now().isoformat()
        }
        send_owner_alert(f"✅ تم تفعيل مشترك:\nالاسم: {data.name}\nالأيدي: {data.telegram_id}")
        return {"status": "success"}
    return {"status": "ignored"}

@app.post("/api/request-login")
async def request_login(data: LoginRequest):
    tid = str(data.telegram_id)
    if tid not in allowed_buyers:
        raise HTTPException(status_code=403, detail="الأيدي غير مسجل بالمتجر.")
    
    otp_code = str(random.randint(100000, 999999))
    active_otps[tid] = {"code": otp_code, "expires_at": time.time() + 120, "attempts": 0}
    
    send_otp_via_bot(tid, otp_code)
    return {"status": "otp_sent"}

@app.post("/api/verify-otp")
async def verify_otp(data: VerifyRequest, request: Request):
    tid = str(data.telegram_id)
    user_ip = request.client.host

    if tid not in active_otps: raise HTTPException(status_code=400, detail="اطلب كوداً أولاً.")
    otp_data = active_otps[tid]
    
    if otp_data["attempts"] >= 3: raise HTTPException(status_code=429, detail="تم تقييدك لكثرة المحاولات الخاطئة.")
    if time.time() > otp_data["expires_at"]: raise HTTPException(status_code=400, detail="انتهت صلاحية الكود (دقيقتين).")
    if data.code != otp_data["code"]:
        active_otps[tid]["attempts"] += 1
        raise HTTPException(status_code=401, detail="الكود خاطئ!")

    # منع التسريب المتزامن
    for token, session in list(active_sessions.items()):
        if session["telegram_id"] == tid and session["expires_at"] > time.time():
            if session["ip"] != user_ip:
                allowed_buyers.pop(tid, None)
                active_sessions.pop(token, None)
                raise HTTPException(status_code=403, detail="تم رصد دخول متزامن. قفل الحساب!")

    session_token = str(uuid.uuid4())
    active_sessions[session_token] = {"telegram_id": tid, "expires_at": time.time() + 3600, "ip": user_ip}
    active_otps.pop(tid, None)
    
    return {"status": "authenticated", "session_token": session_token}
