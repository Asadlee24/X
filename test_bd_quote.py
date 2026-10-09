import urllib.request
import json

url = "https://x.com/i/api/graphql/Se1Bp6zcNnuXYXRecV2qLA/useSubscriptionProductDetailsByRestIdQuery?variables=%7B%22stripeId%22%3A%22prod_TJXJtpzqCpI36N%22%7D&features=%7B%22subscriptions_marketing_page_fetch_promotions%22%3Atrue%7D"

proxy_handler = urllib.request.ProxyHandler({
    'http': 'http://owcmizouuazq-region-BD:owcmizouuazq@us.arxlabs.io:3010',
    'https': 'http://owcmizouuazq-region-BD:owcmizouuazq@us.arxlabs.io:3010'
})
opener = urllib.request.build_opener(proxy_handler)

headers = {
    "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
    "Cookie": "auth_token=519770623e1d09bc0b4ec8f32e8ae125f619b342; ct0=a1a6e1f9b87e6f7404a65bf2804125d3f0ccdf3250d672e439dac3e45ca83d7a4c4d164df7044cf18ba9f5d3ef85bf5ce61512968d31337a002e761bd740186d06abe949b6336bb645ace61d0655b293",
    "X-Csrf-Token": "a1a6e1f9b87e6f7404a65bf2804125d3f0ccdf3250d672e439dac3e45ca83d7a4c4d164df7044cf18ba9f5d3ef85bf5ce61512968d31337a002e761bd740186d06abe949b6336bb645ace61d0655b293",
    "X-Twitter-Auth-Type": "OAuth2Session",
    "X-Twitter-Active-User": "yes",
    "Origin": "https://x.com",
    "Referer": "https://x.com/the195nfts/gift-premium",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

req = urllib.request.Request(url, headers=headers)
try:
    with opener.open(req, timeout=15) as res:
        data = res.read().decode('utf-8')
        print("STATUS:", res.status)
        print("DATA:", data)
except Exception as e:
    print("ERROR:", e)
