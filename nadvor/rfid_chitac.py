# -*- coding: utf-8 -*-
# rfid_chitac.py - NADVOR samo CHITA RFID (uid + token). BEZ hashiranje!
# Hashiranjeto i proverkata se VNATRE (tamu e salt-ot).
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO


def procitaj_karta():
    """Vrakja (uid, token) surovo, ili (None, None) pri greshka."""
    citac = SimpleMFRC522()
    try:
        uid, tekst = citac.read()
        return uid, tekst.strip()
    except Exception as e:
        print("[RFID] greshka:", e)
        return None, None
    finally:
        GPIO.cleanup()
