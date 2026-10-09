import urllib.request
import re
import json

url = "https://x.com/?xgift_region=123"

proxy_handler = urllib.request.ProxyHandler({
    'http': 'http://owcmizouuazq-region-BD:owcmizouuazq@us.arxlabs.io:3010',
    'https': 'http://owcmizouuazq-region-BD:owcmizouuazq@us.arxlabs.io:3010'
})
opener = urllib.request.build_opener(proxy_handler)

headers = {
    "Cookie": "auth_token=85c5c7abef17325d4a3c3ff96dca2739d023e051; ct0=07804aa7f885de4501e48453842f65f56cc530ded0e9523b9abc3184cd6bef454e43ec596f5b5d653c5c682b6491c936de6d40e2d186377c272401d538fe9f933322d1bf06521d9bf1cc4977281b4879",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

req = urllib.request.Request(url, headers=headers)
try:
    with opener.open(req, timeout=15) as res:
        html = res.read().decode('utf-8', errors='ignore')
        print("HTML length:", len(html))
        # search for country
        match1 = re.search(r'"country":\s*"([^"]+)"', html)
        if match1:
            print("Found country in JSON:", match1.group(1))
        # search all occurrences of country
        all_countries = re.findall(r'"country":\s*"([^"]+)"', html)
        print("All countries found:", set(all_countries))
except Exception as e:
    print("Error:", e)
