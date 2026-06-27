#!/bin/bash
# generiraj_sertifikati.sh - pravi sertifikati za mutual TLS megju dvata Pi.
# Pushti EDNASH (na bilo koj Pi/kompjuter), pa kopiraj gi fajlovite kade treba.
set -e

echo "=== 1. CA (glaven sertifikat - potpishuva za obata) ==="
openssl genrsa -out ca.key 4096
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt \
  -subj "/CN=VrataCA"

echo "=== 2. Sertifikat za VNATRE (RPi5 server) ==="
openssl genrsa -out vnatre.key 4096
openssl req -new -key vnatre.key -out vnatre.csr -subj "/CN=vnatre"
openssl x509 -req -days 3650 -in vnatre.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out vnatre.crt

echo "=== 3. Sertifikat za NADVOR (RPi4 klient) ==="
openssl genrsa -out nadvor.key 4096
openssl req -new -key nadvor.key -out nadvor.csr -subj "/CN=nadvor"
openssl x509 -req -days 3650 -in nadvor.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out nadvor.crt

rm -f *.csr *.srl
echo ""
echo "=== GOTOVO ==="
echo "Kopiraj na VNATRE (RPi5):  ca.crt  vnatre.crt  vnatre.key"
echo "Kopiraj na NADVOR (RPi4):  ca.crt  nadvor.crt  nadvor.key"
echo ""
echo "VAZHNO: ca.key chuvaj go BEZBEDNO (so nego se pravat novi sertifikati)."
echo "        Privatnite .key fajlovi nikogash ne gi sodeluvaj."
