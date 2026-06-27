# -*- coding: utf-8 -*-
# proverki.py - SITE proverki se VNATRE (RPi5). Tuka se tajnite i bazite.
import hashlib
import json
import os
import time
from dotenv import load_dotenv
from config_vnatre import RFID_DB_FAJL, OTPECHATOK_MAPA, OTP_VALIDNOST_SEK

load_dotenv()

# RFID salt - SAMO vnatre, vo .env
_salt_hex = os.getenv("RFID_SALT_HEX")
if not _salt_hex:
    raise RuntimeError("RFID_SALT_HEX ne e postaven vo .env (vnatre)!")
_SALT = bytes.fromhex(_salt_hex)


def _vchitaj(fajl, podrazbирано=None):
    if os.path.exists(fajl):
        with open(fajl, "r", encoding="utf-8") as f:
            return json.load(f)
    return podrazbирано if podrazbирано is not None else {}


def proveri_otpechatok(finger_id, ochekuvana_osoba):
    """Dali finger_id pripagja na ochekuvanata osoba (od face recognition)?"""
    mapa = _vchitaj(OTPECHATOK_MAPA)        # {"3": "Done", ...}
    ime = mapa.get(str(finger_id))
    return ime is not None and ime == ochekuvana_osoba


def proveri_rfid(uid, token, ochekuvana_osoba):
    """Presmetaj hash od (uid+token+salt), proveri vo bazata i dali e taa osoba."""
    materijal = str(uid).encode() + str(token).encode() + _SALT
    h = hashlib.sha256(materijal).hexdigest()
    db = _vchitaj(RFID_DB_FAJL)             # {hash: ime}
    ime = db.get(h)
    return ime is not None and ime == ochekuvana_osoba


# ---- OTP (generira i proveruva VNATRE) ----
import math
import random

_aktivni_otp = {}   # {sesija_id: (otp_string, vreme)}


def generiraj_otp(sesija_id):
    znaci = "0123456789ABCD"
    otp = "".join(znaci[math.floor(random.random() * len(znaci))]
                  for _ in range(random.randint(8, 12)))
    _aktivni_otp[sesija_id] = (otp, time.time())
    return otp


def proveri_otp(sesija_id, vnes):
    podatok = _aktivni_otp.get(sesija_id)
    if not podatok:
        return False
    otp, vreme = podatok
    if time.time() - vreme > OTP_VALIDNOST_SEK:
        return False
    return vnes.strip().upper() == otp
