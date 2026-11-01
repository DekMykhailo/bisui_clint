#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CERT_DIR="${CERT_DIR:-$ROOT/certs}"
DAYS="${DAYS:-365}"
CN="${CN:-localhost}"

mkdir -p "$CERT_DIR"
CERT="$CERT_DIR/cert.pem"
KEY="$CERT_DIR/key.pem"

if [[ -f "$CERT" && -f "$KEY" && "${FORCE:-0}" != "1" ]]; then
  echo "Certs already exist at $CERT_DIR (set FORCE=1 to overwrite)."
  exit 0
fi

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "$KEY" \
  -out "$CERT" \
  -days "$DAYS" \
  -subj "/CN=$CN" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

chmod 600 "$KEY"
echo "Wrote $CERT and $KEY"
