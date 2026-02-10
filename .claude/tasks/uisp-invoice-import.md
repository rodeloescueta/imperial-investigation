# Task: Import Invoices from Old UISP into New UISP via API

**Date:** February 10, 2026
**Status:** Running (started Feb 10, 19:15 PHT in tmux session `invoice-import`)
**Depends on:** `uisp-csv-client-import.md` (completed)
**Priority:** High — Old UISP access ends February 15, 2026

---

## Current State (as of Feb 10, 2026)

### What's Done

- [x] Script built and tested: `scripts/import_invoices.py`
- [x] Config updated: `scripts/config.py` has both old + new UISP credentials
- [x] All 64,301 invoices exported to `scripts/invoices_export.json` (129.4 MB)
- [x] Test run: 10/10 invoices created, 10/10 payments linked, 0 failures
- [x] Test data cleaned up — new UISP has no invoices/payments (clean slate)
- [x] Full import started (Feb 10, 19:15 PHT) in tmux session `invoice-import`

### What's Left

- [ ] Check import completed (reconnect to tmux session)
- [ ] Verify in UISP UI
- [ ] Spot-check random invoices

---

## How to Run (Resume Instructions)

### Quick Start

```bash
# 1. Start tmux (survives SSH disconnect)
tmux new -s invoice-import

# 2. Go to scripts directory
cd /home/imperial/projects/imperial-investigation/scripts

# 3. Run full import from the already-exported file
python3 import_invoices.py --import-from invoices_export.json --verbose

# 4. Detach tmux: press Ctrl+B, then D
# 5. Close SSH — import keeps running

# 6. To check progress later:
tmux attach -s invoice-import

# 7. Or check the log file:
ls -t import_invoices_*.log | head -1 | xargs tail -20
```

### If Something Goes Wrong

```bash
# Resume from a specific invoice index (e.g., skip first 5000 already imported)
python3 import_invoices.py --import-from invoices_export.json --resume-from 5000 --verbose

# Test with just 10 invoices first
python3 import_invoices.py --import-from invoices_export.json --test --verbose

# Dry run (show stats, don't import)
python3 import_invoices.py --import-from invoices_export.json --dry-run
```

### If You Need to Start Over

```bash
# Truncate invoices and payments from new UISP database
sudo docker exec unms-postgres psql -U postgres -d unms -c \
  "TRUNCATE TABLE ucrm.payment CASCADE;"
sudo docker exec unms-postgres psql -U postgres -d unms -c \
  "TRUNCATE TABLE ucrm.invoice CASCADE;"

# Then re-run the import
python3 import_invoices.py --import-from invoices_export.json --verbose
```

### If Export File Is Lost

```bash
# Re-export from old UISP (needs network access to uisp.imperial-networks.com)
python3 import_invoices.py --export-only
# Creates invoices_export.json (~130 MB, takes ~18 min)
```

---

## Export Results (Completed Feb 10)

**File:** `scripts/invoices_export.json` (129.4 MB)

| Metric | Value |
|--------|-------|
| **Total invoices exported** | **64,301** |
| Date range | 2025-03-01 to 2026-02-11 |
| Currency | PHP (all) |
| Items per invoice | 1-2 (avg 1.1) |

### Status Distribution (actual counts from export)

| Status | Code | Count | % |
|--------|------|-------|---|
| Paid | 3 | 60,012 | 93.3% |
| Unpaid | 1 | 3,478 | 5.4% |
| Partially paid | 2 | 688 | 1.1% |
| Void | 4 | 122 | 0.2% |
| Draft | 0 | 1 | <0.1% |

---

## Runtime Estimate

| Operation | Count | Notes |
|-----------|-------|-------|
| Invoices to create | ~64,178 | (64,301 minus 122 void, 1 draft) |
| Payments to create | ~60,700 | (paid + partially paid invoices) |
| **Estimated time** | **~9-17 hours** | Depends on API speed |

Each invoice = 1 POST. Each paid invoice = 1 additional POST (payment).
Rate observed in testing: ~1.3 invoices/sec including payment creation.

---

## Script Details

### Files

| File | Path | Purpose |
|------|------|---------|
| Import script | `scripts/import_invoices.py` | Main script |
| Config | `scripts/config.py` | API credentials (both old + new UISP) |
| Exported data | `scripts/invoices_export.json` | 64,301 invoices (129.4 MB) |
| Log file | `scripts/import_invoices_YYYYMMDD_HHMMSS.log` | Created on each run |
| Failed list | `scripts/failed_invoices_YYYYMMDD_HHMMSS.json` | Created if failures occur |

### CLI Options

```
--test              Import only 10 invoices
--limit N           Import only N invoices
--offset N          Start export from offset N
--resume-from N     Skip first N invoices during import (for resuming)
--dry-run           Show stats without importing
--export-only       Export invoices to JSON, don't import
--import-from FILE  Import from previously exported JSON file
--verbose, -v       Show per-invoice progress
```

### What the Script Does

1. Loads invoices from `invoices_export.json` (or fetches from old UISP API)
2. Builds client ID mapping: `original_client_id → new_client_id` via `userIdent`
3. For each invoice:
   - Skips void (status=4) and draft (status=0) invoices
   - Skips invoices where the client doesn't exist in new UISP
   - Creates invoice via `POST /clients/{clientId}/invoices`
   - For paid/partial invoices: creates linked payment via `POST /payments` with `invoiceIds`
4. Logs progress every 500 invoices with ETA
5. Saves failed invoices to JSON file

### Payment Method

All imported payments use **Cash** method (`6efe0fa8-36b2-4dd1-b049-427bffc7d369`).

The "Custom" payment method was tested but requires `providerName` and `providerPaymentId` fields — not suitable for bulk import. Cash method works without extra fields.

---

## API Findings (from testing)

### Invoice Creation

```
POST /crm/api/v1.0/clients/{clientId}/invoices
```

**Allowed fields:** `number`, `items[]`, `createdDate`, `maturityDays`, `notes`, `adminNotes`

**NOT allowed:**
- `dueDate` — auto-calculated from `createdDate + maturityDays`
- `status` — derived from payment linkage (can't set directly)
- `type` on items — always creates as "other" (cosmetic, doesn't affect amounts)

### Payment Creation (for marking invoices as paid)

```
POST /crm/api/v1.0/payments
```

**Payload:**
```json
{
    "clientId": 12492,
    "amount": 899.00,
    "currencyCode": "PHP",
    "methodId": "6efe0fa8-36b2-4dd1-b049-427bffc7d369",
    "createdDate": "2025-03-01T04:00:14+0800",
    "note": "Imported - Invoice #116252",
    "invoiceIds": [17]
}
```

This auto-sets invoice `status=3` (paid) and creates `paymentCovers` linkage.

---

## Payment Strategy Decision (RESOLVED)

**Decision: Import invoices + linked payments together via API.**

- New UISP had **0 payments** when checked (Feb 10) — no duplicates risk
- Team's earlier UI payment import either didn't complete or was cleared
- Each paid invoice gets a Cash payment linked via `invoiceIds`
- Gives proper invoice ↔ payment linkage and correct statuses

---

## Potential Issues

### 1. Client Not Found
~45 clients failed during original client import → their invoices will be skipped. Logged as `invoices_skipped_no_client` in summary.

### 2. Long Runtime
~9-17 hours. Use `tmux` to survive SSH disconnect. If interrupted, use `--resume-from N`.

### 3. Duplicate Invoice Numbers
If the team created new invoices on the new UISP between now and running the import, number conflicts may occur. Check before running:
```bash
curl -sk "https://10.255.255.86/crm/api/v1.0/invoices?limit=1" \
  -H "X-Auth-App-Key: <YOUR_API_TOKEN from config.py>"
```

### 4. Invoice Item Type
Old UISP has `type: "service"` on items. New UISP creates as `type: "other"`. Cosmetic only — amounts are correct.

---

## Verification Checklist (after import)

- [ ] Check invoice count matches (~64,178 expected, minus skipped)
- [ ] Paid invoices show status=3 in UISP UI
- [ ] Invoice numbers match old system
- [ ] Line items have correct amounts
- [ ] Spot-check 10 random clients — verify their invoices appear
- [ ] Check client account balances look reasonable

```bash
# Quick count check
curl -sk "https://10.255.255.86/crm/api/v1.0/invoices?limit=1&offset=60000" \
  -H "X-Auth-App-Key: <YOUR_API_TOKEN from config.py>"

# Database count
sudo docker exec unms-postgres psql -U postgres -d unms -c \
  "SELECT COUNT(*) FROM ucrm.invoice;"

sudo docker exec unms-postgres psql -U postgres -d unms -c \
  "SELECT COUNT(*) FROM ucrm.payment;"
```

---

## Reference

| Item | Value |
|------|-------|
| Client import task | `.claude/tasks/uisp-csv-client-import.md` |
| Payment history task | `.claude/tasks/uisp-payment-history-import.md` |
| PPPoE import task | `.claude/tasks/uisp-pppoe-import.md` |
| New UISP API | `https://10.255.255.86/crm/api/v1.0` |
| New UISP API key | See `scripts/config.py` → `UISP_API_TOKEN` |
| Old UISP API | `https://uisp.imperial-networks.com/crm/api/v1.0` |
| Old UISP API key | See `scripts/config.py` → `OLD_UISP_API_KEY` |
| Scripts directory | `/home/imperial/projects/imperial-investigation/scripts/` |
| Old UISP access deadline | February 15, 2026 |
| UISP database | `unms` database, `ucrm` schema |
