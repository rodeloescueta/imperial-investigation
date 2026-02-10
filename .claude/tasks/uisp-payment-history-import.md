# Task: Import Payment History via UISP CRM API

**Date:** February 10, 2026
**Status:** Pending
**Depends on:** `uisp-csv-client-import.md` (completed)

---

## Objective

Import ~59K payment records from McBroad CSV export into new UISP instance using the CRM payments API.

---

## Data Source

| File | Location | Records |
|------|----------|---------|
| `413_export_overview_2026-02-04_183358.csv` | `/home/imperial/projects/` | 59,041 payments |

### CSV Columns

| # | Column | Example |
|---|--------|---------|
| 1 | Method | `Paymongo Payment Gateway`, `Cash`, `ecPay` |
| 2 | Client name | `kimberly tutor` |
| 3 | Amount | `₱799.00`, `₱1,600.00` |
| 4 | Created date | `2026-02-04T18:31:58+08:00` |
| 5 | Organization name | `Imperial Network Inc.` |
| 6 | Client ID | `16557854` (original ID, stored as `userIdent` in new UISP) |
| 7 | Amount (numeric) | `799.00487804878` |
| 8 | Currency | `PHP` |
| 9 | Note | (mostly blank) |
| 10 | Admin name | `Mcbroad Admin`, `monicaannebrioso` |
| 11 | Admin ID | `1000`, `1004` |
| 12 | Check number | (mostly blank) |
| 13 | Service Plan (custom attribute) | (mostly blank) |

### Date Range

- **Earliest:** 2025-03-26
- **Latest:** 2026-02-04
- **~10 months** of payment history

---

## Data Statistics

### Payment Methods (59,041 total)

| Method | Count | UISP Payment Method | Method ID (UUID) |
|--------|-------|---------------------|------------------|
| Paymongo Payment Gateway | 26,098 | `Custom` | `d8c1eae9-d41d-479f-aeaf-38497975d7b3` |
| Cash | 19,076 | `Cash` | `6efe0fa8-36b2-4dd1-b049-427bffc7d369` |
| ecPay | 10,706 | `Custom` | `d8c1eae9-d41d-479f-aeaf-38497975d7b3` |
| GCASH/MAYA | 1,575 | `Custom` | `d8c1eae9-d41d-479f-aeaf-38497975d7b3` |
| (blank) | 978 | `Custom` | `d8c1eae9-d41d-479f-aeaf-38497975d7b3` |
| Bank transfer | 283 | `Bank transfer` | `4145b5f5-3bbc-45e3-8fc5-9cda970c62fb` |
| EASTWEST IMPERIAL | 212 | `Bank transfer` | `4145b5f5-3bbc-45e3-8fc5-9cda970c62fb` |
| Check | 106 | `Check` | `11721cdf-a498-48be-903e-daa67552e4f6` |
| BPI | 5 | `Bank transfer` | `4145b5f5-3bbc-45e3-8fc5-9cda970c62fb` |
| test payments only | 2 | Skip | — |

### Data Quality

- All 59,041 records have a Client ID
- 978 records have blank payment method
- All amounts in PHP currency

---

## API Details

### Create Payment Endpoint

```
POST /crm/api/v1.0/payments
```

**Confirmed working fields** (tested):

```json
{
    "clientId": 2668,              // UISP internal client ID (NOT the original CSV ID)
    "amount": 799.00,
    "methodId": "6efe0fa8-...",    // UUID from /payment-methods
    "createdDate": "2026-02-04T18:31:58+0800",
    "note": "Paymongo Payment Gateway",
    "checkNumber": null,
    "currencyCode": "PHP"
}
```

### Available Payment Methods in UISP

| Name | UUID |
|------|------|
| Check | `11721cdf-a498-48be-903e-daa67552e4f6` |
| Cash | `6efe0fa8-36b2-4dd1-b049-427bffc7d369` |
| Bank transfer | `4145b5f5-3bbc-45e3-8fc5-9cda970c62fb` |
| Custom | `d8c1eae9-d41d-479f-aeaf-38497975d7b3` |

(Full list of 19 methods available — see API response in previous task)

### Delete Payment (for cleanup)

```
DELETE /crm/api/v1.0/payments/{id}
```

---

## Implementation Plan

### Step 1: Build Client ID Mapping

The payment CSV has original `Client ID` (e.g., `16557854`) but the UISP API needs the new internal `clientId`. We stored the original ID as `userIdent` during client import.

**Approach:** Query all clients from UISP API, build a `userIdent → id` mapping.

```python
# Fetch all clients and build mapping
# GET /crm/api/v1.0/clients?limit=10000
mapping = {}  # {"16557854": 2668, "16560862": 2669, ...}
```

**Note:** ~45 clients failed during import. Payments for these clients will need to be skipped or handled separately.

### Step 2: Map Payment Methods

```python
METHOD_MAP = {
    "Cash": "6efe0fa8-36b2-4dd1-b049-427bffc7d369",
    "Check": "11721cdf-a498-48be-903e-daa67552e4f6",
    "Bank transfer": "4145b5f5-3bbc-45e3-8fc5-9cda970c62fb",
    "BPI": "4145b5f5-3bbc-45e3-8fc5-9cda970c62fb",
    "EASTWEST IMPERIAL": "4145b5f5-3bbc-45e3-8fc5-9cda970c62fb",
    "Paymongo Payment Gateway": "d8c1eae9-d41d-479f-aeaf-38497975d7b3",
    "ecPay": "d8c1eae9-d41d-479f-aeaf-38497975d7b3",
    "GCASH/MAYA": "d8c1eae9-d41d-479f-aeaf-38497975d7b3",
    "": "d8c1eae9-d41d-479f-aeaf-38497975d7b3",
}
```

### Step 3: Parse CSV and Import

For each payment row:
1. Look up `Client ID` → new UISP `clientId` via mapping
2. Map payment method → UISP method UUID
3. Parse amount from `Amount (numeric)` column (already numeric)
4. POST to `/payments`
5. Store original payment method name in `note` field for audit trail

### Step 4: Verify

- Compare count: CSV (59,041) vs UISP payments
- Spot-check 10 random payments
- Verify amounts match

---

## Script Structure

Reuse existing script framework from client import:

```
/home/imperial/projects/imperial-investigation/scripts/
├── import_clients.py          # Existing client import (completed)
├── import_payments.py         # NEW - payment import script
├── config.py                  # Shared config (API token, URLs)
├── requirements.txt           # Dependencies
└── README.md                  # Usage instructions
```

### Script Flow

```python
1. Load config (API token, CSV path)
2. Test API connection
3. Build client ID mapping (userIdent → UISP id)
4. Parse payment CSV
5. For each payment:
   a. Look up clientId from mapping
   b. Map payment method to UUID
   c. POST to /payments
   d. Log result
6. Print summary
```

---

## Key Considerations

### Client ID Mapping Challenge

- Payment CSV uses original Client ID (e.g., `16557854`)
- UISP stores original ID in `userIdent` field
- Need to fetch ALL clients from UISP API first to build mapping
- The client listing API may paginate — check `limit` and `offset` params
- 45 clients failed import → their payments (~250 records estimated) will be orphaned

### Amount Precision

- `Amount` column has currency symbol and commas: `₱1,600.00`
- `Amount (numeric)` column has raw numbers: `1600` or `799.00487804878`
- Some amounts have extra decimal precision (e.g., `799.00487804878`) — likely a display quirk
- **Use `Amount (numeric)` column** and round to 2 decimal places

### Date Format

- CSV dates are already in ISO 8601 with timezone: `2026-02-04T18:31:58+08:00`
- UISP API expects: `Y-m-dTH:i:sO` format (e.g., `2026-02-04T18:31:58+0800`)
- Minor difference: CSV has `+08:00`, API wants `+0800` — strip the colon

### Performance Estimate

- 59,041 payments at ~2 payments/second = ~8 hours
- Consider increasing parallelism or removing delay
- Payments are simpler than clients (single API call, no sub-resources)

### Note Field Strategy

Store the original payment method in `note` for audit trail:
```
"note": "Original method: Paymongo Payment Gateway"
```

This preserves the distinction between Paymongo, ecPay, GCASH/MAYA etc. even though they all map to "Custom" in UISP.

---

## Useful Commands

```bash
# Check current payment count in UISP
curl -sk "https://10.255.255.86/crm/api/v1.0/payments?limit=1" \
  -H "X-Auth-App-Key: <API_TOKEN from config.py>"

# List payment methods
curl -sk "https://10.255.255.86/crm/api/v1.0/payment-methods" \
  -H "X-Auth-App-Key: <API_TOKEN from config.py>"

# Truncate payments (if needed for re-import)
sudo docker exec unms-postgres psql -U postgres -d unms -c \
  "TRUNCATE TABLE ucrm.payment CASCADE;"

# Count payments in database
sudo docker exec unms-postgres psql -U postgres -d unms -c \
  "SELECT COUNT(*) FROM ucrm.payment;"
```

---

## Reference

- **Previous task:** `.claude/tasks/uisp-csv-client-import.md`
- **API base:** `https://10.255.255.86/crm/api/v1.0`
- **Auth header:** `X-Auth-App-Key`
- **API token:** Stored in `scripts/config.py`
- **Database:** `unms` database, `ucrm` schema
- **Sudo password:** Required for database operations
