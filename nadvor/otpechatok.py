# -*- coding: utf-8 -*-
# otpechatok.py - fingerprint senzor na UART (GPIO14 TXD / GPIO15 RXD)

import serial
import adafruit_fingerprint

# /dev/serial0 sekogash pokazhuva na primarniot UART na GPIO14/15.
# So 'dtoverlay=disable-bt' toa e stabilniot PL011 (preporacheno).
uart = serial.Serial("/dev/serial0", baudrate=57600, timeout=1)
finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)


def get_fingerprint():
    """Cheka prst, template, bara match. Vrakja True/False."""
    print("Chekam otpechatok...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Obrabotuvam...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    print("Prebaruvam...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True
