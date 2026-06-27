#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main_nadvor.py - RPi4 NADVOR - sledi LOKALNO, prakja surovi podatoci VNATRE.
# ============================================================================
# NADVOR ne odluchuva NISHTO. Samo:
#   - sledi dvizhenje/lice lokalno (mazni serva)
#   - koga ima lice -> slika -> prati VNATRE -> dobiva "Done"/"unknown"
#   - ako poznato -> vodi niz faktori (otpechatok -> OTP -> RFID),
#     sekoj pat prakja SUROVO citanje VNATRE, VNATRE proveruva
#   - VNATRE odluchuva i otkluchuva
#
# Koristi gi POSTOECHKITE moduli: config, kamera, sledenje, tastatura,
# otpechatok, lcd (isti kako dosega). Plus: vrska, rfid_chitac, config_vrska.

import base64
import socket
import ssl
import time

# TLS sertifikati (kopiraj gi tuka - vidi generiraj_sertifikati.sh)
CA_CRT = "ca.crt"
CLIENT_CRT = "nadvor.crt"
CLIENT_KEY = "nadvor.key"

import cv2

from config import (cam_cx, cam_cy, window_on, CIRCLE_SIZE, LINE_THICKNESS,
                    green, PAN_START, TILT_START, SCAN_STEP, PAN_MIN, PAN_MAX,
                    TILT_MIN, TILT_MAX, TILT_STEP, SCAN_DELAY,
                    TRACK_DIV, TRACK_MAX_STEP, STILL_TIMEOUT)
from config_vrska import VNATRE_IP, VNATRE_PORT, TIMEOUT
from vrska import poslji, primi, klient_kontekst
import sledenje
import tastatura
import lcd
from kamera import WebcamVideoStream
from otpechatok import get_fingerprint, finger
import rfid_chitac


def povrzi_vnatre():
    """Otvori SIFRIRANA (TLS) vrska kon RPi5 vnatre."""
    ctx = klient_kontekst(CA_CRT, CLIENT_CRT, CLIENT_KEY)
    raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw.settimeout(TIMEOUT)
    raw.connect((VNATRE_IP, VNATRE_PORT))
    # server_hostname mora da se sovpagja so CN vo sertifikatot ("vnatre")
    return ctx.wrap_socket(raw, server_hostname="vnatre")


def slika_vo_b64(bgr):
    ok, buf = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return base64.b64encode(buf).decode("ascii")


def proces_otkluchuvanje(img_frame):
    """
    Vodi go korisnikot niz faktorite, prakajki surovo VNATRE.
    Vrakja True ako VNATRE otkluchi.
    """
    try:
        s = povrzi_vnatre()
    except Exception as e:
        print("[NADVOR] ne moze da se povrze so VNATRE:", e)
        lcd.poraka("Nema vrska", "so vnatre")
        return False

    try:
        # ---- 1. LICE ----
        lcd.poraka("Proveruvam", "lice...")
        poslji(s, {"tip": "PROVERI_LICE", "slika": slika_vo_b64(img_frame)})
        odg = primi(s)
        rez = (odg or {}).get("rezultat")
        if rez in (None, "nema_lice"):
            lcd.poraka("Nema lice", "")
            return False
        if rez == "unknown":
            lcd.poraka("Nepoznato lice", "Odbieno")
            time.sleep(2)
            return False
        osoba = rez
        lcd.poraka(f"Zdravo {osoba}", "Stavi prst")

        # ---- 2. OTPECHATOK ----
        if not get_fingerprint():
            lcd.poraka("Otpechatok", "Odbien")
            time.sleep(2)
            return False
        poslji(s, {"tip": "OTPECHATOK", "id": finger.finger_id})
        if not (primi(s) or {}).get("ok"):
            lcd.poraka("Otpechatok", "ne se sovpagja")
            time.sleep(2)
            return False

        # ---- 3. OTP (VNATRE prati email; korisnik vnesuva na tastatura) ----
        lcd.poraka("OTP na email", "Vnesi: * kod #")
        vnes = ""
        is_start = False
        while True:
            k = tastatura.scankey()
            if k is None:
                continue
            if k == "*":
                is_start = True
                vnes = ""
            elif k == "#":
                break
            elif is_start:
                vnes += k
        poslji(s, {"tip": "OTP", "vnes": vnes})
        if not (primi(s) or {}).get("ok"):
            lcd.poraka("Pogreshen OTP", "Odbieno")
            time.sleep(2)
            return False

        # ---- 4. RFID ----
        lcd.poraka("Prinesi", "karta")
        uid, token = rfid_chitac.procitaj_karta()
        if uid is None:
            lcd.poraka("Greshka karta", "")
            return False
        poslji(s, {"tip": "RFID", "uid": uid, "token": token})
        finalno = primi(s) or {}
        if finalno.get("tip") == "OTKLUCENO":
            lcd.poraka("Dobredojde", finalno.get("osoba", ""))
            return True
        lcd.poraka("Karta odbiena", "")
        time.sleep(2)
        return False
    finally:
        s.close()


def main():
    lcd.poraka("Pametna vrata", "Startuvam...")
    vs = PiVideoStream().start()
    time.sleep(2.0)

    x, y = PAN_START, TILT_START
    dx = SCAN_STEP
    x, y = sledenje.postavi(x, y)
    sledi = False
    posledno = 0.0
    lcd.poraka("Skeniram...", "")

    while True:
        f1 = vs.read()
        if f1 is None:
            continue
        g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
        time.sleep(0.03)
        f2 = vs.read()
        g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
        centar = sledenje.motion_centar(g1, g2)

        if centar is not None:
            # MOTION -> sledi LOKALNO (mazno)
            sledi = True
            posledno = time.time()
            cx, cy = centar
            x += max(-TRACK_MAX_STEP, min(TRACK_MAX_STEP, int((cx - cam_cx) / TRACK_DIV)))
            y += max(-TRACK_MAX_STEP, min(TRACK_MAX_STEP, int((cy - cam_cy) / TRACK_DIV)))
            x, y = sledenje.postavi(x, y)
        else:
            if sledi and (time.time() - posledno < STILL_TIMEOUT):
                # nekoj zastana -> probaj otkluchuvanje (slika ide VNATRE)
                if proces_otkluchuvanje(f2):
                    print("[NADVOR] VNATRE otkluci!")
                sledi = False
                lcd.poraka("Skeniram...", "")
            else:
                # skeniraj (snake)
                sledi = False
                x += dx
                if x >= PAN_MAX:
                    x = PAN_MAX; dx = -SCAN_STEP; y += TILT_STEP
                    if y >= TILT_MAX:
                        y = TILT_MIN
                elif x <= PAN_MIN:
                    x = PAN_MIN; dx = SCAN_STEP; y += TILT_STEP
                    if y >= TILT_MAX:
                        y = TILT_MIN
                x, y = sledenje.postavi(x, y)
                time.sleep(SCAN_DELAY)

        if window_on and centar is not None:
            cv2.circle(f2, centar, CIRCLE_SIZE, green, LINE_THICKNESS)
            cv2.imshow("Nadvor - q izlez", f2)
        if window_on and cv2.waitKey(1) & 0xFF == ord('q'):
            break

    vs.stop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nKraj.")
    finally:
        sledenje.zatvori_serva()
