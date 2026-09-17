# Turbo Intruder — Rate Limit PoC Script

A Turbo Intruder script that tests whether a password-change endpoint
enforces server-side rate limiting, while clearly distinguishing valid
from invalid password responses.

## How the Script Works

The script runs in **two phases** inside Turbo Intruder:

### Phase 1 — Validation
Sends a fixed payload list (e.g. 306 passwords) once. One of them is the
correct password, placed at a known index. This reproduces the original
evidence that valid and invalid inputs return different responses.

### Phase 2 — Sustained Load
Keeps sending filler (wrong) passwords until a 60-second window closes.
The valid password is **never** re-sent, so the "valid" count stays at
exactly 1 while the request rate is sustained.

## Author

## Author

[![X](https://img.shields.io/badge/X-spy0x1-black?style=for-the-badge&logo=x&logoColor=white)](https://x.com/spy0x1)
