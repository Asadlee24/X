import urllib.request
import json

url = 'https://api.x.com/1.1/account/settings.json'
headers = {
    'Authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
    'Cookie': 'auth_token=85c5c7abef17325d4a3c3ff96dca2739d023e051; ct0=07804aa7f885de4501e48453842f65f56cc530ded0e9523b9abc3184cd6bef454e43ec596f5b5d653c5c682b6491c936de6d40e2d186377c272401d538fe9f933322d1bf06521d9bf1cc4977281b4879',
    'X-Csrf-Token': '07804aa7f885de4501e48453842f65f56cc530ded0e9523b9abc3184cd6bef454e43ec596f5b5d653c5c682b6491c936de6d40e2d186377c272401d538fe9f933322d1bf06521d9bf1cc4977281b4879',
    'X-Twitter-Auth-Type': 'OAuth2Session',
    'X-Twitter-Active-User': 'yes'
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        d = json.loads(resp.read().decode('utf-8'))
        print('Screen name:', d.get('screen_name'))
        print('Country code:', d.get('country_code'))
        print('Language:', d.get('language'))
        print('Time zone:', d.get('time_zone'))
except Exception as e:
    print('Err:', e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
