#!/usr/bin/env bash
# ============================================================
# Mutual TLS Certificate Generation Script
# ============================================================
# Generates:
#   1. A self-signed Certificate Authority (CA)
#   2. A Server certificate signed by the CA
#   3. A Client certificate signed by the CA
#
# Usage:
#   chmod +x generate_certs.sh
#   ./generate_certs.sh
#
# Security notes:
#   - 4096-bit RSA keys
#   - CA key MUST be kept secret — never share ca-key.pem
#   - Only ca-cert.pem (the public CA cert) is distributed to both sides
#   - Certificates expire after 365 days — rotate before expiry
#   - X.509 extensions are required by Python 3.13+ strict SSL validation
# ============================================================

set -euo pipefail

OUTDIR="$(dirname "$0")"   # Write all files into the certs/ directory
DAYS=365
C="IN"
O="MySecureApp"

echo ""
echo "=============================================="
echo "  Mutual TLS Certificate Generator"
echo "=============================================="
echo ""

# -----------------------------------------------------------
# 1. Certificate Authority (CA)
#    MUST have: basicConstraints=CA:TRUE and keyUsage=keyCertSign,cRLSign
#    Python 3.13 strict SSL REQUIRES these extensions on CA certs.
# -----------------------------------------------------------
echo "[1/6] Generating CA private key (4096-bit RSA)..."
openssl genrsa -out "$OUTDIR/ca-key.pem" 4096

echo ""

echo "[2/6] Generating self-signed CA certificate (with required extensions)..."
openssl req -new -x509 \
    -key "$OUTDIR/ca-key.pem" \
    -out "$OUTDIR/ca-cert.pem" \
    -days $DAYS \
    -subj "/C=$C/O=$O/CN=MyCA" \
    -addext "basicConstraints=critical,CA:TRUE" \
    -addext "keyUsage=critical,keyCertSign,cRLSign" \
    -addext "subjectKeyIdentifier=hash"

# -----------------------------------------------------------
# 2. Server Certificate
#    CN must match the hostname clients connect to (localhost here).
#    subjectAltName is required for modern hostname verification.
# -----------------------------------------------------------
echo ""
echo "[3/6] Generating Server private key..."
openssl genrsa -out "$OUTDIR/server-key.pem" 4096

echo ""
echo "[4/6] Generating Server CSR and signing with CA..."
openssl req -new \
    -key "$OUTDIR/server-key.pem" \
    -out "$OUTDIR/server.csr" \
    -subj "/C=$C/O=$O/CN=localhost"

openssl x509 -req \
    -in "$OUTDIR/server.csr" \
    -CA "$OUTDIR/ca-cert.pem" \
    -CAkey "$OUTDIR/ca-key.pem" \
    -CAcreateserial \
    -out "$OUTDIR/server-cert.pem" \
    -days $DAYS \
    -extfile <(printf \
        "basicConstraints=CA:FALSE\n\
keyUsage=critical,digitalSignature,keyEncipherment\n\
extendedKeyUsage=serverAuth\n\
subjectAltName=DNS:localhost,IP:127.0.0.1\n\
subjectKeyIdentifier=hash\n\
authorityKeyIdentifier=keyid,issuer")

# -----------------------------------------------------------
# 3. Client Certificate
#    CN is just an identity label (e.g. "MyClient") — does NOT
#    need to match any hostname.
# -----------------------------------------------------------
echo ""
echo "[5/6] Generating Client private key..."
openssl genrsa -out "$OUTDIR/client-key.pem" 4096

echo ""
echo "[6/6] Generating Client CSR and signing with CA..."
openssl req -new \
    -key "$OUTDIR/client-key.pem" \
    -out "$OUTDIR/client.csr" \
    -subj "/C=$C/O=$O/CN=MyClient"

openssl x509 -req \
    -in "$OUTDIR/client.csr" \
    -CA "$OUTDIR/ca-cert.pem" \
    -CAkey "$OUTDIR/ca-key.pem" \
    -CAcreateserial \
    -out "$OUTDIR/client-cert.pem" \
    -days $DAYS \
    -extfile <(printf \
        "basicConstraints=CA:FALSE\n\
keyUsage=critical,digitalSignature\n\
extendedKeyUsage=clientAuth\n\
subjectKeyIdentifier=hash\n\
authorityKeyIdentifier=keyid,issuer")

# -----------------------------------------------------------
# 4. Cleanup intermediate files
# -----------------------------------------------------------
echo "\n"
echo "[7/6] Cleaning up intermediate files..."
rm -f "$OUTDIR/server.csr" "$OUTDIR/client.csr" "$OUTDIR/ca-cert.srl"

# -----------------------------------------------------------
# 5. Lock down permissions
# -----------------------------------------------------------
echo ""
echo "Setting secure file permissions..."
chmod 600 "$OUTDIR/ca-key.pem"       # CA private key — most sensitive
chmod 600 "$OUTDIR/server-key.pem"   # Server private key
chmod 600 "$OUTDIR/client-key.pem"   # Client private key
chmod 644 "$OUTDIR/ca-cert.pem"      # CA public cert — safe to share
chmod 644 "$OUTDIR/server-cert.pem"  # Server public cert
chmod 644 "$OUTDIR/client-cert.pem"  # Client public cert

echo ""
echo "=============================================="
echo "  Done! Files generated in: $OUTDIR"
echo "=============================================="
echo ""
echo "  ca-key.pem      SECRET: Keep offline, never share"
echo "  ca-cert.pem     Share with both server and client"
echo "  server-key.pem  SECRET: Server only"
echo "  server-cert.pem Place on Server"
echo "  client-key.pem  SECRET: Client only"
echo "  client-cert.pem Place on Client"
echo ""
echo "  Expiry: $DAYS days. Rotate before they expire!"
echo "=============================================="
