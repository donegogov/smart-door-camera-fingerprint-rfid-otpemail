# -*- coding: utf-8 -*-
# lcd.py - 16x2 I2C LCD na VTORATA i2c shina (I2C-3, GPIO12 SDA / GPIO16 SCL)
#
# Ako LCD-to ne e povrzano ili padne, programata NE pukа - samo pechati vo konzola.

from config import (LCD_ENABLED, LCD_I2C_PORT, LCD_I2C_ADDRESS,
                    LCD_COLS, LCD_ROWS)

_lcd = None

if LCD_ENABLED:
    try:
        from RPLCD.i2c import CharLCD
        _lcd = CharLCD('PCF8574', LCD_I2C_ADDRESS, port=LCD_I2C_PORT,
                       cols=LCD_COLS, rows=LCD_ROWS, auto_linebreaks=False)
        _lcd.clear()
        print("[LCD] inicijaliziran na i2c-%d adresa 0x%02x"
              % (LCD_I2C_PORT, LCD_I2C_ADDRESS))
    except Exception as e:
        print("[LCD] ne moze da se inicijalizira (%s) - prodolzhuvam bez LCD" % e)
        _lcd = None


def poraka(linija1="", linija2=""):
    """Prikazi do dve linii. Sekogash pechati i vo konzola."""
    print("[LCD] %-16s | %-16s" % (linija1, linija2))
    if _lcd is None:
        return
    try:
        _lcd.clear()
        _lcd.cursor_pos = (0, 0)
        _lcd.write_string(linija1[:LCD_COLS])
        if LCD_ROWS > 1:
            _lcd.cursor_pos = (1, 0)
            _lcd.write_string(linija2[:LCD_COLS])
    except Exception as e:
        print("[LCD] greshka pri pishuvanje: %s" % e)


def ischisti():
    if _lcd is not None:
        try:
            _lcd.clear()
        except Exception:
            pass
