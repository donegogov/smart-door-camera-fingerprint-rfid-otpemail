# -*- coding: utf-8 -*-
# tastatura.py - 4x4 matrichna tastatura + proverka na OTP pin
#
# Povrzuvanje (BCM): redovi 19,13,6,5  koloni 21,20,22,27

import time
from gpiozero import LED, Button

from config import (KEYPAD_ROW_PINS, KEYPAD_COL_PINS,
                    PASSWORD_START_CHARACTER, PASSWORD_END_CHARACTER)

matrix_keys = [['1', '2', '3', 'A'],
               ['4', '5', '6', 'B'],
               ['7', '8', '9', 'C'],
               ['*', '0', '#', 'D']]

_rows = [LED(p) for p in KEYPAD_ROW_PINS]
_cols = [Button(p, pull_up=False) for p in KEYPAD_COL_PINS]

guess = []
is_password_start = False
_secret_pin = ['1', '2', '3', '4', '5', '6']


def set_secret_pin(pin_lista):
    """main.py go povikuva so sveziot OTP pred sekoja proverka."""
    global _secret_pin, guess, is_password_start
    _secret_pin = pin_lista
    guess = []
    is_password_start = False


def scankey():
    """Skenira edna tipka, vrakja znak ili None."""
    for row in range(4):
        _rows[row].on()
        for col in range(4):
            if _cols[col].is_pressed:
                key_press = matrix_keys[row][col]
                print("Pritisnato:", key_press)
                time.sleep(0.5)
                _rows[row].off()
                return key_press
        _rows[row].off()
    return None


def checkPin(key_press):
    """Vrakja True ako pinot e tochen i zavrshen so #."""
    global is_password_start, guess
    if key_press == PASSWORD_END_CHARACTER:
        print(guess, "vs", _secret_pin)
        if guess == _secret_pin:
            print("Tochen pin!")
            time.sleep(1)
            guess = []
            is_password_start = False
            return True
        else:
            print("Pogreshen pin")
            guess = []
            is_password_start = False
    elif key_press == PASSWORD_START_CHARACTER:
        is_password_start = True
        guess = []
    elif is_password_start:
        guess.append(key_press)
    return False


def scankeys():
    """Cheka vnes: * cifri #. Vrakja True ako e tochen."""
    while True:
        key_pressed = None
        while True:
            key_pressed = scankey()
            if key_pressed != None:
                break
        if checkPin(key_pressed) == True:
            return True
        if key_pressed == PASSWORD_END_CHARACTER:
            break
    return False
