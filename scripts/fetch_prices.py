#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SOXL 일별 종가와 원/달러 환율을 받아 prices.json 으로 저장한다.

GitHub Actions 에서 매일 실행된다. 표준 라이브러리만 쓴다.
출력 형식:  {"prices": [{"d": "2026-08-27", "c": 121.06}, ...],
             "fx": 1380.38, "fxDate": "2026-08-27",
             "fetchedAt": "2026-08-28T00:05:00Z", "source": "stooq"}
"""

import json, csv, io, sys, urllib.request, datetime

UA = {"User-Agent": "Mozilla/5.0 (compatible; soxl-ledger/1.0)"}
TICKER = "SOXL"
DAYS = 400                     # 보관할 최근 거래일 수


def get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


# ---------- 종가 ----------
def from_stooq():
    txt = get("https://stooq.com/q/d/l/?s=%s.us&i=d" % TICKER.lower())
    rows = list(csv.DictReader(io.StringIO(txt)))
    out = []
    for row in rows:
        d, c = row.get("Date"), row.get("Close")
        if not d or not c or c in ("N/A", "-"):
            continue
        out.append({"d": d, "c": round(float(c), 4)})
    if len(out) < 20:
        raise RuntimeError("stooq: rows=%d" % len(out))
    return out, "stooq"


def from_yahoo():
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/%s"
           "?range=2y&interval=1d" % TICKER)
    j = json.loads(get(url))
    res = j["chart"]["result"][0]
    ts = res["timestamp"]
    closes = res["indicators"]["quote"][0]["close"]
    out = []
    for t, c in zip(ts, closes):
        if c is None:
            continue
        d = datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d")
        out.append({"d": d, "c": round(float(c), 4)})
    if len(out) < 20:
        raise RuntimeError("yahoo: rows=%d" % len(out))
    return out, "yahoo"


# ---------- 환율 ----------
def fx_frankfurter():
    j = json.loads(get("https://api.frankfurter.dev/v1/latest?from=USD&to=KRW"))
    return round(float(j["rates"]["KRW"]), 2), j.get("date"), "frankfurter"


def fx_erapi():
    j = json.loads(get("https://open.er-api.com/v6/latest/USD"))
    return round(float(j["rates"]["KRW"]), 2), (j.get("time_last_update_utc") or "")[:16], "er-api"


def first_ok(fns, label):
    errs = []
    for fn in fns:
        try:
            return fn()
        except Exception as e:                      # noqa: BLE001
            errs.append("%s: %s" % (fn.__name__, e))
            print("  ! %s 실패 — %s" % (fn.__name__, e), file=sys.stderr)
    raise RuntimeError("%s 전부 실패\n%s" % (label, "\n".join(errs)))


def main():
    prices, psrc = first_ok([from_stooq, from_yahoo], "종가")
    prices.sort(key=lambda x: x["d"])
    # 날짜 중복 제거(뒤엣것 우선)
    seen = {}
    for p in prices:
        seen[p["d"]] = p["c"]
    prices = [{"d": d, "c": seen[d]} for d in sorted(seen)][-DAYS:]

    try:
        fx, fxdate, fsrc = first_ok([fx_frankfurter, fx_erapi], "환율")
    except Exception as e:                          # noqa: BLE001
        print("환율 조회 실패, 종가만 저장합니다: %s" % e, file=sys.stderr)
        fx, fxdate, fsrc = None, None, None

    data = {
        "prices": prices,
        "fx": fx,
        "fxDate": fxdate,
        "fetchedAt": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": psrc + ("+" + fsrc if fsrc else ""),
    }
    with open("prices.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    last = prices[-1]
    print("종가 %d일치 (출처 %s) · 최신 %s $%s" % (len(prices), psrc, last["d"], last["c"]))
    print("환율 %s (%s)" % (fx, fsrc))


if __name__ == "__main__":
    main()
