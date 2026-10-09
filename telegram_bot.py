"""
X (Twitter) Premium Gift Automation Telegram Bot
Private Admin Bot for Asad (@Asadlee24 / Chat ID: 7080909965)

Features:
- Dedicated proxy routing:
  • Bangladesh proxy for Twitter X mutations (unlocks 300 BDT / 600 BDT discount prices)
  • US proxy for ultra-fast and reliable Telegram Bot connectivity
- Look up any Twitter/X handle to check eligibility & details
- Automatically generate 3 Months (300 BDT) and 6 Months (600 BDT) Stripe Checkout Gift Links
- Check live payment status directly from Stripe
- Order tracking in local SQLite database
- Zero automated card charging: 100% safe checkout link generation
"""

import os
import sys
import time
import json
import sqlite3
import logging
import requests
from datetime import datetime

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

# Twitter / X Credentials (from init_secrets.json)
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

# Logging configuration
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("XGiftBot")

# ==================== DATABASE ====================
DB_PATH = os.path.join(os.path.dirname(__file__), "orders.db")

def init_db():
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO orders (created_at, username, recipient_id, plan_key, amount_bdt, session_id, session_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (datetime.utcnow().isoformat(), username, recipient_id, plan_key, amount_bdt, session_id, session_url))
    conn.commit()
    conn.close()

def update_order_status(session_id, status, payment_status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    paid_at = datetime.utcnow().isoformat() if payment_status == "paid" else None
    c.execute("""
        UPDATE orders 
        SET status = ?, payment_status = ?, paid_at = COALESCE(paid_at, ?)
        WHERE session_id = ?
    """, (status, payment_status, paid_at, session_id))
    conn.commit()
    conn.close()

def get_recent_orders(limit=5):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT username, plan_key, amount_bdt, session_id, session_url, status, payment_status, created_at
        FROM orders ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

# ==================== ROBUST HTTP CLIENT ====================

def robust_req(method, url, proxies, max_retries=4, timeout=12, **kwargs):
    last_err = None
    for attempt in range(max_retries):
        try:
            r = requests.request(method, url, proxies=proxies, timeout=timeout, **kwargs)
            return r
        except Exception as e:
            last_err = e
            time.sleep(0.5 + attempt * 0.5)
    raise last_err

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
    """Verify if auth_token and ct0 cookies are valid"""
    try:
        url = "https://x.com/i/api/graphql/kn8hCE6bHstQV2MtfYDTKg/PremiumGiftingQuery?variables=" + requests.utils.quote(json.dumps({"screenName": "elonmusk"}))
        r = robust_req("GET", url, proxies=BD_PROXIES, headers=get_x_headers("elonmusk"), timeout=15)
        if r.status_code == 200:
            return True, "Cookies are valid and connected to X."
        return False, f"HTTP Error {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def lookup_x_user(screen_name):
    """Query Twitter user details and check gifting eligibility"""
    screen_name = screen_name.strip().lstrip("@")
    if "/" in screen_name:
        screen_name = screen_name.split("/")[-1]
    
    url = "https://x.com/i/api/graphql/kn8hCE6bHstQV2MtfYDTKg/PremiumGiftingQuery?variables=" + requests.utils.quote(json.dumps({"screenName": screen_name}))
    try:
        r = robust_req("GET", url, proxies=BD_PROXIES, headers=get_x_headers(screen_name), timeout=15)
    except Exception as e:
        return None, f"Network error contacting Twitter: {e}"
    
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

def create_gift_checkout(screen_name, rest_id, plan_key):
    """Calls useOneTimePurchaseGiftMutation to generate Stripe checkout session"""
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
    
    try:
        r = robust_req("POST", url, proxies=BD_PROXIES, json=payload, headers=get_x_headers(screen_name), timeout=20)
    except Exception as e:
        return None, f"Network error creating checkout: {e}"
    
    if r.status_code != 200:
        return None, f"X API error (HTTP {r.status_code}): {r.text[:150]}"
    
    res = r.json()
    errors = res.get("errors", [])
    if errors:
        msg = errors[0].get("message", "Unknown error from X")
        return None, f"X Error: {msg}"
    
    gift_data = res.get("data", {}).get("onetimepurchase_gift", {})
    session_id = gift_data.get("session_id")
    session_url = gift_data.get("session_url")
    
    if not session_id or not session_url:
        return None, "Failed to get checkout session from X response."
    
    # Save into DB
    save_order(screen_name, rest_id, plan_key, plan["bdt"], session_id, session_url)
    
    return {
        "session_id": session_id,
        "session_url": session_url,
        "plan": plan
    }, None

# ==================== STRIPE API ====================

def inspect_stripe_session(session_id):
    """Check payment status of a Stripe checkout session"""
    url = f"https://api.stripe.com/v1/payment_pages/{session_id}?key={STRIPE_PK}"
    try:
        r = robust_req("GET", url, proxies=TG_PROXIES, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
        if r.status_code != 200:
            return None, f"Stripe HTTP {r.status_code}"
        data = r.json()
        status = data.get("status", "unknown") # open, complete, expired
        payment_status = data.get("payment_status", "unpaid") # paid, unpaid
        total = data.get("total", 0)
        currency = data.get("currency", "")
        
        # update DB
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

def tg_api(method, data=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    try:
        r = robust_req("POST", url, proxies=TG_PROXIES, json=data or {}, timeout=25)
        return r.json()
    except Exception as e:
        logger.error(f"Telegram API request failed: {e}")
        return {"ok": False, "error": str(e)}

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
    return tg_api("answerCallbackQuery", payload)

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

# In-memory user state for lookup
user_cache = {}

def handle_update(update):
    # Message handler
    if "message" in update:
        msg = update["message"]
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "").strip()
        
        # Security: restrict to Admin only
        if chat_id != ADMIN_CHAT_ID:
            logger.warning(f"Unauthorized message from chat_id={chat_id}: {text}")
            send_message(chat_id, "⛔ *Access Restricted.*\nThis bot is in private admin mode.")
            return

        if not text:
            return

        # Commands
        if text.startswith("/start") or text.startswith("/help"):
            welcome = (
                "👋 *Assalam o Alaikum Asad!*\n\n"
                "🚀 *X (Twitter) Premium Gift Automation Bot is Active.*\n\n"
                "💡 *How to Sell / Generate Gift Links:*\n"
                "1️⃣ Send any Twitter username (e.g. `@the195nfts` or `elonmusk`)\n"
                "2️⃣ Select the Plan: **3 Months** or **6 Months**\n"
                "3️⃣ The bot generates the official **Stripe Payment Link** in BDT\n"
                "4️⃣ Send the link to the customer (or pay yourself), and Twitter grants Premium immediately!\n\n"
                "⚡ *Plans & BD Pricing:*\n"
                "• 🎁 *3 Months:* `300 BDT` (~$2.50 USD)\n"
                "• 🎁 *6 Months:* `600 BDT` (~$5.00 USD)\n\n"
                "🛠 *Other Commands:*\n"
                "• `/orders` - View recent generated links & statuses\n"
                "• `/status <session_id>` - Check payment status of an order\n"
                "• `/check` - Check X cookies & proxy health"
            )
            send_message(chat_id, welcome)
            return

        elif text.startswith("/check"):
            send_message(chat_id, "🔍 *Testing X cookies and BD Gateway...*")
            ok, msg_res = check_x_cookies()
            if ok:
                send_message(chat_id, f"✅ *All Systems Operational!*\n\n{msg_res}\nGateway: Bangladesh Proxy (Active & Connected)")
            else:
                send_message(chat_id, f"⚠️ *Status Alert:*\n\n{msg_res}")
            return

        elif text.startswith("/orders"):
            orders = get_recent_orders(5)
            if not orders:
                send_message(chat_id, "ℹ️ No orders generated yet. Send a Twitter username to start!")
                return
            
            res = "📋 *Recent Orders & Links:*\n\n"
            for o in orders:
                u, pk, amt, sid, surl, st, pst, cat = o
                status_icon = "✅" if pst == "paid" else "⏳"
                res += (
                    f"{status_icon} *@{u}* — {pk.upper()} ({amt} BDT)\n"
                    f"• Status: `{pst}` ({st})\n"
                    f"• [Payment Link]({surl})\n"
                    f"• ID: `{sid[:20]}...`\n\n"
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
                send_message(chat_id, f"❌ Error checking session: {err}")
                return
            
            icon = "✅ PAID" if info["payment_status"] == "paid" else "⏳ UNPAID"
            msg_reply = (
                f"📊 *Payment Status Check:*\n\n"
                f"• Payment: *{icon}*\n"
                f"• Page Status: `{info['status']}`\n"
                f"• Amount: `{info['total']/100:.2f} {info['currency'].upper()}`\n"
                f"• Session: `{sid}`"
            )
            send_message(chat_id, msg_reply)
            return

        # Default text -> Twitter username lookup
        username = text.strip()
        send_message(chat_id, f"🔍 *Checking @{username.lstrip('@')} on Twitter...*")
        
        user_info, err = lookup_x_user(username)
        if err:
            send_message(chat_id, f"❌ {err}")
            return
        
        # Cache user info
        user_cache[chat_id] = user_info
        
        eligibility_text = "✅ Eligible for Premium Gift" if user_info["eligible"] else "⚠️ Notice: User has Blue or Ineligible flag"
        blue_text = "Yes (Subscribed)" if user_info["is_blue"] else "No"
        
        reply = (
            f"👤 *Twitter Account Found!*\n\n"
            f"• *Username:* `@{user_info['screen_name']}`\n"
            f"• *Name:* {user_info['name']}\n"
            f"• *Rest ID:* `{user_info['rest_id']}`\n"
            f"• *Blue Verified:* {blue_text}\n"
            f"• *Status:* {eligibility_text}\n\n"
            f"👇 *Select plan to generate official Stripe link:*"
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
        send_message(chat_id, reply, reply_markup=markup)
        return

    # Callback Query handler
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
            edit_message(chat_id, msg_id, "❌ Action cancelled. Send another username whenever you're ready!")
            return
        
        if data.startswith("check_status:"):
            session_id = data.split(":", 1)[1]
            answer_callback(cq_id, "Checking payment status...")
            info, err = inspect_stripe_session(session_id)
            if err:
                send_message(chat_id, f"❌ Failed to verify status: {err}")
                return
            
            if info["payment_status"] == "paid":
                msg_status = (
                    f"🎉 *PAYMENT CONFIRMED!*\n\n"
                    f"✅ Amount Paid: `{info['total']/100:.2f} {info['currency'].upper()}`\n"
                    f"Session: `{session_id}`\n\n"
                    f"Twitter Premium has been delivered to the recipient!"
                )
            else:
                msg_status = (
                    f"⏳ *Status: Still Unpaid*\n\n"
                    f"• Status: `{info['status']}` (Payment: `{info['payment_status']}`)\n"
                    f"• Amount Due: `{info['total']/100:.2f} {info['currency'].upper()}`\n"
                    f"Session: `{session_id}`\n\n"
                    f"Waiting for customer/buyer to pay on Stripe."
                )
            send_message(chat_id, msg_status)
            return

        if data.startswith("plan:"):
            parts = data.split(":")
            plan_key = parts[1]
            screen_name = parts[2]
            
            user_info = user_cache.get(chat_id)
            if not user_info or user_info.get("screen_name") != screen_name:
                user_info, err = lookup_x_user(screen_name)
                if err:
                    answer_callback(cq_id, "Error looking up user", show_alert=True)
                    return
            
            rest_id = user_info["rest_id"]
            plan = PLANS[plan_key]
            
            answer_callback(cq_id, f"Generating {plan['title']} link...")
            edit_message(chat_id, msg_id, f"⏳ *Generating official Stripe Checkout for @{screen_name} ({plan['title']})...*\nConnecting to X Bangladesh gateway...")
            
            result, err = create_gift_checkout(screen_name, rest_id, plan_key)
            if err:
                edit_message(chat_id, msg_id, f"❌ *Checkout Generation Failed*\n\n{err}\n\n💡 If the user already received Premium recently, Twitter will reject new gifts.")
                return
            
            session_id = result["session_id"]
            session_url = result["session_url"]
            
            success_text = (
                f"🎉 *X Premium Gift Link Created!* 🎉\n\n"
                f"👤 *Recipient:* `@{screen_name}`\n"
                f"🆔 *Rest ID:* `{rest_id}`\n"
                f"📦 *Plan:* *{plan['title']}*\n"
                f"💰 *Cost:* `{plan['bdt']} BDT` ({plan['usd_approx']})\n\n"
                f"🔗 *Stripe Checkout Link:*\n"
                f"{session_url}\n\n"
                f"📋 *Session ID:*\n`{session_id}`\n\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💡 *Selling Instructions:*\n"
                f"1. Give this link to the customer OR open it yourself to pay with any card.\n"
                f"2. Once paid, X activates the Premium subscription automatically!\n"
                f"3. Click below to verify payment status anytime."
            )
            
            markup = {
                "inline_keyboard": [
                    [
                        {"text": "💳 Open Checkout in Browser", "url": session_url}
                    ],
                    [
                        {"text": "🔄 Check Payment Status", "callback_data": f"check_status:{session_id}"}
                    ]
                ]
            }
            edit_message(chat_id, msg_id, success_text, reply_markup=markup)
            return

def start_bot():
    """Main long polling loop with automatic error recovery"""
    init_db()
    logger.info("Initializing X Gift Telegram Bot...")
    
    # Test connection
    me = tg_api("getMe")
    if not me.get("ok"):
        logger.error(f"Failed to connect to Telegram: {me}")
        return
    
    bot_user = me["result"]["username"]
    logger.info(f"Bot connected: @{bot_user} (Admin: {ADMIN_CHAT_ID})")
    
    # Notify admin that bot is running
    notify_text = (
        "🟢 *X Premium Gift Bot is ONLINE!*\n\n"
        "Bhai bot active ho gaya hai. Aap mujhe Twitter username bhej kar 3 months ya 6 months ka link generate kar sakte hain!"
    )
    send_message(ADMIN_CHAT_ID, notify_text)
    
    offset = None
    logger.info("Starting Telegram polling loop...")
    while True:
        try:
            params = {"timeout": 20}
            if offset:
                params["offset"] = offset
            
            res = tg_api("getUpdates", params)
            if res.get("ok"):
                updates = res.get("result", [])
                for u in updates:
                    offset = u["update_id"] + 1
                    try:
                        handle_update(u)
                    except Exception as err:
                        logger.error(f"Error handling update: {err}", exc_info=True)
            else:
                time.sleep(2)
        except Exception as e:
            logger.error(f"Polling loop exception: {e}")
            time.sleep(3)

if __name__ == "__main__":
    start_bot()
