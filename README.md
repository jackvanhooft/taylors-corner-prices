# taylors-corner-prices

Live fuel prices for **Taylor's Corner Service Station** (89 Ewing St,
Murwillumbah NSW 2484), pulled from the **NSW FuelCheck** API on a schedule and
published as `prices.json` for the Taylor's Corner website to read.

- `fetch_prices.py` — gets a token, reads FuelCheck station **18597**, writes `prices.json`.
- `.github/workflows/update-prices.yml` — runs every 30 min and commits `prices.json` when it changes.
- The website fetches the raw URL of `prices.json` and re-polls every 5 min.

`prices.json` shape:

```json
{ "updated": "2026-07-11T01:20:00Z", "prices": { "U91": 169.0, "Diesel": 188.0 }, "station": "18597", "source": "nsw-fuelcheck" }
```

Fuel codes: FuelCheck `U91` -> `U91`, FuelCheck `DL` -> `Diesel`.

Credentials live in repo **Actions secrets** (`FUELCHECK_API_KEY`,
`FUELCHECK_AUTH_BASIC`), never in this repo.
