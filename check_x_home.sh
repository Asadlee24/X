#!/bin/bash
PROXY="http://owcmizouuazq-region-BD:owcmizouuazq@us.arxlabs.io:3010"
AUTH_TOKEN="85c5c7abef17325d4a3c3ff96dca2739d023e051"
CT0="07804aa7f885de4501e48453842f65f56cc530ded0e9523b9abc3184cd6bef454e43ec596f5b5d653c5c682b6491c936de6d40e2d186377c272401d538fe9f933322d1bf06521d9bf1cc4977281b4879"

curl -s -x "$PROXY" \
  -H "Cookie: auth_token=$AUTH_TOKEN; ct0=$CT0" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36" \
  "https://x.com/?xgift_region=123" > /tmp/x_home.html

grep -o '"country":"[^"]*"' /tmp/x_home.html | head -n 10
grep -o '"currency":"[^"]*"' /tmp/x_home.html | head -n 10
