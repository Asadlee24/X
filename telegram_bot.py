"""
X (Twitter) Premium Gift Automation Telegram Bot
Private Admin Bot for Asad (@Asadlee24 / Chat ID: 7080909965)

High-Performance, Multithreaded Edition:
- Non-blocking ThreadPoolExecutor: zero lag on polling or user input
- Persistent HTTP connection pooling with keep-alive for sub-second responses
- Immediate callback acknowledgement (<100ms UI feedback)
- Duplicate click debouncing
- Bangladesh proxy dedicated to Twitter X pricing (300 BDT / 600 BDT)
- US proxy with keep-alive for Telegram Bot API
"""

import os
import sys
import time
import json
import sqlite3
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import requests
from requests.adapters import HTTPAdapter

# ==================== CONFIGURATION ====================
TELEGRAM_BOT_TOKEN = "8714769969:AAFEm0v1o0tlMOxa8zZnhB2whxwg3w8b5lE"
ADMIN_CHAT_ID = 7080909965

# Telegram proxy (US outbound for stable connection)
TG_PROXY = "http://owcmizouuazq-region-US:owcmizouuazq@us.arxlabs.io:3010"
TG_PROXIES = {
    "http": TG_PROXY,
    "https": TG_PROXY
}

# Bangladesh Regional Proxy (required for X to give cheap 300 BDT / 600 BDT pricing)
BD_PROXY = "http://owcmizouuazq-region-BD:owcmizouuazq@us.arxlabs.io:3010"
BD_PROXIES = {
    "http": BD_PROXY,
    "https": BD_PROXY
}

# Twitter / X Credentials
AUTH_TOKEN = "6db315b21b21d55a5a02577ab2b04d3a220c1268"
CT0 = "0c0d71ddfa92485d469ad70b1d535dcd2083a1520b52a2838d93b37f26322e39d5b41df367ba1902d9538d0bf79b49ab02ca0fa0a9695eae707c7e3e68de44d09aa74b28586920240af265f692062367"
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

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

# ==================== CONNECTION POOLS ====================
# Persistent session for Telegram (fast keep-alive)
tg_session = requests.Session()
tg_adapter = HTTPAdapter(pool_connections=25, pool_maxsize=25, max_retries=2)
tg_session.mount("https://", tg_adapter)
tg_session.mount("http://", tg_adapter)
tg_session.proxies = TG_PROXIES

# Persistent session for BD Twitter gateway
bd_session = requests.Session()
bd_adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=2)
bd_session.mount("https://", bd_adapter)
bd_session.mount("http://", bd_adapter)
bd_session.proxies = BD_PROXIES

# Thread pool for non-blocking asynchronous event handling
executor = ThreadPoolExecutor(max_workers=12)

# Set of currently processing actions to prevent duplicate double-clicks
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
        conn.commit()
        conn.close()

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
    for attempt in range(3):
        try:
            url = "https://x.com/i/api/graphql/kn8hCE6bHstQV2MtfYDTKg/PremiumGiftingQuery?variables=" + requests.utils.quote(json.dumps({"screenName": "elonmusk"}))
            r = bd_session.get(url, headers=get_x_headers("elonmusk"), timeout=8)
            if r.status_code == 200:
                return True, "Cookies are valid and connected to X."
            return False, f"HTTP Error {r.status_code}"
        except Exception as e:
            if attempt == 2:
                return False, f"Connection error: {str(e)}"
            time.sleep(0.5)

def lookup_x_user(screen_name):
    screen_name = screen_name.strip().lstrip("@")
    if "/" in screen_name:
        screen_name = screen_name.split("/")[-1]
    
    url = "https://x.com/i/api/graphql/kn8hCE6bHstQV2MtfYDTKg/PremiumGiftingQuery?variables=" + requests.utils.quote(json.dumps({"screenName": screen_name}))
    
    last_err = None
    for attempt in range(3):
        try:
            r = bd_session.get(url, headers=get_x_headers(screen_name), timeout=8)
            if r.status_code != 200:
                return None, f"Twitter API error (HTTP {r.status_code})"
            
            data = r.json()
            user_res = data.get("data", {}).get("user", {}).get("result", {})
            if not user_res:
                return None, f"User `@{screen_name}` not found on X."
            
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
            }, None
        except Exception as e:
            last_err = e
            time.sleep(0.5)
            
    return None, f"Network error contacting Twitter: {last_err}"

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
    
    last_err = None
    for attempt in range(3):
        try:
            r = bd_session.post(url, json=payload, headers=get_x_headers(screen_name), timeout=10)
            if r.status_code != 200:
                return None, f"X API HTTP {r.status_code}: {r.text[:120]}"
            
            res = r.json()
            errors = res.get("errors", [])
            if errors:
                msg = errors[0].get("message", "Unknown error from X")
                return None, f"X Error: {msg}"
            
            gift_data = res.get("data", {}).get("onetimepurchase_gift", {})
            session_id = gift_data.get("session_id")
            session_url = gift_data.get("session_url")
            
            if not session_id or not session_url:
                return None, "Failed to get checkout session from X."
            
            # Save into DB
            save_order(screen_name, rest_id, plan_key, plan["bdt"], session_id, session_url)
            
            return {
                "session_id": session_id,
                "session_url": session_url,
                "plan": plan
            }, None
        except Exception as e:
            last_err = e
            time.sleep(0.5)
            
    return None, f"Network error creating checkout: {last_err}"

# ==================== STRIPE API ====================

def inspect_stripe_session(session_id):
    url = f"https://api.stripe.com/v1/payment_pages/{session_id}?key={STRIPE_PK}"
    try:
        r = tg_session.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
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
        return None, str(e)

# ==================== TELEGRAM BOT API ====================

def tg_api(method, data=None, timeout=10):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    for attempt in range(3):
        try:
            r = tg_session.post(url, json=data or {}, timeout=timeout)
            return r.json()
        except Exception as e:
            if attempt == 2:
                logger.error(f"Telegram API {method} failed: {e}")
                return {"ok": False, "error": str(e)}
            time.sleep(0.3)

def send_message(chat_id, text, reply_markup=None, parse_mode="Markdown"):
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
    return tg_api("answerCallbackQuery", payload, timeout=5)

def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode="Markdown"):
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
                send_message(chat_id, "⛔ *Access Restricted.*\nThis bot is in private admin mode.")
                return

            if not text:
                return

            # Commands
            if text.startswith("/start") or text.startswith("/help"):
                welcome = (
                    "⚡ *X Premium Gift Fast Automation*\n\n"
                    "Assalam o Alaikum Asad bhai! Bot speed optimized hai.\n\n"
                    "💡 *Kaise use karein:*\n"
                    "• Twitter username bhejein (maslan `@BRIDGR__` ya `@elonmusk`)\n"
                    "• 3 Months ya 6 Months select karein\n"
                    "• Foran official Stripe BDT payment link haasil karein!\n\n"
                    "⚡ *Plans:* \n"
                    "• 🎁 *3 Months:* `300 BDT` (~$2.50)\n"
                    "• 🎁 *6 Months:* `600 BDT` (~$5.00)\n\n"
                    "Commands: `/orders` | `/check` | `/status <id>`"
                )
                send_message(chat_id, welcome)
                return

            elif text.startswith("/check"):
                send_message(chat_id, "🔍 *Testing X Gateway...*")
                ok, msg_res = check_x_cookies()
                if ok:
                    send_message(chat_id, f"✅ *All Systems Active!*\n\n{msg_res}\nGateway: Bangladesh (300/600 BDT Discount)")
                else:
                    send_message(chat_id, f"⚠️ *Status Alert:*\n\n{msg_res}")
                return

            elif text.startswith("/orders"):
                orders = get_recent_orders(5)
                if not orders:
                    send_message(chat_id, "ℹ️ No orders yet. Send a username to start!")
                    return
                
                res = "📋 *Recent Orders:*\n\n"
                for o in orders:
                    u, pk, amt, sid, surl, st, pst, cat = o
                    status_icon = "✅" if pst == "paid" else "⏳"
                    res += (
                        f"{status_icon} *@{u}* — {pk.upper()} ({amt} BDT)\n"
                        f"• Status: `{pst}`\n"
                        f"• [Stripe Checkout]({surl})\n\n"
                    )
                send_message(chat_id, res)
                return

            elif text.startswith("/status"):
                parts = text.split()
                if len(parts) < 2:
                    send_message(chat_id, "Usage: `/status <session_id>`")
                    return
                sid = parts[1].strip()
                info, err = inspect_stripe_session(sid)
                if err:
                    send_message(chat_id, f"❌ Error: {err}")
                    return
                
                icon = "✅ PAID" if info["payment_status"] == "paid" else "⏳ UNPAID"
                msg_reply = (
                    f"📊 *Payment Status:*\n\n"
                    f"• Status: *{icon}*\n"
                    f"• Amount: `{info['total']/100:.2f} {info['currency'].upper()}`\n"
                    f"• Session: `{sid}`"
                )
                send_message(chat_id, msg_reply)
                return

            # Fast greeting / conversational check
            clean_lower = text.lower().strip()
            if clean_lower in ["hi", "hello", "hey", "salam", "aoa", "assalam o alaikum", "kese ho", "kaise ho", "bot", "help", "test"]:
                send_message(chat_id, "👋 *Salam Asad bhai!* Bot bilkul active aur fast hai.\n\nAap mujhe kisi customer ka **Twitter username** bhejein (maslan `@BRIDGR__` ya `@elonmusk`), me foran uske 3M aur 6M ke Stripe payment links bana doonga!")
                return

            # Twitter username lookup
            username = text.strip()
            if "x.com/" in username or "twitter.com/" in username:
                username = username.rstrip("/").split("/")[-1].split("?")[0]
            
            clean_user = username.lstrip("@")
            wait_msg = send_message(chat_id, f"⚡ *Looking up @{clean_user} on Twitter...*")
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
                f"👤 *Twitter Account:*\n\n"
                f"• *User:* `@{user_info['screen_name']}`\n"
                f"• *Name:* {user_info['name']}\n"
                f"• *Rest ID:* `{user_info['rest_id']}`\n"
                f"• *Verified:* {blue_text} | *Status:* {eligibility_text}\n\n"
                f"👇 *Select Plan:*"
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
            
            if data.startswith("check_status:"):
                session_id = data.split(":", 1)[1]
                answer_callback(cq_id, "Checking...")
                info, err = inspect_stripe_session(session_id)
                if err:
                    send_message(chat_id, f"❌ Failed to verify: {err}")
                    return
                
                if info["payment_status"] == "paid":
                    msg_status = (
                        f"🎉 *PAID & DELIVERED!*\n\n"
                        f"✅ `{info['total']/100:.2f} {info['currency'].upper()}` received.\n"
                        f"Twitter Premium has been granted!"
                    )
                else:
                    msg_status = (
                        f"⏳ *Still Unpaid*\n\n"
                        f"• Amount: `{info['total']/100:.2f} {info['currency'].upper()}`\n"
                        f"Waiting for payment on Stripe."
                    )
                send_message(chat_id, msg_status)
                return

            if data.startswith("plan:"):
                parts = data.split(":")
                plan_key = parts[1]
                screen_name = parts[2]
                
                # Debounce: prevent duplicate button clicks
                task_key = (chat_id, plan_key, screen_name)
                with tasks_lock:
                    if task_key in active_tasks:
                        answer_callback(cq_id, "Generating already... please wait a moment!")
                        return
                    active_tasks.add(task_key)
                
                try:
                    plan = PLANS[plan_key]
                    # Immediately answer callback to remove spinner
                    answer_callback(cq_id, f"Generating {plan['title']} link...")
                    
                    user_info = user_cache.get(chat_id)
                    if not user_info or user_info.get("screen_name") != screen_name:
                        user_info, err = lookup_x_user(screen_name)
                        if err:
                            edit_message(chat_id, msg_id, f"❌ Error: {err}")
                            return
                    
                    rest_id = user_info["rest_id"]
                    edit_message(chat_id, msg_id, f"⚡ *Generating {plan['title']} Stripe Link for @{screen_name}...*")
                    
                    result, err = create_gift_checkout(screen_name, rest_id, plan_key)
                    if err:
                        edit_message(chat_id, msg_id, f"❌ *Checkout Generation Failed*\n\n{err}")
                        return
                    
                    session_id = result["session_id"]
                    session_url = result["session_url"]
                    
                    success_text = (
                        f"🎉 *Stripe Gift Checkout Link Created!* 🎉\n\n"
                        f"👤 *Recipient:* `@{screen_name}`\n"
                        f"📦 *Plan:* *{plan['title']}*\n"
                        f"💰 *Cost:* `{plan['bdt']} BDT` ({plan['usd_approx']})\n\n"
                        f"🔗 *Payment URL:*\n"
                        f"{session_url}\n\n"
                        f"📋 *Session ID:*\n`{session_id}`\n\n"
                        f"👉 Ye link customer ko bhejein ya khud pay karein. Payment hote hi Premium active ho jayega!"
                    )
                    
                    markup = {
                        "inline_keyboard": [
                            [
                                {"text": "💳 Open Checkout", "url": session_url}
                            ],
                            [
                                {"text": "🔄 Check Payment Status", "callback_data": f"check_status:{session_id}"}
                            ]
                        ]
                    }
                    edit_message(chat_id, msg_id, success_text, reply_markup=markup)
                finally:
                    with tasks_lock:
                        active_tasks.discard(task_key)
                return

    except Exception as e:
        logger.error(f"Error handling update: {e}", exc_info=True)

def start_bot():
    init_db()
    logger.info("Initializing High-Speed X Gift Bot...")
    
    me = tg_api("getMe")
    if not me.get("ok"):
        logger.error(f"Failed to connect to Telegram: {me}")
        return
    
    bot_user = me["result"]["username"]
    logger.info(f"Bot connected: @{bot_user} (Admin: {ADMIN_CHAT_ID})")
    
    offset = None
    logger.info("Starting High-Speed non-blocking Telegram polling loop...")
    while True:
        try:
            params = {"timeout": 0}
            if offset:
                params["offset"] = offset
            
            res = tg_api("getUpdates", params, timeout=12)
            if res.get("ok"):
                updates = res.get("result", [])
                for u in updates:
                    offset = u["update_id"] + 1
                    # Dispatch to thread pool immediately - NEVER block polling loop!
                    executor.submit(handle_update, u)
            time.sleep(0.4)
        except Exception as e:
            logger.error(f"Polling loop exception: {e}")
            time.sleep(1)

if __name__ == "__main__":
    start_bot()
