import urllib.request
import json

url = "https://x.com/i/api/graphql/Se1Bp6zcNnuXYXRecV2qLA/useSubscriptionProductDetailsByRestIdQuery?variables=%7B%22stripeId%22%3A%22prod_TJXJtpzqCpI36N%22%7D&features=%7B%22subscriptions_marketing_page_fetch_promotions%22%3Atrue%7D"

proxy_handler = urllib.request.ProxyHandler({
    'http': 'http://owcmizouuazq-region-BD:owcmizouuazq@us.arxlabs.io:3010',
    'https': 'http://owcmizouuazq-region-BD:owcmizouuazq@us.arxlabs.io:3010'
})
opener = urllib.request.build_opener(proxy_handler)

# Guest token or just Bearer without auth_token
headers = {
    "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

req = urllib.request.Request(url, headers=headers)
try:
    with opener.open(req, timeout=15) as res:
        print("Anonymous Quote Result:")
        print(res.read().decode('utf-8'))
except Exception as e:
    print("Error:", e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
