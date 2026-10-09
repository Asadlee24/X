import urllib.request
import json

auth_token = "6db315b21b21d55a5a02577ab2b04d3a220c1268"
ct0 = "0c0d71ddfa92485d469ad70b1d535dcd2083a1520b52a2838d93b37f26322e39d5b41df367ba1902d9538d0bf79b49ab02ca0fa0a9695eae707c7e3e68de44d09aa74b28586920240af265f692062367"
bearer = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

url = "https://x.com/i/api/graphql/GqTVJ4S1526tLkxj69xIZw/useOneTimePurchaseGiftMutation"

payload = {
    "variables": {
        "cancel_url": "https://x.com/the195nfts/gift-premium",
        "success_url": "https://x.com/the195nfts/gift-premium/success",
        "external_product_id": "prod_TJXJtpzqCpI36N",
        "gift_recipient": "2091097007930900480"
    },
    "queryId": "GqTVJ4S1526tLkxj69xIZw"
}

headers = {
    "Authorization": f"Bearer {bearer}",
    "Cookie": f"auth_token={auth_token}; ct0={ct0}",
    "X-Csrf-Token": ct0,
    "Content-Type": "application/json",
    "Origin": "https://x.com",
    "Referer": "https://x.com/the195nfts/gift-premium",
    "X-Twitter-Auth-Type": "OAuth2Session",
    "X-Twitter-Active-User": "yes",
    "X-Twitter-Client-Language": "en",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("RESULT:")
        print(json.dumps(data, indent=2))
except Exception as e:
    print("ERROR:", e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
