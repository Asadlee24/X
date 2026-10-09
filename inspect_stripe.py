import urllib.request
import re
import json

url = 'https://checkout.stripe.com/f/pay/cs_live_a1aSOV3NPwuILolyb8xo2gPKuNU9kks03Ljtu97jsST0gYEZjPbndG7gze'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req).read().decode('utf-8')

with open('stripe_checkout.html', 'w', encoding='utf-8') as f:
    f.write(html)

currencies = re.findall(r'"currency":\s*"([^"]+)"', html)
totals = re.findall(r'"total":\s*(\d+)', html)
pk = re.findall(r'pk_live_[A-Za-z0-9]+', html)
titles = re.findall(r'"name":\s*"([^"]+)"', html)

print("Currencies:", currencies[:5])
print("Totals:", totals[:5])
print("Stripe PK:", set(pk))
print("Titles:", titles[:5])
