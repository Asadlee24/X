import urllib.request
import json

proxy = urllib.request.ProxyHandler({
    'http': 'http://owcmizouuazq-region-BD:owcmizouuazq@us.arxlabs.io:3010',
    'https': 'http://owcmizouuazq-region-BD:owcmizouuazq@us.arxlabs.io:3010'
})
opener = urllib.request.build_opener(proxy)

try:
    with opener.open('http://ip-api.com/json', timeout=10) as r:
        print("ip-api:", r.read().decode())
except Exception as e:
    print("ip-api error:", e)

try:
    with opener.open('https://api.ipify.org?format=json', timeout=10) as r:
        print("ipify:", r.read().decode())
except Exception as e:
    print("ipify error:", e)
