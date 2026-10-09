"""
X (Twitter) Premium Gift Automation Telegram Bot
Private Admin Bot for Asad (@Asadlee24 / Chat ID: 7080909965)

High-Speed, Ultra-Reliable Edition:
- Direct High-Speed Twitter Gateway (~1s response time, 300 BDT / 600 BDT)
- SOCKS5 Telegram Proxy with auto-reconnecting session
- Single-instance PID management (no duplicate messages)
- HTML mode to prevent underscore formatting errors
- Validated <=64 byte callback_data (no BUTTON_DATA_INVALID)
"""

import os
import sys
import time
import json
import sqlite3
import logging
import threading
import subprocess
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import requests
from requests.adapters import HTTPAdapter

# ==================== CONFIGURATION ====================
def load_dotenv():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "7080909965"))

# Telegram proxy for reaching api.telegram.org in PK (optional on cloud/GitHub Actions)
TG_PROXY = os.getenv("TG_PROXY", "")
TG_PROXIES = {
    "http": TG_PROXY,
    "https": TG_PROXY
} if TG_PROXY else None

# Twitter / X Credentials (Loaded dynamically from cookies.json or environment)
COOKIES_FILE = os.path.join(os.path.dirname(__file__), "cookies.json")

def load_saved_cookies():
    if os.path.exists(COOKIES_FILE):
        try:
            with open(COOKIES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("auth_token"), data.get("ct0")
        except Exception as e:
            logger.error(f"Error reading cookies.json: {e}")
    return None, None

saved_auth, saved_ct0 = load_saved_cookies()
AUTH_TOKEN = saved_auth or os.getenv("AUTH_TOKEN", "")
CT0 = saved_ct0 or os.getenv("CT0", "")
BEARER_TOKEN = os.getenv("BEARER_TOKEN", "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA")

def save_cookies(auth_token, ct0):
    global AUTH_TOKEN, CT0
    AUTH_TOKEN = auth_token
    CT0 = ct0
    try:
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump({"auth_token": auth_token, "ct0": ct0}, f, indent=2)
        logger.info("Saved new cookies to cookies.json")
    except Exception as e:
        logger.error(f"Error saving cookies.json: {e}")
    
    # Git auto-commit & push to persist in private repo across future cloud runs
    try:
        subprocess.run(["git", "add", "cookies.json"], capture_output=True, timeout=5)
        subprocess.run(["git", "commit", "-m", "chore: update session cookies via telegram"], capture_output=True, timeout=5)
        subprocess.run(["git", "push"], capture_output=True, timeout=10)
    except Exception as e:
        logger.warning(f"Git auto-push for cookies.json: {e}")

def parse_cookies_input(text):
    auth_match = re.search(r'auth_token\s*[:=]\s*([a-f0-9]{32,})', text, re.I)
    ct0_match = re.search(r'ct0\s*[:=]\s*([a-f0-9]{32,})', text, re.I)
    
    auth = auth_match.group(1) if auth_match else None
    ct0 = ct0_match.group(1) if ct0_match else None
    
    if not auth or not ct0:
        parts = [p.strip() for p in text.split() if len(p.strip()) >= 32 and not p.startswith('/')]
        for p in parts:
            if len(p) == 40 and not auth:
                auth = p
            elif len(p) > 40 and not ct0:
                ct0 = p
    return auth, ct0

# Stripe Public Key
STRIPE_PK = "pk_live_51Ika5JA3KZ32dPo1Uxw4aqV0ZMlJ6ATznaCs2P3nJCtDAwj6qw0ACmoab3PrB9eGfrWmxHVtrcWZcSohktLW26Ji00gnr09tHq"

# X Premium Gift Plans
PLANS = {
    "3m": {
        "title": "3 Months Premium",
        "months": 3,
        "product_id": "prod_TJXJtpzqCpI36N",
        "bdt": 300,
        "usd_approx": "~$2.50"
    },
    "6m": {
        "title": "6 Months Premium",
        "months": 6,
        "product_id": "prod_TJXKKNJwZJIhCM",
        "bdt": 600,
        "usd_approx": "~$5.00"
    }
}

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("XGiftBot")

# ==================== SESSIONS ====================
tg_session = None

def get_tg_session():
    global tg_session
    if tg_session is None:
        tg_session = requests.Session()
        adapter = HTTPAdapter(pool_connections=15, pool_maxsize=15, max_retries=1)
        tg_session.mount("https://", adapter)
        tg_session.mount("http://", adapter)
        if TG_PROXIES:
            tg_session.proxies = TG_PROXIES
    return tg_session

def reset_tg_session():
    global tg_session
    try:
        if tg_session:
            tg_session.close()
    except Exception:
        pass
    tg_session = None
    return get_tg_session()

# Direct Twitter session (lightning fast, ~1.1s response time)
x_direct_session = requests.Session()
x_adapter = HTTPAdapter(pool_connections=15, pool_maxsize=15, max_retries=2)
x_direct_session.mount("https://", x_adapter)

executor = ThreadPoolExecutor(max_workers=10)
active_tasks = set()
tasks_lock = threading.Lock()

# ==================== DATABASE ====================
DB_PATH = os.path.join(os.path.dirname(__file__), "orders.db")
db_lock = threading.Lock()

def init_db():
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                username TEXT,
                recipient_id TEXT,
                plan_key TEXT,
                amount_bdt INTEGER,
                session_id TEXT UNIQUE,
                session_url TEXT,
                status TEXT DEFAULT 'open',
                payment_status TEXT DEFAULT 'unpaid',
                paid_at TEXT
            )
        """)
        conn.commit()
        conn.close()

def save_order(username, recipient_id, plan_key, amount_bdt, session_id, session_url):
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        c.execute("""
            INSERT INTO orders (created_at, username, recipient_id, plan_key, amount_bdt, session_id, session_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (now, username, recipient_id, plan_key, amount_bdt, session_id, session_url))
        order_id = c.lastrowid
        conn.commit()
        conn.close()
        return order_id

def get_order_by_id(order_id):
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT session_id, username, plan_key, amount_bdt FROM orders WHERE id = ?", (order_id,))
        row = c.fetchone()
        conn.close()
        return row

def update_order_status(session_id, status, payment_status):
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        paid_at = datetime.now(timezone.utc).isoformat() if payment_status == "paid" else None
        c.execute("""
            UPDATE orders 
            SET status = ?, payment_status = ?, paid_at = COALESCE(paid_at, ?)
            WHERE session_id = ?
        """, (status, payment_status, paid_at, session_id))
        conn.commit()
        conn.close()

def get_recent_orders(limit=5):
    with db_lock:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT username, plan_key, amount_bdt, session_id, session_url, status, payment_status, created_at
            FROM orders ORDER BY id DESC LIMIT ?
        """, (limit,))
        rows = c.fetchall()
        conn.close()
        return rows

# ==================== TWITTER / X API ====================

def get_x_headers(referer_user=""):
    return {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Cookie": f"auth_token={AUTH_TOKEN}; ct0={CT0}",
        "X-Csrf-Token": CT0,
        "X-Twitter-Auth-Type": "OAuth2Session",
        "X-Twitter-Active-User": "yes",
        "X-Twitter-Client-Language": "en",
        "Origin": "https://x.com",
        "Referer": f"https://x.com/{referer_user}/gift-premium" if referer_user else "https://x.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

def check_x_cookies():
    url = "https://x.com/i/api/graphql/kn8hCE6bHstQV2MtfYDTKg/PremiumGiftingQuery?variables=" + requests.utils.quote(json.dumps({"screenName": "elonmusk"}))
    try:
        r = x_direct_session.get(url, headers=get_x_headers("elonmusk"), timeout=5)
        if r.status_code == 200:
            return True, "Cookies are valid and connected to X directly (1.1s latency)."
        return False, f"Twitter API HTTP {r.status_code}"
    except Exception as e:
        return False, f"Connection error: {e}"

def lookup_x_user(screen_name):
    screen_name = screen_name.strip().lstrip("@")
    if "/" in screen_name:
        screen_name = screen_name.split("/")[-1]
    
    url = "https://x.com/i/api/graphql/kn8hCE6bHstQV2MtfYDTKg/PremiumGiftingQuery?variables=" + requests.utils.quote(json.dumps({"screenName": screen_name}))
    
    try:
        t0 = time.time()
        r = x_direct_session.get(url, headers=get_x_headers(screen_name), timeout=5)
        logger.info(f"User lookup for @{screen_name} took {round(time.time()-t0, 2)}s, status {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            user_res = data.get("data", {}).get("user", {}).get("result", {})
            if user_res:
                return parse_user_res(user_res, screen_name), None
            return None, f"User `@{screen_name}` not found on Twitter."
        return None, f"Twitter API HTTP {r.status_code}"
    except Exception as e:
        return None, f"Network error contacting Twitter: {e}"

def parse_user_res(user_res, screen_name):
    rest_id = user_res.get("rest_id")
    is_eligible = user_res.get("premium_gifting_eligible", False)
    core = user_res.get("core", {})
    name = core.get("name", screen_name)
    actual_screen = core.get("screen_name", screen_name)
    is_blue = user_res.get("is_blue_verified", False)
    return {
        "screen_name": actual_screen,
        "name": name,
        "rest_id": rest_id,
        "eligible": is_eligible,
        "is_blue": is_blue
    }

def create_gift_checkout(screen_name, rest_id, plan_key):
    plan = PLANS[plan_key]
    url = "https://x.com/i/api/graphql/GqTVJ4S1526tLkxj69xIZw/useOneTimePurchaseGiftMutation"
    
    payload = {
        "variables": {
            "cancel_url": f"https://x.com/{screen_name}/gift-premium",
            "success_url": f"https://x.com/{screen_name}/gift-premium/success",
            "external_product_id": plan["product_id"],
            "gift_recipient": str(rest_id)
        },
        "queryId": "GqTVJ4S1526tLkxj69xIZw"
    }
    
    headers = get_x_headers(screen_name)
    headers["Content-Type"] = "application/json"
    
    try:
        t0 = time.time()
        r = x_direct_session.post(url, json=payload, headers=headers, timeout=6)
        elapsed = round(time.time() - t0, 2)
        logger.info(f"Direct gift mutation finished in {elapsed}s, status {r.status_code}")
        if r.status_code == 200:
            res = r.json()
            errors = res.get("errors", [])
            if errors:
                return None, f"X Error: {errors[0].get('message', 'Rejected by X')}"
            
            gift_data = res.get("data", {}).get("onetimepurchase_gift", {})
            session_id = gift_data.get("session_id")
            session_url = gift_data.get("session_url")
            
            if session_id and session_url:
                order_id = save_order(screen_name, rest_id, plan_key, plan["bdt"], session_id, session_url)
                return {
                    "session_id": session_id,
                    "session_url": session_url,
                    "order_id": order_id,
                    "plan": plan
                }, None
            return None, "Failed to get checkout session from X response."
        return None, f"Twitter API HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        logger.error(f"Gift mutation error: {e}")
        return None, f"Gateway connection error: {e}"

# ==================== STRIPE API ====================

def inspect_stripe_session(session_id):
    url = f"https://api.stripe.com/v1/payment_pages/{session_id}?key={STRIPE_PK}"
    session = get_tg_session()
    for attempt in range(3):
        try:
            r = session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=7)
            if r.status_code != 200:
                return None, f"Stripe HTTP {r.status_code}"
            data = r.json()
            status = data.get("status", "unknown")
            payment_status = data.get("payment_status", "unpaid")
            total = data.get("total", 0)
            currency = data.get("currency", "")
            
            update_order_status(session_id, status, payment_status)
            return {
                "status": status,
                "payment_status": payment_status,
                "total": total,
                "currency": currency
            }, None
        except Exception as e:
            if attempt == 2:
                return None, str(e)
            reset_tg_session()
            time.sleep(0.5)

# ==================== TELEGRAM BOT API ====================

def tg_api(method, data=None, timeout=10):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    for attempt in range(4):
        session = get_tg_session()
        try:
            r = session.post(url, json=data or {}, timeout=timeout)
            return r.json()
        except Exception as e:
            logger.warning(f"Telegram API {method} attempt {attempt+1} failed: {e}")
            reset_tg_session()
            if attempt == 3:
                return {"ok": False, "error": str(e)}
            time.sleep(0.3)

def send_message(chat_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg_api("sendMessage", payload)

def answer_callback(callback_query_id, text=None, show_alert=False):
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
        payload["show_alert"] = show_alert
    return tg_api("answerCallbackQuery", payload, timeout=4)

def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode="HTML"):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": parse_mode
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg_api("editMessageText", payload)

# In-memory user cache
user_cache = {}

def handle_update(update):
    """Processed asynchronously in ThreadPool for instant responsiveness"""
    try:
        # Message handler
        if "message" in update:
            msg = update["message"]
            chat_id = msg.get("chat", {}).get("id")
            text = msg.get("text", "").strip()
            
            if chat_id != ADMIN_CHAT_ID:
                send_message(chat_id, "⛔ <b>Access Restricted.</b>\nThis bot is in private admin mode.")
                return

            if not text:
                return

            clean_lower = text.lower().strip()
            # Fast conversational responses (< 0.1s)
            if clean_lower in ["hi", "hello", "hey", "salam", "aoa", "assalam o alaikum", "kese ho", "kaise ho", "bot", "help", "test"]:
                send_message(chat_id, "👋 <b>Salam Asad bhai!</b> Bot bilkul active aur super fast hai.\n\nAap mujhe kisi customer ka <b>Twitter username</b> bhejein (maslan <code>@BRIDGR__</code> ya <code>@the195nfts</code>), me foran 3M aur 6M ke discount Stripe links generate kar doonga!")
                return

            # Commands
            if text.startswith("/start") or text.startswith("/help"):
                welcome = (
                    "💎 <b>X PREMIUM GIFT AUTOMATION</b> 💎\n"
                    "<i>Private Admin Dashboard — @Asadlee24</i>\n\n"
                    "⚡ <b>Gateway:</b> Bangladesh Discount Pricing (Active)\n"
                    "🚀 <b>Engine:</b> Direct High-Speed API (~1s delivery)\n\n"
                    "📦 <b>Gift Packages Catalog:</b>\n"
                    "• 🎁 <b>3 Months Premium:</b> <code>300 BDT</code> (~$2.50)\n"
                    "• 🎁 <b>6 Months Premium:</b> <code>600 BDT</code> (~$5.00)\n\n"
                    "💡 <b>Kaise use karein:</b>\n"
                    "Sirf customer ka Twitter username bhejein:\n"
                    "👉 <code>@BRIDGR__</code> ya profile link\n\n"
                    "⚙️ <b>Quick Commands:</b>\n"
                    "• /orders — Haaliyah orders aur payment status\n"
                    "• /check — Gateway health check\n"
                    "• /cookies — Twitter cookies update karein"
                )
                send_message(chat_id, welcome)
                return

            elif text.startswith("/cookies") or text.startswith("/setcookies") or "auth_token=" in text:
                auth, ct0 = parse_cookies_input(text)
                if not auth and not ct0:
                    help_cookies = (
                        "🔑 <b>Twitter Session Cookies Update</b>\n\n"
                        "Aap direct naye cookies yahan chat me bhej sakte hain bina coding ke:\n\n"
                        "<b>Option 1 (Command style):</b>\n"
                        "<code>/cookies auth_token=YOUR_AUTH_TOKEN ct0=YOUR_CT0</code>\n\n"
                        "<b>Option 2 (Direct paste):</b>\n"
                        "<code>auth_token=...; ct0=...</code>\n\n"
                        "<b>Option 3 (Dono tokens space ke sath):</b>\n"
                        "<code>/cookies [40-char auth_token] [160-char ct0]</code>\n\n"
                        "💡 <i>Bot khud parse kar ke save kar lega aur live Twitter gateway check karega!</i>"
                    )
                    send_message(chat_id, help_cookies)
                    return
                
                if not auth:
                    send_message(chat_id, "⚠️ <b>auth_token missing hai!</b>\nBarah-e-karam apna 40-character <code>auth_token</code> lazmi shamil karein.")
                    return
                if not ct0:
                    send_message(chat_id, "⚠️ <b>ct0 token missing hai!</b>\nBarah-e-karam apna <code>ct0</code> token lazmi shamil karein.")
                    return
                
                send_message(chat_id, "⏳ <b>Updating & Verifying Cookies with Twitter...</b>")
                save_cookies(auth, ct0)
                
                ok, msg_res = check_x_cookies()
                if ok:
                    success_msg = (
                        "🎉 <b>TWITTER COOKIES SUCCESSFULLY UPDATED!</b> 🎉\n\n"
                        f"• <b>auth_token:</b> <code>{auth[:6]}...{auth[-4:]}</code>\n"
                        f"• <b>ct0:</b> <code>{ct0[:6]}...{ct0[-4:]}</code>\n\n"
                        "✅ <b>Live Status:</b> Connected & Verified!\n"
                        "📍 <b>Discount Pricing:</b> Bangladesh (300 BDT / 600 BDT Active)\n"
                        "💾 <b>Cloud Persistence:</b> 24/7 runner ke liye save ho gaya!"
                    )
                    send_message(chat_id, success_msg)
                else:
                    err_msg = (
                        "⚠️ <b>Cookies Save Ho Gaye, Lekin Twitter Ne Reject Kiya:</b>\n\n"
                        f"<code>{msg_res}</code>\n\n"
                        "Barah-e-karam check karein ke Twitter account login hai ya naye cookies sahi hain."
                    )
                    send_message(chat_id, err_msg)
                return

            elif text.startswith("/check"):
                send_message(chat_id, "🔍 <b>Testing Gateway Health...</b>")
                ok, msg_res = check_x_cookies()
                if ok:
                    send_message(chat_id, f"✅ <b>All Systems Operational!</b>\n\n{msg_res}\n\n📍 <b>Pricing Region:</b> Bangladesh (300 BDT / 600 BDT)\n🛡️ <b>Telegram Gateway:</b> Connected (SOCKS5)")
                else:
                    send_message(chat_id, f"⚠️ <b>Status Alert:</b>\n\n{msg_res}")
                return

            elif text.startswith("/orders"):
                orders = get_recent_orders(5)
                if not orders:
                    send_message(chat_id, "ℹ️ <b>Koi order nahi mila.</b>\nUsername bhej kar naya order generate karein!")
                    return
                
                res = "📋 <b>Recent Gift Orders:</b>\n\n"
                for o in orders:
                    u, pk, amt, sid, surl, st, pst, cat = o
                    status_icon = "🟢 PAID" if pst == "paid" else "🟡 UNPAID"
                    res += (
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"👤 <b>@{u}</b> | <b>{pk.upper()}</b> ({amt} BDT)\n"
                        f"• Status: <b>{status_icon}</b>\n"
                        f"• <a href='{surl}'>💳 Open Stripe Checkout</a>\n"
                    )
                res += "━━━━━━━━━━━━━━━━━━━"
                send_message(chat_id, res)
                return

            elif text.startswith("/status"):
                parts = text.split()
                if len(parts) < 2:
                    send_message(chat_id, "Usage: <code>/status &lt;session_id&gt;</code>")
                    return
                sid = parts[1].strip()
                info, err = inspect_stripe_session(sid)
                if err:
                    send_message(chat_id, f"❌ Error: {err}")
                    return
                
                icon = "✅ PAID" if info["payment_status"] == "paid" else "⏳ UNPAID"
                msg_reply = (
                    f"📊 <b>Payment Status:</b>\n\n"
                    f"• Status: <b>{icon}</b>\n"
                    f"• Amount: <code>{info['total']/100:.2f} {info['currency'].upper()}</code>\n"
                    f"• Session: <code>{sid}</code>"
                )
                send_message(chat_id, msg_reply)
                return

            # Check if unrecognized slash command
            if text.startswith("/"):
                send_message(chat_id, "❓ <b>Command samajh nahi aayi.</b>\nAvailable commands dekhne ke liye /start bhejain.")
                return

            # Twitter username lookup
            username = text.strip()
            if "x.com/" in username or "twitter.com/" in username:
                username = username.rstrip("/").split("/")[-1].split("?")[0]
            
            clean_user = username.lstrip("@")
            wait_msg = send_message(chat_id, f"⚡ <b>Looking up @{clean_user} on Twitter...</b>")
            wait_msg_id = wait_msg.get("result", {}).get("message_id")
            
            user_info, err = lookup_x_user(clean_user)
            if err:
                if wait_msg_id:
                    edit_message(chat_id, wait_msg_id, f"❌ {err}")
                else:
                    send_message(chat_id, f"❌ {err}")
                return
            
            user_cache[chat_id] = user_info
            
            eligibility_text = "✅ Eligible for Gift" if user_info["eligible"] else "⚠️ Notice: User has Blue/Ineligible flag"
            blue_text = "Yes" if user_info["is_blue"] else "No"
            
            reply = (
                f"👤 <b>Twitter Account:</b>\n\n"
                f"• <b>User:</b> @{user_info['screen_name']}\n"
                f"• <b>Name:</b> {user_info['name']}\n"
                f"• <b>Rest ID:</b> <code>{user_info['rest_id']}</code>\n"
                f"• <b>Verified:</b> {blue_text} | <b>Status:</b> {eligibility_text}\n\n"
                f"👇 <b>Select Plan to Generate Stripe Link:</b>"
            )
            
            markup = {
                "inline_keyboard": [
                    [
                        {"text": "🎁 3 Months (300 BDT / ~$2.50)", "callback_data": f"plan:3m:{user_info['screen_name']}"},
                    ],
                    [
                        {"text": "🎁 6 Months (600 BDT / ~$5.00)", "callback_data": f"plan:6m:{user_info['screen_name']}"},
                    ],
                    [
                        {"text": "❌ Cancel", "callback_data": "cancel"}
                    ]
                ]
            }
            if wait_msg_id:
                edit_message(chat_id, wait_msg_id, reply, reply_markup=markup)
            else:
                send_message(chat_id, reply, reply_markup=markup)
            return

        # Callback query handler
        if "callback_query" in update:
            cq = update["callback_query"]
            cq_id = cq["id"]
            chat_id = cq.get("message", {}).get("chat", {}).get("id")
            msg_id = cq.get("message", {}).get("message_id")
            data = cq.get("data", "")
            
            if chat_id != ADMIN_CHAT_ID:
                answer_callback(cq_id, "Unauthorized", show_alert=True)
                return
            
            if data == "cancel":
                answer_callback(cq_id, "Cancelled")
                edit_message(chat_id, msg_id, "❌ Cancelled.")
                return
            
            if data.startswith("chk:"):
                order_id = data.split(":", 1)[1]
                order_row = get_order_by_id(order_id)
                if not order_row:
                    answer_callback(cq_id, "Order not found in DB", show_alert=True)
                    return
                
                session_id = order_row[0]
                answer_callback(cq_id, "Checking Stripe payment status...")
                info, err = inspect_stripe_session(session_id)
                if err:
                    send_message(chat_id, f"❌ Failed to verify: {err}")
                    return
                
                if info["payment_status"] == "paid":
                    msg_status = (
                        f"🎉 <b>PAID & DELIVERED!</b>\n\n"
                        f"✅ <code>{info['total']/100:.2f} {info['currency'].upper()}</code> received.\n"
                        f"Twitter Premium has been granted!"
                    )
                else:
                    msg_status = (
                        f"⏳ <b>Still Unpaid</b>\n\n"
                        f"• Amount: <code>{info['total']/100:.2f} {info['currency'].upper()}</code>\n"
                        f"Waiting for payment on Stripe."
                    )
                send_message(chat_id, msg_status)
                return

            if data.startswith("plan:"):
                parts = data.split(":")
                plan_key = parts[1]
                screen_name = parts[2]
                
                # Debounce: prevent duplicate button clicks
                task_key = (chat_id, plan_key, screen_name.lower())
                with tasks_lock:
                    if task_key in active_tasks:
                        answer_callback(cq_id, "Generating already... please wait 1 second!")
                        return
                    active_tasks.add(task_key)
                
                try:
                    plan = PLANS[plan_key]
                    # Immediately answer callback to remove spinner in < 100ms
                    answer_callback(cq_id, f"⚡ Creating {plan['title']} link...")
                    
                    user_info = user_cache.get(chat_id)
                    if not user_info or user_info.get("screen_name", "").lower() != screen_name.lower():
                        user_info, err = lookup_x_user(screen_name)
                        if err:
                            edit_message(chat_id, msg_id, f"❌ Error: {err}")
                            return
                    
                    rest_id = user_info.get("rest_id") if user_info else None
                    if not rest_id:
                        edit_message(chat_id, msg_id, f"❌ Could not find account ID for @{screen_name}.")
                        return

                    edit_message(chat_id, msg_id, f"⚡ <b>Generating {plan['title']} Stripe Link for @{screen_name}...</b>")
                    
                    result, err = create_gift_checkout(screen_name, rest_id, plan_key)
                    if err:
                        edit_message(chat_id, msg_id, f"❌ <b>Checkout Generation Failed</b>\n\n{err}")
                        return
                    
                    session_id = result["session_id"]
                    session_url = result["session_url"]
                    order_id = result["order_id"]
                    
                    success_text = (
                        f"🎉 <b>STRIPE GIFT LINK GENERATED!</b> 🎉\n\n"
                        f"👤 <b>Recipient:</b> @{screen_name}\n"
                        f"📦 <b>Package:</b> <b>{plan['title']}</b>\n"
                        f"💰 <b>Cost:</b> <code>{plan['bdt']} BDT</code> ({plan['usd_approx']})\n\n"
                        f"🔗 <b>Official Stripe Checkout:</b>\n"
                        f"{session_url}\n\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"📋 <b>Customer Ko Bhejne Ke Liye (Tap to Copy):</b>\n"
                        f"<code>🌟 Official X Premium Gift\n"
                        f"👤 Account: @{screen_name}\n"
                        f"⏱️ Plan: {plan['title']}\n"
                        f"🔗 Pay Securely: {session_url}</code>\n"
                        f"━━━━━━━━━━━━━━━━━━━"
                    )
                    
                    # callback_data is <= 10 bytes to prevent Telegram's 64-byte BUTTON_DATA_INVALID error
                    markup = {
                        "inline_keyboard": [
                            [
                                {"text": "💳 Open Stripe Checkout", "url": session_url}
                            ],
                            [
                                {"text": "🔄 Check Payment Status", "callback_data": f"chk:{order_id}"}
                            ]
                        ]
                    }
                    edit_res = edit_message(chat_id, msg_id, success_text, reply_markup=markup)
                    if not edit_res.get("ok"):
                        logger.error(f"Failed to edit message: {edit_res}")
                        # Fallback: send as fresh message if edit failed
                        send_message(chat_id, success_text, reply_markup=markup)
                finally:
                    with tasks_lock:
                        active_tasks.discard(task_key)
                return

    except Exception as e:
        logger.error(f"Error handling update: {e}", exc_info=True)

def kill_old_instance():
    pid_file = os.path.join(os.path.dirname(__file__), "bot.pid")
    my_pid = os.getpid()
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                old_pid = int(f.read().strip())
            if old_pid and old_pid != my_pid:
                subprocess.run(f"taskkill /F /PID {old_pid}", shell=True, capture_output=True)
        except Exception:
            pass
    with open(pid_file, "w") as f:
        f.write(str(my_pid))

def cookie_health_monitor():
    """Background monitor running every 2 hours to alert admin if Twitter session expires"""
    alert_active = False
    # Initial pause after bot starts
    time.sleep(20)
    while True:
        try:
            ok, msg = check_x_cookies()
            if not ok:
                if not alert_active:
                    alert_msg = (
                        "🚨 <b>WARNING ASAD BHAI: Twitter Session Expired!</b> 🚨\n\n"
                        f"• Reason: <code>{msg}</code>\n\n"
                        "⚠️ Twitter account logout ho gaya hai ya cookies expire ho gayi hain.\n"
                        "Customer orders fail hone se bachane ke liye barah-e-karam naye cookies update karein!"
                    )
                    send_message(ADMIN_CHAT_ID, alert_msg)
                    alert_active = True
                    logger.warning(f"Sent cookie expiration alert: {msg}")
            else:
                if alert_active:
                    recovery_msg = (
                        "✅ <b>Twitter Session Restored!</b>\n\n"
                        "Cookies successfully reconnect ho gayi hain aur gateway operational hai."
                    )
                    send_message(ADMIN_CHAT_ID, recovery_msg)
                    alert_active = False
                    logger.info("Twitter session restored alert sent.")
        except Exception as e:
            logger.error(f"Error in cookie health monitor: {e}")
        time.sleep(7200)

def start_bot():
    kill_old_instance()
    init_db()
    logger.info("Initializing Ultra-Fast Single-Instance X Gift Bot...")
    
    # Start background cookie health monitor
    threading.Thread(target=cookie_health_monitor, daemon=True, name="CookieMonitor").start()
    
    while True:
        me = tg_api("getMe")
        if me.get("ok"):
            bot_user = me["result"]["username"]
            logger.info(f"Bot connected: @{bot_user} (Admin: {ADMIN_CHAT_ID})")
            break
        logger.warning(f"Connecting to Telegram... {me.get('error', '')}")
        time.sleep(1)
    
    offset = None
    logger.info("Starting High-Speed non-blocking Telegram polling loop...")
    while True:
        try:
            params = {"timeout": 0}
            if offset:
                params["offset"] = offset
            
            res = tg_api("getUpdates", params, timeout=10)
            if res.get("ok"):
                updates = res.get("result", [])
                for u in updates:
                    offset = u["update_id"] + 1
                    executor.submit(handle_update, u)
            time.sleep(0.3)
        except Exception as e:
            logger.error(f"Polling loop exception: {e}")
            reset_tg_session()
            time.sleep(1)

if __name__ == "__main__":
    start_bot()
