import urllib.request
import urllib.parse
import json
import sys

PK = "pk_live_51Ika5JA3KZ32dPo1Uxw4aqV0ZMlJ6ATznaCs2P3nJCtDAwj6qw0ACmoab3PrB9eGfrWmxHVtrcWZcSohktLW26Ji00gnr09tHq"

def inspect_session(session_id):
    url = f"https://api.stripe.com/v1/payment_pages/{session_id}?key={PK}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

def pay_live():
    session_id = "cs_live_a1Q080KbYAg5GkILLZvKjpJucs7MZ3xVqoKO0KFp5MH8K2C5DtpTMvEVCn"
    card_num = "REMOVED_FOR_SAFETY"
    exp_m = "00"
    exp_y = "0000"
    cvc = "000"
    name = "Customer"
    email = "email@example.com"
    recipient_user = "the195nfts"

    print("==================================================")
    print("STEP 0: Inspecting session...")
    page = inspect_session(session_id)
    currency = page.get("currency", "").lower()
    line_group = page.get("line_item_group", {})
    due = line_group.get("due")
    print(f"Status: {page.get('status')}")
    print(f"Currency: {currency}")
    print(f"Due Amount: {due} ({due/100:.2f} BDT)")

    if currency != "bdt":
        print(f"ERROR: Currency is {currency}, expected bdt! ABORTING.")
        return
    if due != 30000:
        print(f"ERROR: Amount is {due}, expected 30000! ABORTING.")
        return

    print("==================================================")
    print("STEP 1: Initializing checkout session...")
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
    print(f"Checksum: {checksum}")

    print("==================================================")
    print("STEP 2: Creating PaymentMethod for card ending 4223...")
    pm_url = "https://api.stripe.com/v1/payment_methods"
    pm_data = urllib.parse.urlencode({
        "key": PK,
        "type": "card",
        "card[number]": card_num,
        "card[exp_month]": exp_m,
        "card[exp_year]": exp_y,
        "card[cvc]": cvc,
        "billing_details[name]": name,
        "billing_details[email]": email,
        "billing_details[address][country]": "BD",
        "billing_details[address][city]": "Dhaka",
        "billing_details[address][line1]": "House 12, Road 5, Gulshan",
        "billing_details[address][postal_code]": "1212"
    }).encode('utf-8')
    pm_req = urllib.request.Request(pm_url, data=pm_data, headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(pm_req) as resp:
        pm = json.loads(resp.read().decode('utf-8'))
        pm_id = pm.get("id")
    print(f"PaymentMethod created: {pm_id}")

    print("==================================================")
    print("STEP 3: Confirming payment for 300 BDT...")
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

    try:
        with urllib.request.urlopen(confirm_req) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            print("CONFIRM RESULT:")
            print(json.dumps(result, indent=2))
            intent = result.get("payment_intent", {})
            intent_status = intent.get("status") if isinstance(intent, dict) else ""
            print(f"Overall Status: {result.get('status')}")
            print(f"Payment Status: {result.get('payment_status')}")
            print(f"Intent Status: {intent_status}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        err_body = e.read().decode('utf-8')
        print(err_body)

if __name__ == "__main__":
    pay_live()
