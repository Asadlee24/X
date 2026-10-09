#!/bin/bash

PROXY="http://owcmizouuazq-region-BD:owcmizouuazq@us.arxlabs.io:3010"
AUTH_TOKEN="6db315b21b21d55a5a02577ab2b04d3a220c1268"
CT0="0c0d71ddfa92485d469ad70b1d535dcd2083a1520b52a2838d93b37f26322e39d5b41df367ba1902d9538d0bf79b49ab02ca0fa0a9695eae707c7e3e68de44d09aa74b28586920240af265f692062367"
BEARER="AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

PAYLOAD='{
  "variables": {
    "cancel_url": "https://x.com/the195nfts/gift-premium",
    "success_url": "https://x.com/the195nfts/gift-premium/success",
    "external_product_id": "prod_TJXJtpzqCpI36N",
    "gift_recipient": "2091097007930900480"
  },
  "queryId": "GqTVJ4S1526tLkxj69xIZw"
}'

curl -s -x "$PROXY" \
  -X POST "https://x.com/i/api/graphql/GqTVJ4S1526tLkxj69xIZw/useOneTimePurchaseGiftMutation" \
  -H "Authorization: Bearer $BEARER" \
  -H "Cookie: auth_token=$AUTH_TOKEN; ct0=$CT0" \
  -H "X-Csrf-Token: $CT0" \
  -H "Content-Type: application/json" \
  -H "Origin: https://x.com" \
  -H "Referer: https://x.com/the195nfts/gift-premium" \
  -H "X-Twitter-Auth-Type: OAuth2Session" \
  -H "X-Twitter-Active-User: yes" \
  -H "X-Twitter-Client-Language: en" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -d "$PAYLOAD"
