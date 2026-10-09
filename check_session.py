import urllib.request
import urllib.parse
import json

session_id = "cs_live_a1Q080KbYAg5GkILLZvKjpJucs7MZ3xVqoKO0KFp5MH8K2C5DtpTMvEVCn"
pk = "pk_live_51Ika5JA3KZ32dPo1Uxw4aqV0ZMlJ6ATznaCs2P3nJCtDAwj6qw0ACmoab3PrB9eGfrWmxHVtrcWZcSohktLW26Ji00gnr09tHq"

url = f"https://api.stripe.com/v1/payment_pages/{session_id}?key={pk}"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("Status:", data.get("status"))
        print("Currency:", data.get("currency"))
        print("Total:", data.get("total"))
        print("Line items:", data.get("line_item_group"))
except Exception as e:
    print("Error:", e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
