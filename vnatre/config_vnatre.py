# -*- coding: utf-8 -*-
# config_vnatre.py - postavki za RPi5 VNATRE (mozokot)

# ---------------- Mrezha ----------------
# Server slusha na site interfejsi; nadvoreshniot Pi se povrzuva tuka.
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5005

# ---------------- Brava ----------------
BRAVA_PIN = 17             # GPIO za rele (FAIL-SECURE: bez struja = zakluceno)
DOOR_OPEN_SEK = 50000         # kolku sekundi otkluceno

# ---------------- Bazi / fajlovi (SAMO vnatre!) ----------------
ENCODINGS_FILE = "encodings.pickle"      # lica
RFID_DB_FAJL = "korisnici.json"          # RFID hashevi
OTPECHATOK_MAPA = "otpechatoci.json"     # {"3": "Done", "5": "Valentina"}

MIN_PERCENT_MATCH = 50

# Email po chlen (za OTP i alert)
EMAILS = {
    "Done": "donatellorm@gmail.com",
    "Valentina": "valegogovadv@gmail.com",
    "Vasil": "vasil.gogov119@gmail.com",
}
DEFAULT_EMAIL = "done.gogov.1987.dg@gmail.com"

# OTP vazhi tolku sekundi
OTP_VALIDNOST_SEK = 120
