# -*- coding: utf-8 -*-
# brava.py - kontrola na rele/brava na RPi5 VNATRE
import time
from gpiozero import LED
from config_vnatre import BRAVA_PIN, DOOR_OPEN_SEK

_rele = LED(BRAVA_PIN)
_rele.off()   # FAIL-SECURE: bez struja = zakluceno


def otkluci():
    print(">>> OTKLUCHUVAM BRAVA <<<")
    _rele.on()
    time.sleep(DOOR_OPEN_SEK)
    _rele.off()
    print("Zakluceno.")


def zakluci():
    _rele.off()
