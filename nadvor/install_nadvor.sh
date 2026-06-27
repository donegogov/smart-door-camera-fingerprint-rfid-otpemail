#!/bin/bash
# install_nadvor.sh - RPi4 NADVOR (Bookworm). Sledi + senzori + prakja VNATRE.
# NEMA face_recognition/dlib - polesno!
set -e

CONFIG_TXT="/boot/firmware/config.txt"
[ -f "$CONFIG_TXT" ] || CONFIG_TXT="/boot/config.txt"

echo "=== 1/6 Sistemski paketi ==="
sudo apt update
sudo apt install -y python3-opencv python3-picamera2 python3-gpiozero \
                    python3-numpy python3-venv python3-pip \
                    i2c-tools build-essential openssl

echo "=== 2/6 Interfejsi: SPI (RC522), I2C (LCD na GPIO2/3), UART (fingerprint) ==="
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_serial_hw 0
sudo raspi-config nonint do_serial_cons 1
grep -q "^dtparam=spi=on"  "$CONFIG_TXT" || echo "dtparam=spi=on"  | sudo tee -a "$CONFIG_TXT"
grep -q "^dtparam=i2c_arm=on" "$CONFIG_TXT" || echo "dtparam=i2c_arm=on" | sudo tee -a "$CONFIG_TXT"
grep -q "^enable_uart=1" "$CONFIG_TXT" || echo "enable_uart=1" | sudo tee -a "$CONFIG_TXT"
grep -q "^dtoverlay=disable-bt" "$CONFIG_TXT" || echo "dtoverlay=disable-bt" | sudo tee -a "$CONFIG_TXT"
# NAPOMENA: LCD sega na HARDVERSKA i2c-1 (GPIO2/3) - ne treba i2c-gpio overlay!

echo "=== 3/6 Fusion HAT biblioteka (SunFounder) ==="
curl -sSL https://raw.githubusercontent.com/sunfounder/sunfounder-installer-scripts/main/install-fusion-hat.sh | sudo bash || \
  echo "ZABELESHKA: ako padne, instaliraj fusion_hat rachno (vidi SunFounder)"

echo "=== 4/6 Python venv (so sistemski paketi - za picamera2/opencv/fusion_hat) ==="
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "=== 5/6 TLS sertifikati ==="
if [ ! -f nadvor.crt ]; then
    echo ">>> NEMA sertifikati tuka!"
    echo ">>> Pushti ./generiraj_sertifikati.sh (na eden ured) i kopiraj gi:"
    echo ">>>   ca.crt  nadvor.crt  nadvor.key  vo OVAA papka."
fi

echo "=== 6/6 GOTOVO ==="
echo "Sledno:"
echo "  1. Kopiraj TLS: ca.crt nadvor.crt nadvor.key tuka"
echo "  2. Smeni IP vo config_vrska.py (VNATRE_IP)"
echo "  3. Postavi staticki IP za eth0 (vidi README)"
echo "  4. ENROLL (senzorite se TUKA): python3 headshots.py / RFID zapis"
echo "  5. sudo reboot, pa: source venv/bin/activate && python3 main_nadvor.py"
