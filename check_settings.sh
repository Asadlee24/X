#!/bin/bash
AUTH_TOKEN="85c5c7abef17325d4a3c3ff96dca2739d023e051"
CT0="07804aa7f885de4501e48453842f65f56cc530ded0e9523b9abc3184cd6bef454e43ec596f5b5d653c5c682b6491c936de6d40e2d186377c272401d538fe9f933322d1bf06521d9bf1cc4977281b4879"
BEARER="AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

curl -s "https://x.com/i/api/1.1/account/settings.json" \
  -H "Authorization: Bearer $BEARER" \
  -H "Cookie: auth_token=$AUTH_TOKEN; ct0=$CT0" \
  -H "X-Csrf-Token: $CT0" \
  -H "X-Twitter-Auth-Type: OAuth2Session" \
  -H "X-Twitter-Active-User: yes"
