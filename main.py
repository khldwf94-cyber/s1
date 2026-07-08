import os
import time
import random
import uuid
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# الحين الكود بيقرا التوكن بشكل مخفي وآمن تماماً من لوحة تحكم السيرفر
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# باقي الكود حق ALLOWED_USERS والدوال زي ما هو ما تغير فيه شيء...
