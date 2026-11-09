#!/usr/bin/env python3
"""Enter a UniFi API key without putting it in shell history or output."""
import getpass
import os
from pathlib import Path

os.umask(0o077)
key = getpass.getpass("Paste UniFi API key (hidden): ").strip()
if not key or any(c.isspace() for c in key):
    raise SystemExit("No valid key entered; nothing saved.")
destination = Path("/data/unifi-additive-sync/api-key")
destination.write_text(key + "\n", encoding="utf-8")
destination.chmod(0o600)
print("API key saved locally with owner-only permissions.")
