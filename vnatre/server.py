#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# server.py - RPi5 VNATRE - mozokot. TCP server, state-mashina za faktorite.
# ============================================================================
# Tek (sekoja vrska od NADVOR e edna sesija):
#   1. NADVOR prati slika -> VNATRE prepoznava -> "Done" / "unknown"
#      - unknown -> alert email, kraj
#      - poznato -> "pushti otpechatok"
#   2. NADVOR prati finger_id -> proveri dali e taa osoba -> generiraj+prati OTP
#   3. NADVOR prati OTP vnes -> proveri
#   4. NADVOR prati RFID (uid+token) -> proveri hash -> SITE OK -> OTKLUCI
#
# NADVOR ne odluchuva NISHTO. Site proverki, tajni, bazi se TUKA.

import base64
import socket
import ssl
import threading
import time

import cv2
import numpy as np

from config_vnatre import SERVER_HOST, SERVER_PORT
from vrska import poslji, primi, server_kontekst

# TLS sertifikati (kopiraj gi tuka - vidi generiraj_sertifikati.sh)
CA_CRT = "ca.crt"
SERVER_CRT = "vnatre.crt"
SERVER_KEY = "vnatre.key"
import prepoznavanje
import proverki
import email_notifikacija
import brava


def dekodiraj_slika(b64):
    data = base64.b64decode(b64)
    arr = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def obrabotaj_vrska(conn, addr):
    print(f"[VNATRE] Vrska od {addr}")
    sesija_id = f"{addr[0]}:{addr[1]}:{time.time()}"
    osoba = None
    face_ok = finger_ok = otp_ok = rfid_ok = False

    try:
        while True:
            poraka = primi(conn)
            if poraka is None:
                break
            tip = poraka.get("tip")

            # ---- 1. LICE ----
            if tip == "PROVERI_LICE":
                slika = dekodiraj_slika(poraka["slika"])
                rez = prepoznavanje.prepoznaj(slika)
                if rez is None:
                    poslji(conn, {"tip": "LICE", "rezultat": "nema_lice"})
                elif rez == "unknown":
                    cv2.imwrite("vnatre_alert.jpg", slika)
                    email_notifikacija.prati_alert("vnatre_alert.jpg")
                    poslji(conn, {"tip": "LICE", "rezultat": "unknown"})
                else:
                    osoba = rez
                    face_ok = True
                    print(f"[VNATRE] Prepoznaen: {osoba}")
                    poslji(conn, {"tip": "LICE", "rezultat": osoba})

            # ---- 2. OTPECHATOK ----
            elif tip == "OTPECHATOK":
                if not face_ok:
                    poslji(conn, {"tip": "OTPECHATOK_OK", "ok": False})
                    continue
                ok = proverki.proveri_otpechatok(poraka.get("id"), osoba)
                finger_ok = ok
                if ok:
                    otp = proverki.generiraj_otp(sesija_id)
                    email_notifikacija.prati_otp(osoba, otp)
                poslji(conn, {"tip": "OTPECHATOK_OK", "ok": ok})

            # ---- 3. OTP ----
            elif tip == "OTP":
                if not finger_ok:
                    poslji(conn, {"tip": "OTP_OK", "ok": False})
                    continue
                ok = proverki.proveri_otp(sesija_id, poraka.get("vnes", ""))
                otp_ok = ok
                poslji(conn, {"tip": "OTP_OK", "ok": ok})

            # ---- 4. RFID -> finalna odluka ----
            elif tip == "RFID":
                if not otp_ok:
                    poslji(conn, {"tip": "RFID_OK", "ok": False})
                    continue
                ok = proverki.proveri_rfid(poraka.get("uid"),
                                           poraka.get("token"), osoba)
                rfid_ok = ok
                if face_ok and finger_ok and otp_ok and rfid_ok:
                    print(f"[VNATRE] SITE PROVERKI OK za {osoba} - OTKLUCHUVAM")
                    poslji(conn, {"tip": "OTKLUCENO", "osoba": osoba})
                    brava.otkluci()
                else:
                    poslji(conn, {"tip": "RFID_OK", "ok": False})

            elif tip == "RESET":
                osoba = None
                face_ok = finger_ok = otp_ok = rfid_ok = False
                poslji(conn, {"tip": "RESET_OK"})
    except Exception as e:
        print(f"[VNATRE] greshka vo vrska: {e}")
    finally:
        conn.close()
        print(f"[VNATRE] Vrska zatvorena {addr}")


def main():
    ctx = server_kontekst(CA_CRT, SERVER_CRT, SERVER_KEY)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((SERVER_HOST, SERVER_PORT))
    s.listen(1)
    print(f"[VNATRE] TLS server slusha na {SERVER_HOST}:{SERVER_PORT}")
    try:
        while True:
            raw_conn, addr = s.accept()
            try:
                conn = ctx.wrap_socket(raw_conn, server_side=True)
            except ssl.SSLError as e:
                print(f"[VNATRE] ODBIEN nevaliden sertifikat od {addr}: {e}")
                raw_conn.close()
                continue
            t = threading.Thread(target=obrabotaj_vrska, args=(conn, addr))
            t.daemon = True
            t.start()
    except KeyboardInterrupt:
        print("\n[VNATRE] Kraj.")
    finally:
        brava.zakluci()
        s.close()


if __name__ == "__main__":
    main()
