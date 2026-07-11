#!/usr/bin/env python3
"""Pull Taylor's Corner (89 Ewing St, Murwillumbah) fuel prices from the NSW
FuelCheck API and write prices.json in the shape the website expects.

Env:
  FUELCHECK_API_KEY     the api key (also sent as the `apikey` header)
  FUELCHECK_AUTH_BASIC  the "Basic <base64>" header used on the token call
  FUELCHECK_STATION     FuelCheck station code (default 18597 = Taylors Corner)

Output prices.json:
  { "updated": "<UTC ISO8601>", "prices": {"U91": 169.0, "Diesel": 188.0},
    "station": "18597", "source": "nsw-fuelcheck" }

If FuelCheck omits a fuel on a given run, the last known value for that fuel is
carried forward from the existing prices.json so the site never goes blank.
"""
import json, os, sys, uuid, urllib.request
from datetime import datetime, timezone

API_KEY    = os.environ["FUELCHECK_API_KEY"]
AUTH_BASIC = os.environ["FUELCHECK_AUTH_BASIC"]
STATION    = os.environ.get("FUELCHECK_STATION", "18597")

TOKEN_URL  = "https://api.onegov.nsw.gov.au/oauth/client_credential/accesstoken?grant_type=client_credentials"
PRICE_URL  = "https://api.onegov.nsw.gov.au/FuelPriceCheck/v1/fuel/prices/station/" + STATION

# FuelCheck fuel code -> our JSON key (the two fuels the site shows)
WANT = {"U91": "U91", "DL": "Diesel"}


# The onegov API gateway 403s the default Python-urllib User-Agent, so set our own.
USER_AGENT = "taylors-corner-fuel/1.0"


def get_token():
    req = urllib.request.Request(
        TOKEN_URL, headers={"Authorization": AUTH_BASIC, "User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["access_token"]


def get_station_prices(token):
    headers = {
        "Authorization": "Bearer " + token,
        "apikey": API_KEY,
        "Content-Type": "application/json; charset=utf-8",
        "transactionid": str(uuid.uuid4()),
        "requesttimestamp": datetime.now().strftime("%d/%m/%Y %I:%M:%S %p"),
        "User-Agent": USER_AGENT,
    }
    req = urllib.request.Request(PRICE_URL, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def load_previous():
    try:
        with open("prices.json") as f:
            return json.load(f).get("prices", {})
    except (OSError, ValueError):
        return {}


def main():
    data = get_station_prices(get_token())
    prev = load_previous()
    prices = {}
    for p in data.get("prices", []):
        code = p.get("fueltype")
        if code in WANT and isinstance(p.get("price"), (int, float)):
            prices[WANT[code]] = p["price"]

    # Carry forward any fuel missing from this run.
    for key in WANT.values():
        if key not in prices and key in prev:
            prices[key] = prev[key]
            print("WARN: carried forward %s from previous run" % key, file=sys.stderr)

    missing = [k for k in WANT.values() if k not in prices]
    if missing:
        print("ERROR: no price (new or previous) for %s. Response: %s"
              % (missing, json.dumps(data)), file=sys.stderr)
        sys.exit(1)

    out = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "prices": prices,
        "station": STATION,
        "source": "nsw-fuelcheck",
    }
    with open("prices.json", "w") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    print(json.dumps(out))


if __name__ == "__main__":
    main()
