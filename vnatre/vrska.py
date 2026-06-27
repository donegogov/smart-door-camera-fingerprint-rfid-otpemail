# -*- coding: utf-8 -*-
# vrska.py - SIFRIRANA TCP komunikacija (mutual TLS) megju NADVOR i VNATRE.
# IST fajl na obata uredi. Length-prefixed JSON + TLS (nikoj ne moze da slusha/imitira).

import json
import socket
import ssl
import struct


def _recvall(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def poslji(sock, obj):
    """Prati JSON objekt (4-bajten length prefix). Raboti preku TLS socket."""
    data = json.dumps(obj).encode("utf-8")
    sock.sendall(struct.pack(">I", len(data)) + data)


def primi(sock):
    """Prochitaj JSON objekt, ili None ako vrskata e zatvorena."""
    raw = _recvall(sock, 4)
    if not raw:
        return None
    n = struct.unpack(">I", raw)[0]
    data = _recvall(sock, n)
    if not data:
        return None
    return json.loads(data.decode("utf-8"))


# ---------------- TLS kontekst ----------------

def server_kontekst(ca_crt, server_crt, server_key):
    """
    VNATRE (server): bara klientot da ima validен sertifikat (mutual TLS).
    Samo NADVOR so vistinskiot sertifikat moze da se povrze.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=server_crt, keyfile=server_key)
    ctx.load_verify_locations(cafile=ca_crt)
    ctx.verify_mode = ssl.CERT_REQUIRED   # KLIENTOT mora da ima sertifikat!
    return ctx


def klient_kontekst(ca_crt, client_crt, client_key):
    """
    NADVOR (klient): proveruva deka serverot e VISTINSKIOT RPi5,
    i se pretstavuva so svoj sertifikat.
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_cert_chain(certfile=client_crt, keyfile=client_key)
    ctx.load_verify_locations(cafile=ca_crt)
    ctx.check_hostname = False   # koristime CN "vnatre", ne hostname
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx
