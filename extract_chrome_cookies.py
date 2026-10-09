import os
import json
import base64
import sqlite3
import ctypes
from ctypes import wintypes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ('cbData', wintypes.DWORD),
        ('pbData', ctypes.POINTER(ctypes.c_byte))
    ]

def decrypt_dpapi(encrypted_bytes):
    blob_in = DATA_BLOB(len(encrypted_bytes), ctypes.cast(ctypes.create_string_buffer(encrypted_bytes), ctypes.POINTER(ctypes.c_byte)))
    blob_out = DATA_BLOB()
    if ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        data = ctypes.string_at(blob_out.pbData, blob_out.cbData)
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
        return data
    else:
        raise Exception("CryptUnprotectData failed")

def get_encryption_key():
    local_state_path = r"C:\Users\Aftab\AppData\Local\Google\Chrome\User Data\Local State"
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    encrypted_key = encrypted_key[5:] # strip DPAPI prefix
    return decrypt_dpapi(encrypted_key)

def copy_locked_file(src, dst):
    GENERIC_READ = 0x80000000
    FILE_SHARE_READ = 0x00000001
    FILE_SHARE_WRITE = 0x00000002
    FILE_SHARE_DELETE = 0x00000004
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80

    handle = ctypes.windll.kernel32.CreateFileW(
        src, GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None
    )
    if handle == -1:
        raise Exception(f"Failed to open locked file: {src}")

    content = bytearray()
    buffer = ctypes.create_string_buffer(65536)
    bytes_read = wintypes.DWORD()
    while True:
        success = ctypes.windll.kernel32.ReadFile(handle, buffer, 65536, ctypes.byref(bytes_read), None)
        if not success or bytes_read.value == 0:
            break
        content.extend(buffer.raw[:bytes_read.value])
    ctypes.windll.kernel32.CloseHandle(handle)

    with open(dst, "wb") as f:
        f.write(content)

def decrypt_cookie_val(encrypted_val, key):
    if not encrypted_val:
        return ""
    if encrypted_val[:3] in (b'v10', b'v20'):
        nonce = encrypted_val[3:15]
        ciphertext = encrypted_val[15:]
        aesgcm = AESGCM(key)
        try:
            return aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8', errors='ignore')
        except:
            return ""
    else:
        try:
            return decrypt_dpapi(encrypted_val).decode('utf-8', errors='ignore')
        except:
            return ""

def get_x_cookies():
    key = get_encryption_key()
    for profile in ["Profile 7", "Default", "Profile 1", "Profile 2", "Profile 6", "Profile 8", "Profile 13"]:
        db_path = rf"C:\Users\Aftab\AppData\Local\Google\Chrome\User Data\{profile}\Network\Cookies"
        if not os.path.exists(db_path):
            continue
        temp_db = rf"C:\Users\Aftab\x_gift_bot\temp_cookies_{profile.replace(' ', '_')}.db"
        try:
            copy_locked_file(db_path, temp_db)
        except Exception as e:
            continue

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name, value, encrypted_value FROM cookies WHERE host_key LIKE '%x.com%'")
        rows = cursor.fetchall()
        cookies = {}
        for name, value, enc in rows:
            if not value:
                value = decrypt_cookie_val(enc, key)
            cookies[name] = value
        conn.close()
        try: os.remove(temp_db)
        except: pass
        if "auth_token" in cookies:
            print(f"=== FOUND X COOKIES IN {profile} ===")
            print("auth_token:", cookies.get("auth_token"))
            print("ct0:", cookies.get("ct0"))
            print("twid:", cookies.get("twid"))
            cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items() if v)
            with open(rf"C:\Users\Aftab\x_gift_bot\x_cookies_{profile.replace(' ', '_')}.txt", "w", encoding="utf-8") as f:
                f.write(cookie_header)
            return cookies

if __name__ == "__main__":
    get_x_cookies()
