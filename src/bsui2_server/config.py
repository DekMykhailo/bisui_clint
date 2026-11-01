"""Runtime configuration for the BSUI2 server."""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PACKAGE_ROOT / "data" / "bsui2.db"
DEFAULT_CERT = PACKAGE_ROOT / "certs" / "cert.pem"
DEFAULT_KEY = PACKAGE_ROOT / "certs" / "key.pem"

PORT = int(os.getenv("BSUI2_PORT", "2137"))
HOST = os.getenv("BSUI2_HOST", "0.0.0.0")
DATABASE_URL = os.getenv(
    "BSUI2_DATABASE_URL",
    f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}",
)
SSL_CERTFILE = os.getenv("BSUI2_SSL_CERTFILE", str(DEFAULT_CERT))
SSL_KEYFILE = os.getenv("BSUI2_SSL_KEYFILE", str(DEFAULT_KEY))
