# -*- coding: utf-8 -*-
# config.py - SITE postavki za pametna vrata (BEZ tajni - tie odat vo .env!)
#
# HARDVERSKA SHEMA (spored tvoeto povrzuvanje):
#   Fingerprint UART : GPIO14 (TXD) , GPIO15 (RXD)        -> /dev/serial0
#   PCA9685   I2C-1  : GPIO2 (SDA1) , GPIO3 (SCL1)        -> /dev/i2c-1 (default)
#   LCD       I2C-3  : GPIO12 (SDA) , GPIO16 (SCL)        -> /dev/i2c-3 (softverski)
#   RC522     SPI    : GPIO10 MOSI, GPIO9 MISO, GPIO11 SCLK, GPIO8 CE0, GPIO25 RST
#   Tastatura 4x4    : redovi 19,13,6,5  koloni 21,20,22,27
#   Pan/Tilt serva   : PCA9685 kanal 0 (pan) , kanal 3 (tilt)
#   Brava/rele       : GPIO26 (ne be spomnata - smeni ako treba)

# ---------------- Prikaz / Debug ----------------
debug = True
verbose = True
show_fps = True
window_on = True      # True = OpenCV prozorec (treba GUI desktop); False za SSH
CIRCLE_SIZE = 8
LINE_THICKNESS = 2
WINDOW_BIGGER = 1

# ---------------- GPIO pinovi ----------------
GPIOZERO_DOOR_PIN = 26          # rele za bravata

# Tastatura 4x4 (BCM broevi)
# Konektor od LEVO kon DESNO: pin1..pin8
#   pin1=19 pin2=13 pin3=6 pin4=5  | pin5=21 pin6=20 pin7=22 pin8=27
# Standardno: prvite 4 = REDOVI, vtorite 4 = KOLONI.
# Ako tipkите izleguvaat pogreshno -> zameni gi dvete grupi (vidi README).
KEYPAD_ROW_PINS = [19, 13, 6, 5]
KEYPAD_COL_PINS = [21, 20, 22, 27]

# ---------------- FUSION HAT serva (pan/tilt) ----------------
# Kanali se STRINGOVI "P0".."P11" spored oznakите na Fusion HAT plочката!
# Smeni gi spored kade fizicki gi vklucki servata.
PCA_PAN_CHANNEL = "P0"      # pan servo (levo-desno)
PCA_TILT_CHANNEL = "P1"     # tilt servo (gore-dolu)

# ---------------- Pan/Tilt agli (CHISTI servo stepeni 0-180) ----------------
# x = pan (levo-desno), y = tilt (gore-dolu). 90 = sredina.
PAN_DIR = 1              # 1 ili -1 ako pan se dvizi NAOPAKU
TILT_DIR = 1             # 1 ili -1 ako tilt se dvizi NAOPAKU

PAN_MIN = 30             # najlev agol pri skeniranje
PAN_MAX = 150            # najdesen agol
TILT_MIN = 70            # najdolen/najgoren agol na tilt
TILT_MAX = 110           # drug kraj na tilt
PAN_START = 90           # pochetna pan pozicija (gleda pravo napred)
TILT_START = 90          # pochetna tilt pozicija (visina na lice)

SCAN_STEP = 2            # stepeni po cekor pri skeniranje (MAL = mazno)
TILT_STEP = 10           # kolku tilt da skokne koga pan ke stigne kraj (nov red)
SCAN_DELAY = 0.03        # pauza po sekoj cekor (mazno tempo)

TRACK_DIV = 25           # sledenje: POGOLEM = pomazno/pobavno
TRACK_MAX_STEP = 6       # max stepeni po cekor pri sledenje na glava
STILL_TIMEOUT = 3.0      # sek po posledno dvizhenje da probuva lice pred scan

# ---------------- LCD (I2C-3, softverski bus) ----------------
LCD_ENABLED = True
LCD_I2C_PORT = 1            # HARDVERSKA i2c-1 (GPIO2/3), PCA go nema veke
LCD_I2C_ADDRESS = 0x27     # proveri so: i2cdetect -y 3  (chesto 0x27 ili 0x3f)
LCD_COLS = 16
LCD_ROWS = 2

# ---------------- Kamera ----------------
WEBCAM = False
WEBCAM_SRC = 0
WEBCAM_WIDTH = 640
WEBCAM_HEIGHT = 480
WEBCAM_HFLIP = True
WEBCAM_VFLIP = False

CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
CAMERA_HFLIP = False
CAMERA_VFLIP = True
CAMERA_ROTATION = 0
CAMERA_FRAMERATE = 15
FRAME_COUNTER = 1000

# ---------------- Tajmeri za sostojbi ----------------
timer_motion = 3
timer_face = 2
timer_pan = 1

# ---------------- Smiruvanje na sledenjeto ----------------
HEAD_FACTOR = 0.18         # "glava" = 18% od vrvot na motion box

# Skeniranje koga nema nishto (MALI cekori = mazno, kako originalot)


# ---------------- Face recognition ----------------
ENCODINGS_FILE = "encodings.pickle"
CASCADE_FILE = "haarcascade_frontalface_default.xml"
MIN_PERCENT_MATCH = 50

PRIORITET_IMINJA = ["Vase", "Valentina", "Done", "unknown"]

EMAILS = {
    "Done": "done.gogov.1987.dg@gmail.com",
    "Valentina": "valegogovadv@gmail.com",
    "Vasil": "vasil.gogov119@gmail.com",
}
DEFAULT_EMAIL = "done.gogov.1987.dg@gmail.com"

# ---------------- RFID ----------------
RFID_DB_FAJL = "korisnici.json"

# ---------------- Vrata ----------------
DOOR_OPEN_SECONDS = 60

# ---------------- Alert za nepoznato lice ----------------
# Kolku sekundi da chekame pred da pratime NOV alert za nepoznat
# (za da ne spamame email ako nepoznatiot stoi pred kamerata)
UNKNOWN_ALERT_COOLDOWN = 120

# ---------------- OpenCV motion ----------------
MIN_AREA = 800        # bea 2000; so shirokata slika chovekot e pomal
THRESHOLD_SENSITIVITY = 25
BLUR_SIZE = 10

# ---------------- Tastatura znaci ----------------
PASSWORD_START_CHARACTER = "*"
PASSWORD_END_CHARACTER = "#"

# ---------------- Boi (BGR) ----------------
blue = (255, 0, 0)
green = (0, 255, 0)
red = (0, 0, 255)

# ---------------- Presmetani vrednosti ----------------
cam_cx = CAMERA_WIDTH / 2
cam_cy = CAMERA_HEIGHT / 2
big_w = int(CAMERA_WIDTH * WINDOW_BIGGER)
big_h = int(CAMERA_HEIGHT * WINDOW_BIGGER)

