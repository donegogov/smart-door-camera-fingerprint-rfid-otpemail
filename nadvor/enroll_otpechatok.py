#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# enroll_otpechatok.py - registriranje (enroll) na otpechatoci
# Koristi go istiot UART kako otpechatok.py (/dev/serial0). BEZ pigpio/GPIO!
#
# Upotreba:  python3 enroll_otpechatok.py
#   - izberi mesto (1-127) za sekoj chlen i sledi gi uputstvata
#   - prstot se stava DVAPATI za eden enroll

import adafruit_fingerprint
from otpechatok import finger   # vekje konfiguriran UART /dev/serial0


def enroll_finger(location):
    """Registrira otpechatok na dadenoto mesto (1-127)."""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Stavi go prstot na senzorot...")
        else:
            print("Stavi go ISTIOT prst PONOVNO...")

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Slika zemena")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="", flush=True)
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Greshka so slikata")
                return False

        print("Obrabotuvam...")
        i = finger.image_2_tz(fingerimg)
        if i != adafruit_fingerprint.OK:
            print("Ne uspea obrabotkata")
            return False

        if fingerimg == 1:
            print("Trgni go prstot")
            import time
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Kreiram model...")
    i = finger.create_model()
    if i != adafruit_fingerprint.OK:
        print("Prstite ne se sovpadnaa - probaj povtorno")
        return False

    print(f"Zachuvuvam na mesto #{location}...")
    i = finger.store_model(location)
    if i != adafruit_fingerprint.OK:
        print("Ne uspea zachuvuvanjeto")
        return False

    print(f"USPEH! Otpechatok zachuvan na mesto #{location}")
    return True


def izbrishi(location):
    import adafruit_fingerprint as af
    if finger.delete_model(location) == af.OK:
        print(f"Izbrishan otpechatok #{location}")
    else:
        print("Ne uspea brishenjeto")


if __name__ == "__main__":
    print("=== Enroll na otpechatoci ===")
    finger.read_templates()
    print("Zafateni mesta:", finger.templates)
    print()
    print("1) Enroll nov otpechatok")
    print("2) Izbrishi otpechatok")
    izbor = input("Izbor: ").strip()

    if izbor == "2":
        loc = int(input("Mesto za brishenje (broj): ").strip())
        izbrishi(loc)
    else:
        loc = int(input("Mesto za zachuvuvanje (1-127, npr. 1=Done): ").strip())
        enroll_finger(loc)
