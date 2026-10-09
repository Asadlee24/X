import urllib.request
import urllib.parse
import json
import sys

PK = "pk_live_51Ika5JA3KZ32dPo1Uxw4aqV0ZMlJ6ATznaCs2P3nJCtDAwj6qw0ACmoab3PrB9eGfrWmxHVtrcWZcSohktLW26Ji00gnr09tHq"

def inspect_session(session_id):
    url = f"https://api.stripe.com/v1/payment_pages/{session_id}?key={PK}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        return data

def pay_session(session_id, card_num, exp_m, exp_y, cvc, name, email, recipient_user):
    # Step 0: Inspect session to verify amount and currency
    print(f"[*] Checking session {session_id}...")
    page = inspect_session(session_id)
    currency = page.get("currency", "").lower()
    line_group = page.get("line_item_group", {})
    due = line_group.get("due")
    print(f"[*] Session Currency: {currency}, Total Due: {due}")

    if currency != "bdt":
        raise Exception(f"ABORT: Currency is {currency}, not BDT! Won't charge card.")
    if due != 30000:
        raise Exception(f"ABORT: Amount is {due}, not 30000 minor units (300 BDT)! Won't charge card.")

    # Step 1: Init payment page to get init_checksum
    print("[*] Initializing payment page...")
    init_url = f"https://api.stripe.com/v1/payment_pages/{session_id}/init"
    init_data = urllib.parse.urlencode({
        "key": PK,
        "browser_locale": "en",
        "redirect_type": "url"
    }).encode('utf-8')
    init_req = urllib.request.Request(init_url, data=init_data, headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(init_req) as resp:
        init_page = json.loads(resp.read().decode('utf-8'))
        checksum = init_page.get("init_checksum")
    print(f"[+] Init successful! Checksum obtained: {checksum[:10]}...")

    # Step 2: Tokenize card -> create PaymentMethod
    print("[*] Creating Stripe PaymentMethod...")
    pm_url = "https://api.stripe.com/v1/payment_methods"
    pm_data = urllib.parse.urlencode({
        "key": PK,
        "type": "card",
        "card[number]": card_num,
        "card[exp_month]": exp_m,
        "card[exp_year]": exp_y,
        "card[cvc]": cvc,
        "billing_details[name]": name,
        "billing_details[email]": email
    }).encode('utf-8')
    pm_req = urllib.request.Request(pm_url, data=pm_data, headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(pm_req) as resp:
        pm = json.loads(resp.read().decode('utf-8'))
        pm_id = pm.get("id")
    print(f"[+] Card tokenized successfully! PaymentMethod ID: {pm_id}")

    # Step 3: Confirm payment
    print("[*] Confirming payment for 300 BDT...")
    confirm_url = f"https://api.stripe.com/v1/payment_pages/{session_id}/confirm"
    confirm_data = urllib.parse.urlencode({
        "key": PK,
        "payment_method": pm_id,
        "expected_amount": "30000",
        "expected_payment_method_type": "card",
        "init_checksum": checksum,
        "return_url": f"https://x.com/{recipient_user}/gift-premium/success"
    }).encode('utf-8')
    confirm_req = urllib.request.Request(confirm_url, data=confirm_data, headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(confirm_req) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        status = result.get("status")
        payment_status = result.get("payment_status")
        print(f"[SUCCESS] Status: {status}, Payment Status: {payment_status}")
        return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        s_id = sys.argv[1]
        print(json.dumps(inspect_session(s_id), indent=2))
