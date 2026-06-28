if you like my work donate some crypto

Bitcoin: bc1p0pmdvk0g86z0apl4l9f0rgymtfvcjtlekkm47hyptl5zf8ask6hqpf82un

Ethereum: 0x4F641266B906AcEA1Ed106FDD50978EE5337e3e7

Solana: 4UCTxasy88uFfBvxVqoLxvh8sPomCSJ1Ljoxbf5Xc1ef


# 🔒 Pametna Vrata — Multi-Layer Smart Door Security System

Sistem za pametno zakluchuvanje so **5 sloevi na zashtita**, izgraden na
Raspberry Pi. Raboti kako **dopolnitelen sloj** nad obichnata brava so kluc.

> **Vazhno:** Ova e DIY/hobi proekt i DOPOLNITELEN sloj na zashtita. Obichnata
> brava so kluc OSTANUVA glavnata zashtita. Ne se potпiraj samo na ova za
> vistinska bezbednost na dom.

---

## 📋 Sodrzhina
1. Shto pravi sistemot
2. Arhitektura (zoshto DVA uredi)
3. Shto ti treba (hardver)
4. Povrzuvanje (pinout)
5. Instalacija od NULA
6. Mrezha (Ethernet megju dvata Pi)
7. TLS sertifikati
8. Enroll (lica, otpechatoci, kartichki)
9. Pushtanje
10. Shtelovanje i problemi
11. Bezbednost — kako raboti

---

## 1. Shto pravi sistemot

Koga nekoj ke se priblizhi do vratata:

1. 📷 **Kamera na pan/tilt** detektira dvizhenje i SLEDI go liceto (mazno)
2. 🧠 **Face recognition** — proveruva dali e poznat chlen ili nepoznat
   - Nepoznat → praka ALERT email so slika do sopstvenikot
   - Poznat → prodolzhuva na sledniot sloj
3. 👆 **Otpechatok od prst**
4. 📧 **OTP kod** — ispraten na email, se vnesuva na tastatura
5. 💳 **RFID kartichka**

Ako SITE 5 proverki pominat → vratata se otkluchuva.
LCD ekran prikazhuva status na sekoj chekor.

---

## 2. Arhitektura — zoshto DVA uredi?

Sistemot koristi **dva Raspberry Pi** za maksimalna bezbednost:

```
   NADVOR (RPi4, na vratata)            VNATRE (RPi5, zad vratata)
   +----------------------+            +----------------------+
   | • Kamera + serva      |            | • Face recognition    |
   | • Otpechatok, RFID    |  Ethernet  | • Site proverki       |
   | • Tastatura, LCD      |<==(TLS)==> | • Bazi + tajni        |
   | • SLEDI lokalno       |            | • OTP (email)         |
   | x NEMA tajni          |            | • ODLUCHUVA           |
   | x NEMA bazi           |            | • Komanduva BRAVA     |
   | x NE odluchuva        |            | 🔒 BRAVA (vnatre)     |
   +----------------------+            +----------------------+
```

**Zoshto vaka?** Nadvoreshniot Pi e fizichki dostapen (napagjach moze da go
dofati). Zatoa toj NEMA nishto vredno — bez tajni, bez bazi, bez moc da
otkluchи. Samo CHITA senzori i PRAKA surovi podatoci vnatre. Mozokot
(odluka + brava) e VNATRE, nedostapen.

Duri i da nekoj go ukrade ili hakira nadvoreshniot Pi → dobiva bezvreden
"preprakjach". Ne moze da otkluchi bez da pomine SITE proverki vnatre.

---

## 3. Shto ti treba (hardver)

| Komponenta | Uloga | Kade |
|---|---|---|
| Raspberry Pi 4 (4-8GB) | sledi + senzori | NADVOR |
| Raspberry Pi 5 | mozok + odluka | VNATRE |
| Pi Camera v3 (NoIR za nok) | lice | NADVOR |
| SunFounder Fusion HAT+ | serva + napojuvanje | NADVOR |
| 2x servo (pan/tilt) | dvizhenje na kamera | NADVOR |
| Fingerprint senzor (UART) | otpechatok | NADVOR |
| RC522 RFID chitac | kartichki | NADVOR |
| 4x4 tastatura | OTP vnes | NADVOR |
| 16x2 LCD (I2C) | status | NADVOR |
| Rele + brava (FAIL-SECURE) | zakluchuvanje | VNATRE |
| Ethernet kabel + armored door loop | vrska | megju dvata |

**Napojuvanje:** NADVOR preku Fusion HAT+ (eden 5V/3A USB-C za Pi+serva).
VNATRE obichen RPi5 napojuvac (5V/5A).

> **NoIR kamera** = gleda vo temnina so IR svetlo. Dobro za vrata. Preku den
> boite izgledaat malku rozevo.

---

## 4. Povrzuvanje (pinout)

Site pinovi se **BCM** broevi.

### NADVOR (RPi4)
| Komponenta | Povrzuvanje |
|---|---|
| **Serva pan/tilt** | Fusion HAT kanali **P0** (pan), **P1** (tilt) |
| **Fingerprint** UART | TX→GPIO15, RX→GPIO14, 3.3V, GND (`/dev/serial0`) |
| **RC522** SPI | SDA→GPIO8, SCK→GPIO11, MOSI→GPIO10, MISO→GPIO9, RST→GPIO25, **3.3V**, GND |
| **Tastatura 4x4** | redovi 19,13,6,5 / koloni 21,20,22,27 |
| **LCD I2C** | SDA→GPIO2, SCL→GPIO3 (**hardverska i2c-1**), 5V, GND |
| **Vrska kon VNATRE** | Ethernet (eth0) |

> ⚠️ RC522 SAMO na **3.3V** (na 5V gori!). Fingerprint TX↔RX se VKRSTENI.

### VNATRE (RPi5)
| Komponenta | Pin |
|---|---|
| Rele za brava | GPIO17 (FAIL-SECURE: bez struja = zakluceno) |
| Ethernet | eth0 → kon NADVOR |
| Monitor | HDMI |

---

## 5. Instalacija od NULA

### 5.1 — Snimi OS na dvete SD kartichki
Koristi **Raspberry Pi Imager**. Za OBATA:
- OS: **Raspberry Pi OS (64-bit) — Bookworm**
- Vo postavki (⚙️): vkluchi SSH, postavi korisnik/lozinka, WiFi

### 5.2 — Prv boot i azhuriranje (OBATA)
```bash
sudo apt update && sudo apt full-upgrade -y
```

### 5.3 — Svali go proektot
Stavi ja `nadvor/` papka na RPi4, `vnatre/` papka na RPi5.

### 5.4 — Pushti install skripta

**NADVOR (RPi4):**
```bash
cd nadvor
chmod +x install_nadvor.sh
./install_nadvor.sh
sudo reboot
```
**VNATRE (RPi5):**
```bash
cd vnatre
chmod +x install_vnatre.sh
./install_vnatre.sh
sudo reboot
```

> ⏳ Na VNATRE, dlib KOMPAJLIRA 10-30 min. Normalno. NADVOR e pobrz (nema dlib).

### 5.5 — Sekogash aktiviraj venv pred rabota
```bash
cd nadvor   # ili vnatre
source venv/bin/activate
```

---

## 6. Mrezha — Ethernet megju dvata Pi

Preporachano: **direkten kabel Pi-na-Pi** so staticki IP.

> Bookworm koristi **NetworkManager** (ne dhcpcd!). Koristi `nmcli`.

Najdi go imeto na ethernet vrskata:
```bash
nmcli con show          # baraj "ethernet" tip (npr "eth0" ili "Wired connection 1")
```

**VNATRE (RPi5)** — IP 10.0.0.1:
```bash
sudo nmcli con mod "<ime>" ipv4.method manual ipv4.addresses 10.0.0.1/24
sudo nmcli con mod "<ime>" ipv4.never-default yes
sudo nmcli con up "<ime>"
```
**NADVOR (RPi4)** — IP 10.0.0.2:
```bash
sudo nmcli con mod "<ime>" ipv4.method manual ipv4.addresses 10.0.0.2/24
sudo nmcli con mod "<ime>" ipv4.never-default yes
sudo nmcli con up "<ime>"
```

Povrzhi go kabelot (obata Pi vkluceni!), pa testiraj od NADVOR:
```bash
ping 10.0.0.1     # treba da odgovara
```
Vo `nadvor/config_vrska.py` proveri: `VNATRE_IP = "10.0.0.1"`

> Ethernet kabelot pominuva niz **armored door cable** (povrshinski, bez dupcenje dzid).

---

## 7. TLS sertifikati (sifrirana vrska)

Pushti **EDNASH**:
```bash
chmod +x generiraj_sertifikati.sh
./generiraj_sertifikati.sh
```
Kopiraj:
- **VNATRE** (vnatre/): `ca.crt`, `vnatre.crt`, `vnatre.key`
- **NADVOR** (nadvor/): `ca.crt`, `nadvor.crt`, `nadvor.key`

> 🔑 `ca.key` chuvaj go OFFLINE. Privatnite `.key` NIKOGASH ne gi sodeluvaj.

---

## 8. Enroll — lica, otpechatoci, kartichki

Senzorite se NADVOR, bazите VNATRE → dva chekori.

### 8.1 LICA
NADVOR:
```bash
cd nadvor && source venv/bin/activate
python3 headshots.py        # ime, SPACE=slikaj, Q=kraj (10-15 sliki/chlen)
```
Kopiraj `dataset/` na VNATRE, pa:
```bash
cd vnatre && source venv/bin/activate
python3 train_model.py      # pravi encodings.pickle
```

### 8.2 OTPECHATOCI
NADVOR:
```bash
python3 enroll_otpechatok.py    # registriraj prst, zapamti finger_id
```
VNATRE — vo `otpechatoci.json`:
```json
{"1": "Done", "2": "Valentina", "3": "Vasil"}
```

### 8.3 RFID KARTICHKI
NADVOR:
```bash
python3 rfid_zapis.py       # zapisuva token, ti dava UID + Token
```
VNATRE:
```bash
python3 rfid_dodaj.py       # vnesi UID+Token, presmetuva hash, zachuvuva
```

### 8.4 Email (Mailgun) — na VNATRE
Vo `vnatre/.env` popolni `MAILGUN_API_KEY`, `MAILGUN_DOMAIN`, `ADMIN_EMAIL`.
Vo `vnatre/config_vnatre.py` smeni `EMAILS` so iminjata na familijata.

---

## 9. Pushtanje

**Prvo VNATRE (RPi5):**
```bash
cd vnatre && source venv/bin/activate && python3 server.py
```
**Potoa NADVOR (RPi4):**
```bash
cd nadvor && source venv/bin/activate && python3 main_nadvor.py
```

### Avtomatski na boot (systemd) — primer za VNATRE
```bash
sudo nano /etc/systemd/system/vrata.service
```
```ini
[Unit]
Description=Pametna Vrata
After=network.target

[Service]
User=donatello
WorkingDirectory=/home/donatello/vnatre
ExecStart=/home/donatello/vnatre/venv/bin/python /home/donatello/vnatre/server.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable vrata.service && sudo systemctl start vrata.service
```

---

## 10. Shtelovanje i chesti problemi

### Serva
| Problem | Reshenie |
|---|---|
| servo odi naopaku | `PAN_DIR`/`TILT_DIR` = -1 vo config.py |
| servo ne mrda | proveri kanal (P0/P1), kabli, Fusion HAT napojuvanje |

### Sledenje
| Problem | Reshenie |
|---|---|
| haoticno dvizhenje | namali `SCAN_STEP`, zgolemi `SCAN_DELAY` |
| ne gleda dvizhenje | namali `MIN_AREA` |
| premnogu osetlivo | zgolemi `MIN_AREA` i `THRESHOLD_SENSITIVITY` |

### Kamera
| Problem | Reshenie |
|---|---|
| ne bootira so HAT | proveri kabel na kamera (chest problem!) |
| mnogu zoom | `kamera.py` koristi ScalerCrop na cel senzor (full FoV) |
| lista prazna | kabel labav ili lош |

### Mrezha
| Problem | Reshenie |
|---|---|
| ping ne pominuva | proveri kabel, obata Pi vkluceni, IP adresi |
| `nmcli con up` greshka | kabelot mora da e povrzan PRVO |
| TLS greshka | sertifikatите kopirani vo dvete papki? |

### Fingerprint
| Problem | Reshenie |
|---|---|
| UART Input/output error | serial konzola iskluchena? TX↔RX vkrsteni? |

---

## 11. Bezbednost — kako raboti

| Sloj | Zashtita |
|---|---|
| **Mozok vnatre** | NADVOR nema tajni/bazi/odluka → ukraden = bezvreden |
| **TLS sifriranje** | nikoj na mrezhata ne moze da slusha/imitira |
| **OTP** | razlichen sekoj pat, na email → anti-replay |
| **RFID hash** | samo SHA-256 hash vnatre, salt ne patuva, kartichka bez lichni podatoci |
| **SSH kluc-samo** | bez lozinka, samo so privaten kluc |
| **FAIL-SECURE brava** | bez struja = zakluceno |
| **Obichen kluc** | GLAVNA zashtita — ova e DOPOLNITELEN sloj |

### SSH hardening
```bash
ssh-keygen -t ed25519              # na tvojot kompjuter
ssh-copy-id korisnik@<ip-na-Pi>
# vo /etc/ssh/sshd_config: PasswordAuthentication no
sudo systemctl restart ssh
```

---

## 📁 Struktura na fajlovi

### nadvor/ (RPi4)
```
main_nadvor.py       glavna (sledi + vodi niz faktori)
config.py            postavki (pinovi, kamera, serva)
config_vrska.py      IP na VNATRESHNIOT Pi
kamera.py            video stream
sledenje.py          Fusion HAT serva + motion
tastatura.py         4x4 tastatura
otpechatok.py        fingerprint
rfid_chitac.py       RFID (samo chita)
lcd.py               LCD status
vrska.py             TLS komunikacija
headshots.py         ALATKA: slikanje lica
enroll_otpechatok.py ALATKA: otpechatoci
rfid_zapis.py        ALATKA: RFID token
install_nadvor.sh    instalacija
generiraj_sertifikati.sh  TLS
```

### vnatre/ (RPi5)
```
server.py            glavna (TCP server + odluka + brava)
config_vnatre.py     postavki
prepoznavanje.py     face recognition
proverki.py          proverki (+ tajni/bazi)
email_notifikacija.py  Mailgun
brava.py             rele
vrska.py             TLS komunikacija
train_model.py       ALATKA: encodings.pickle
rfid_dodaj.py        ALATKA: RFID hash vo baza
install_vnatre.sh    instalacija
generiraj_sertifikati.sh  TLS
.env                 TAJNI - NE se sodeluva!
```

### Fajlovi shto TI gi pravish (ne se vo repo)
```
vnatre/encodings.pickle    lica
vnatre/korisnici.json      RFID hashevi
vnatre/otpechatoci.json    finger_id → ime
vnatre/.env                tajni
ca.crt, *.crt, *.key       TLS sertifikati
```

---

## ⚖️ Odgovornost

Edukativen/hobi proekt. Avtorot ne e odgovoren za bezbednost na tvoj dom.
Sekogash chuvaj ja obichnata brava so kluc kako GLAVNA zashtita.

Pridonesi i podobruvanja se dobredojdeni! 🚀
