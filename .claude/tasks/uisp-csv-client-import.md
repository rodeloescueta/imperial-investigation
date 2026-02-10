# Task: Import Client Data via UISP CRM API

**Date:** February 5, 2026
**Status:** Completed
**Duration:** ~4.5 hours (from CSV export to full import)

---

## Objective

Import ~10K clients with services from McBroad CSV export into new UISP instance using the CRM REST API, since UISP does not have native CSV import for CRM clients.

---

## Data Sources

| File | Location | Records | Content |
|------|----------|---------|---------|
| `414_export_2026-02-04_200703.csv` | `/home/imperial/projects/` | ~19,761 rows (~9,871 clients) | Clients + services (multi-row format) |
| `413_export_overview_2026-02-04_183358.csv` | `/home/imperial/projects/` | ~59K rows | Payment history (reference only, not imported) |

---

## Final Import Results

| Metric | Count |
|--------|-------|
| Clients created | **9,826** |
| Clients failed | 45 |
| Services created | **9,771** |
| Services failed | 26 |
| Services (no matching plan) | 19 |
| **Success rate** | **99.5%** |

---

## Implementation

### Scripts Created

Location: `/home/imperial/projects/imperial-investigation/scripts/`

| File | Purpose |
|------|---------|
| `import_clients.py` | Main import script |
| `config.py` | API config with token (gitignored) |
| `config.py.example` | Template config |
| `requirements.txt` | Python dependencies: `requests`, `pandas`, `python-dotenv` |
| `README.md` | Full usage instructions |

### API Details

- **Base URL:** `https://10.255.255.86/crm/api/v1.0`
- **Auth Header:** `X-Auth-App-Key: <token>`
- **SSL:** Self-signed cert, `verify_ssl=False`

### Key API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/organizations` | GET | Test connection |
| `/service-plans` | GET | Fetch plans + period IDs |
| `/clients` | POST | Create client |
| `/clients/{id}/services` | POST | Create service for client |
| `/clients/services?clientId={id}` | GET | Verify services |
| `/custom-attributes` | GET | List custom attributes |

---

## Issues Encountered & Fixes

### Issue 1: Custom Attribute IDs (422 Error)

**Error:** `"customAttributeId":["This value is not in valid type. Integer expected."]`

**Cause:** Script was passing string attribute keys (`"pppoeUsername"`) instead of integer IDs. UISP custom attributes are service-level (not client-level).

**Fix:** Removed client-level custom attributes from payload. Stored PPPoE username in client `note` field instead.

```python
# Instead of passing attributes array, append to note
pppoe_note = f"PPPoE: {pppoe_username}"
payload['note'] = f"{existing_note}\n{pppoe_note}".strip()
```

### Issue 2: Service Creation - Wrong Field Name (422 Error)

**Error:** `"servicePlanId":["Field servicePlanId is not allowed for recurring services."]`

**Cause:** The API requires `servicePlanPeriodId` (the specific pricing period), not `servicePlanId`.

**Fix:** Fetch service plans with their periods, use the first enabled period ID.

```python
# Correct: use the period ID, not the plan ID
payload = {'servicePlanPeriodId': period_id}

# Wrong: this doesn't work
payload = {'servicePlanId': plan_id}
```

### Issue 3: Service Fields Not Allowed (422 Error)

**Error:** `"status":["This field is not allowed."], "contractType":["This field is not allowed."]`

**Cause:** `status`, `contractType`, and `invoicingPeriodType` (as string) are not valid fields on the service creation endpoint.

**Fix:** Removed `status`, `contractType` from payload. The API sets sensible defaults.

### Issue 4: Date Format (400 Error)

**Error:** `"Invalid datetime \"2026-02-04\", expected one of the format \"Y-m-TH:i:sO\""`

**Cause:** API requires full ISO 8601 with timezone, not just `Y-m-d`.

**Fix:** Convert all dates to `Y-m-dTH:i:s+0800` format.

```python
# Correct
"2026-02-04T00:00:00+0800"

# Wrong
"2026-02-04"
```

### Issue 5: Original Client IDs Not Preserved

**Cause:** UISP auto-generates internal IDs. Original CSV IDs were being lost.

**Fix:** Added `userIdent` field to preserve original ID as Custom ID.

```python
payload['userIdent'] = client.get('original_id')  # e.g., "16560862"
```

---

## CSV Format Details

The McBroad CSV export uses a **multi-row format**:
- **Client rows** have an `Id` value in the first column
- **Service rows** follow immediately with empty `Id`, service data in columns 44+
- One client can have multiple service rows

```
Id,First name,Last name,...,Service,...
16560862,teresita,bajaro,...,,              ← Client row (no service inline)
,,,,...,07. RUBY 2000,...                   ← Service row
16560861,Maricris,Mora,...,,                ← Next client
,,,,...,01. SOLO PLAN,...                   ← Service row
```

### Column Mapping (CSV → API)

| CSV Column | API Field | Notes |
|------------|-----------|-------|
| Id | `userIdent` | Original ID preserved as Custom ID |
| First name | `firstName` | |
| Last name | `lastName` | |
| Emails | `contacts[].email` | First email used |
| Phones | `contacts[].phone` | Split on `/`, first used |
| Street 1 | `street1` | |
| City | `city` | |
| Country | `countryId` | Hardcoded to 170 (Philippines) |
| ZIP code | `zipCode` | |
| Client latitude | `addressGpsLat` | |
| Client longitude | `addressGpsLon` | |
| Note | `note` | |
| Registration date | Not imported | API doesn't accept on create |
| PPPOE Username (custom attribute) | `note` (appended) | Stored as "PPPoE: username" |
| Service | Lookup → `servicePlanPeriodId` | Matched by plan name |
| Service active from | `activeFrom` | ISO 8601 format |
| Service latitude | `addressGpsLat` | Service-level GPS |
| Service longitude | `addressGpsLon` | Service-level GPS |

---

## Service Plans

38 service plans were pre-created in UISP. The top plans by volume:

| Plan Name | Period ID | Count |
|-----------|-----------|-------|
| 03. SILVER 999 | 43 | 2,603 |
| 02.  BRONZE 799 | 31 | 2,451 |
| 01. SOLO PLAN | 25 | 1,656 |
| 04. GOLD 1200 | 49 | 1,290 |
| 05. PLATINUM 1400 | 37 | 794 |
| 06. DIAMOND 1600 | 55 | 676 |
| 08. OLD 800 | — | 175 |
| 07. RUBY 2000 | 19 | 153 |

### 10 Unmatched Plans (not created in UISP)

These affected only 19 services total:

- 11. SILVER INSTALLMENT 1099
- 18. SILVER INSTALLMENT 1199
- 23. OLD 1000
- 24. Imperial Bliz
- 28, BRONZE ADD 500 IST BILL
- 29, SILVER ADD 500 IST BILL
- BUSINESS PLAN 500
- IMPERIALBIZ500
- Imperial Bliz
- Test

---

## Failed Clients Analysis (45 total)

| Category | Count | Original IDs | Cause |
|----------|-------|--------------|-------|
| Empty/blank names | 36 | 16551053, 16557641, 16558655-16559019 | No first/last name in CSV - likely test or placeholder records |
| Named clients | 9 | See below | Likely special characters or data issues |

### Named Failed Clients

| Original ID | Name | Likely Cause |
|-------------|------|--------------|
| 16560481 | Meriel Magallanes | Unknown - needs investigation |
| 16559716 | Karen Grace Banesio Osorio | Unknown |
| 16559322 | Christian R. Del Mundo | Unknown |
| 16559321 | Marlon Villaceran | Unknown |
| 16559069 | Deseree Nuñez | Special character `ñ` |
| 16558157 | armando boholst | Unknown |
| 16557031 | Edwin Bucod | Unknown |
| 16556870 | Cindy Nonsanto Espinosa | Unknown |
| 16555679 | numeriana de ocampo | Unknown |
| 16554868 | GODFREY S. LASTIMOSO | Unknown |

**Failed clients JSON:** `scripts/failed_clients_20260205_234604.json`

---

## How to Re-run / Retry

### Retry Failed Clients Only

The failed clients need manual investigation in the CSV. Search by original ID:
```bash
grep "16560481\|16559716\|16559322" /home/imperial/projects/414_export_2026-02-04_200703.csv
```

### Full Re-import (if needed)

```bash
# 1. Truncate existing data
sudo docker exec unms-postgres psql -U postgres -d unms -c \
  "TRUNCATE TABLE ucrm.service CASCADE; TRUNCATE TABLE ucrm.client CASCADE;"

# 2. Run import
cd /home/imperial/projects/imperial-investigation/scripts
python3 import_clients.py --verbose
```

### Partial Re-import

```bash
# Skip first N clients, import next M
python3 import_clients.py --start 500 --limit 500 --verbose

# Dry run to preview
python3 import_clients.py --dry-run

# List available service plans
python3 import_clients.py --list-plans
```

---

## Database Details

- **Database:** `unms` (not `ucrm` — that's a schema, not a database)
- **Schema:** `ucrm`
- **Key tables:** `ucrm.client`, `ucrm.service`, `ucrm.service_attribute`, `ucrm.client_contact`
- **Sequences:** Auto-increment IDs continue from last value even after TRUNCATE
- **Custom attributes:** Service-level only (IDs: 2=pppoeusername, 3=device, 4=pppoepassword)

### Useful Queries

```sql
-- Count clients
SELECT COUNT(*) FROM ucrm.client;

-- Count services
SELECT COUNT(*) FROM ucrm.service;

-- Check a client by original ID
SELECT id, first_name, last_name, user_ident FROM ucrm.client WHERE user_ident = '16560862';

-- List custom attributes
SELECT id, name, key, attribute_type FROM ucrm.custom_attribute;
```

---

## Performance Notes

- Import rate: ~1.8-2.5 clients/second (with services)
- Full import of 9,871 clients: ~4.5 hours
- API has rate limiting (429 response) — script auto-retries with backoff
- 0.1s delay between clients to avoid overwhelming the API
- Log file generated per run: `import_YYYYMMDD_HHMMSS.log`

---

## What Was NOT Imported

| Data | Reason |
|------|--------|
| Payment history | Not available via client import API |
| Invoices | Requires database-level migration |
| Account balance | Cannot set via API |
| Invoice templates | Requires manual configuration |
| PPPoE passwords | Not in the CSV export |
| Service-level custom attributes (device, PPPoE) | Would need separate API calls per service |

---

## Remaining Work

- [ ] Investigate 9 named failed clients and retry
- [ ] Create 10 missing service plans and re-import 19 orphaned services
- [ ] Set PPPoE username/password on services via API (currently stored in client notes)
- [ ] Verify client count matches: CSV (9,871) vs UISP (9,826 + 45 failed = 9,871)
- [ ] Spot-check 10 random clients in UISP UI
