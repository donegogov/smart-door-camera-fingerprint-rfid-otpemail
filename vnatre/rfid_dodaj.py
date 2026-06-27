#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# rfid_dodaj.py - VNATRE: presmetaj hash od (uid+token+salt) i zachuvaj vo korisnici.json
# Gi vnesuvash uid i token shto gi dobi od rfid_zapis.py (nadvor).

import hashlib
import json
import os
from dotenv import load_dotenv
from config_vnatre import RFID_DB_FAJL

load_dotenv()
_salt = os.getenv("RFID_SALT_HEX")
if not _salt:
    raise SystemExit("RFID_SALT_HEX ne e vo .env!")
SALT = bytes.fromhex(_salt)

def main():
    ime = input("Ime na chlenot: ").strip()
    uid = input("UID (od rfid_zapis.py): ").strip()
    token = input("Token (od rfid_zapis.py): ").strip()

    h = hashlib.sha256(str(uid).encode() + str(token).encode() + SALT).hexdigest()

    db = {}
    if os.path.exists(RFID_DB_FAJL):
        with open(RFID_DB_FAJL) as f:
            db = json.load(f)
    db[h] = ime
    with open(RFID_DB_FAJL, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"Zachuvan {ime} vo {RFID_DB_FAJL} (samo hash, bez lichni podatoci)")

if __name__ == "__main__":
    main()
