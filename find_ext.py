import json

with open('/mnt/c/Users/Aftab/AppData/Local/Google/Chrome/User Data/Default/Preferences', 'r', encoding='utf-8') as f:
    d = json.load(f)

exts = d.get('extensions', {}).get('settings', {})
for k, v in exts.items():
    p = v.get('path', '')
    name = v.get('manifest', {}).get('name', '')
    print(f"ID: {k} | Name: {name} | Path: {p}")
