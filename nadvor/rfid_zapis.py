#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# rfid_zapis.py - NADVOR: zapishi sluchaen token na kartichka (za enroll).
# Hashiranjeto i zachuvuvanjeto vo bazata se VNATRE (proverki.py + korisnici.json).
#
# Tek na enroll za RFID:
#   1. TUKA (nadvor): pushti ovaa, zapisi token, zabelezhi gi uid + token
#   2. VNATRE: presmetaj hash od (uid+token+salt) i zachuvaj vo korisnici.json
#      (mozhe so mala pomoshna skripta ili rachno - vidi README)

import secrets
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

def main():
    citac = SimpleMFRC522()
    try:
        ime = input("Ime na chlenot (samo za tvoja zabeleshka): ").strip()
        token = secrets.token_hex(16)
        print(f"Prinesi ja kartichkata za {ime} ...")
        citac.write(token)
        uid, _ = citac.read()
        print("\n=== ZAPISHANO ===")
        print(f"Ime:   {ime}")
        print(f"UID:   {uid}")
        print(f"Token: {token}")
        print("\nVNESI GI OVIE (uid + token) VNATRE za da se presmeta hash-ot")
        print("i zachuva vo korisnici.json (vidi README).")
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
