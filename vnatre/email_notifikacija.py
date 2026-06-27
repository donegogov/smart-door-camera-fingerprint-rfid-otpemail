
# -*- coding: utf-8 -*-
# email_notifikacija.py - Mailgun (OTP + alert) - SAMO vnatre, kluc vo .env
import os
import smtplib
from email.message import EmailMessage
import requests
from dotenv import load_dotenv
from config_vnatre import EMAILS, DEFAULT_EMAIL

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

EMAIL_FROM = os.getenv("EMAIL_FROM")
ADMIN_EMAIL = os.getenv("EMAIL_TO")

def send_email(subject, text, to, attachments=None):
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
        print("[EMAIL] SMTP ne e konfiguriran")
        return False

    if not to:
        print("[EMAIL] nema recipient")
        return False

    if isinstance(to, str):
        recipients = [x.strip() for x in to.split(",") if x.strip()]
    else:
        recipients = to

    if not recipients:
        print("[EMAIL] prazna recipient lista")
        return False

    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(text)

    attachments = attachments or []

    for att in attachments:
        # att moze da bide: ("nepoznat.jpg", "/path/do/slika.jpg")
        filename, path = att

        if not os.path.exists(path):
            print(f"[EMAIL] attachment ne postoi: {path}")
            continue

        with open(path, "rb") as f:
            data = f.read()

        msg.add_attachment(
            data,
            maintype="application",
            subtype="octet-stream",
            filename=filename
        )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        print("[EMAIL] prateno:", subject)
        return True

    except Exception as e:
        print("[EMAIL] greshka:", e)
        return False


def prati_otp(ime, otp):
    email = EMAILS.get(ime, DEFAULT_EMAIL)

    if not email:
        print("[EMAIL] nema email za", ime, "OTP:", otp)
        return

    ok = send_email(
        subject="Vasiot OTP kod",
        text=f"OTP kod za vlez: {otp}",
        to=email
    )

    if ok:
        print(f"[EMAIL] OTP praten do {ime}")
    else:
        print("[EMAIL] OTP ne e praten:", otp)


def prati_alert(slika_path="vnatre_alert.jpg"):
    if not ADMIN_EMAIL:
        print("[EMAIL] alert preskoknat - nema ADMIN_EMAIL/EMAIL_TO")
        return

    attachments = []

    if os.path.exists(slika_path):
        attachments.append(("nepoznat.jpg", slika_path))

    ok = send_email(
        subject="ALERT: Nepoznato lice na vratata",
        text="Nepoznato lice detektirano.",
        to=ADMIN_EMAIL,
        attachments=attachments
    )

    if ok:
        print("[EMAIL] alert praten")
    else:
        print("[EMAIL] alert ne e praten")
