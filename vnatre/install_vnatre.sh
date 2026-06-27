#!/bin/bash
# install_vnatre.sh - RPi5 VNATRE (Bookworm). Mozokot: face recognition + odluka + brava.
set -e

echo "=== 1/5 Sistemski paketi (vkl. dlib zavisnosti) ==="
sudo apt update
sudo apt install -y python3-venv python3-pip python3-gpiozero \
                    build-essential cmake libopenblas-dev liblapack-dev \
                    libatlas-base-dev openssl python3-numpy

echo "=== 2/5 Python venv ==="
python3 -m venv --system-site-packages virt-vnatre
source virt-vnatre/bin/activate
pip install --upgrade pip

echo "=== 3/5 Python paketi (face_recognition/dlib - trae nekolku minuti!) ==="
pip install -r requirements.txt

echo "=== 4/5 .env (tajni - SAMO tuka) ==="
if [ ! -f .env ]; then
    cp .env.example .env
    SALT=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s|^RFID_SALT_HEX=.*|RFID_SALT_HEX=$SALT|" .env
    echo ">>> Kreiran .env so svezh RFID_SALT_HEX. Popolni MAILGUN_* i ADMIN_EMAIL!"
fi

echo "=== 5/5 TLS sertifikati ==="
if [ ! -f vnatre.crt ]; then
    echo ">>> NEMA sertifikati! Pushti ./generiraj_sertifikati.sh (na eden ured)"
    echo ">>> i kopiraj:  ca.crt  vnatre.crt  vnatre.key  vo OVAA papka."
fi

echo ""
echo "=== GOTOVO ==="
echo "Sledno:"
echo "  1. Kopiraj TLS: ca.crt vnatre.crt vnatre.key tuka"
echo "  2. Postavi staticki IP za eth0 (vidi README)"
echo "  3. Stavi gi BAZITE tuka:"
echo "       - encodings.pickle  (od train_model.py - vidi dolu)"
echo "       - korisnici.json    (RFID hashevi)"
echo "       - otpechatoci.json  (npr {\"1\":\"Done\",\"2\":\"Valentina\"})"
echo "  4. Popolni .env (Mailgun)"
echo "  5. Rele za brava na GPIO17 (FAIL-SECURE)"
echo "  6. python3 server.py"
echo ""
echo "TRENIRANJE LICA:"
echo "  - Sliki se pravat NADVOR (python3 headshots.py - tamu e kamerata)"
echo "  - Kopiraj ja dataset/ papkata TUKA (preku USB ili scp)"
echo "  - python3 train_model.py  -> pravi encodings.pickle"
