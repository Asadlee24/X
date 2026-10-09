#!/bin/bash
PROXY="http://owcmizouuazq-region-BD:owcmizouuazq@us.arxlabs.io:3010"
AUTH_TOKEN="85c5c7abef17325d4a3c3ff96dca2739d023e051"
CT0="07804aa7f885de4501e48453842f65f56cc530ded0e9523b9abc3184cd6bef454e43ec596f5b5d653c5c682b6491c936de6d40e2d186377c272401d538fe9f933322d1bf06521d9bf1cc4977281b4879"
BEARER="AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

URL="https://x.com/i/api/graphql/Se1Bp6zcNnuXYXRecV2qLA/useSubscriptionProductDetailsByRestIdQuery?variables=%7B%22stripeId%22%3A%22prod_TJXJtpzqCpI36N%22%7D&features=%7B%22subscriptions_marketing_page_fetch_promotions%22%3Atrue%7D"

curl -s -x "$PROXY" \
  -H "Authorization: Bearer $BEARER" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  -H "Origin: https://x.com" \
  -H "Referer: https://x.com/the195nfts/gift-premium" \
  "$URL"
echo ""
