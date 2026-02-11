# Task: Extract Remaining Data from Old UISP API

**Date:** February 11, 2026
**Status:** ✅ Completed (Feb 11, 11:45 PHT) — all high-priority extractions done
**Priority:** High — Old UISP access expires February 15, 2026
**Depends on:** Invoice import (running), Client import (completed)

---

## Background

While waiting for the invoice import to finish, we explored all accessible API endpoints on the old UISP (`uisp.imperial-networks.com`) to identify what other data can and should be extracted before access expires on Feb 15.

---

## API Endpoint Inventory

### Accessible with Data

| Endpoint | Count | Description |
|----------|-------|-------------|
| `GET /clients` | ~10,113 | Client records — **already imported** |
| `GET /invoices` | ~64,301 | Invoices — **import running (~80%)** |
| `GET /payments` | ~61,000 | Payments — **being created with invoices** |
| `GET /clients/services` | **~10,340** | Service subscriptions per client |
| `GET /service-plans` | **74** | Service plan definitions |
| `GET /products` | **11** | One-time charge products |
| `GET /custom-attributes` | **5** | Custom attribute definitions |
| `GET /payment-methods` | **20** | Payment method definitions |
| `GET /client-logs` | ~10 | Very few log entries |
| `GET /countries` | Standard list | Country definitions |
| `GET /currencies` | Standard list | Currency definitions |

### Empty / No Data

| Endpoint | Result |
|----------|--------|
| `GET /scheduling/jobs` | 0 |
| `GET /quotes` | 0 |
| `GET /taxes` | 0 |
| `GET /refunds` | 0 |
| `GET /credit-notes` | 0 |
| `GET /surcharges` | Not accessible |

### Not Accessible (403/401)

| Endpoint | Notes |
|----------|-------|
| `GET /organizations` | 403 — restricted to super admin |
| `GET /invoice-templates` | Not accessible |
| NMS backup endpoints | Not accessible |

---

## Recommendation: What to Extract

### Priority 1: Services (~10,340 records)

**Why:** This is the most important remaining data. Each service record contains:

```json
{
  "id": 13,
  "clientId": 16549820,
  "servicePlanId": 4,
  "status": 1,
  "name": "02.  BRONZE 799",
  "attributes": [...]
}
```

**What it gives us:**
- Which service plan each client is subscribed to
- Service status (active, suspended, ended, etc.)
- Service-level custom attributes (may include PPPoE data)
- Direct feed into the **PPPoE import task**

**Effort:** Export ~10,340 records via paginated API calls. Similar to invoice export.

### Priority 2: Service Plans (74 plans)

**Why:** Need to verify the new UISP has all 74 plans. The team manually created some plans on the new UISP — need to identify what's missing or mismatched.

**All 74 plans from old UISP:**

| ID | Name | Notes |
|----|------|-------|
| 3 | 01. SOLO PLAN | |
| 4 | 02. BRONZE 799 | |
| 5 | 03. SILVER 999 | |
| 6 | 04. GOLD 1200 | |
| 7 | 05. PLATINUM 1400 | |
| 8 | 06. DIAMOND 1600 | |
| 9 | 07. RUBY 2000 | |
| 10 | 08. OLD 800 | |
| 11-17 | Installment plans (699-2100) | 7 plans |
| 18-24 | Installment plans v2 (899-2200) | 7 plans |
| 25 | 23. OLD 1000 | |
| 26, 34 | Imperial Bliz | |
| 27-28 | DIA 300 MBPS | Duplicate names |
| 29-33 | ADD 500 1ST BILL variants | 5 plans |
| 36 | IMPERIALBIZ500 | |
| 39 | diamond 1600 add 500 to 1st bill | |
| 40 | Test | |
| 41-57 | DIA BGP TIM / DIA BGP VM2 | Multiple entries |
| 58-65 | LEASED LINE (1GB-10GB) | 8 plans |
| 66 | DIA BGP TIM | |
| 67-69 | IMPERIAL SME (2999-4999) | 3 plans |
| 70-76 | UNLIMITED plans (599-2000) | 7 plans |
| 77-79 | SME PLAN (2999-4999) | 3 plans |
| 80 | DIA BGP VM2 | |

**Note:** All plans show `price: 0` via API. The actual pricing may be configured elsewhere or on the service level. All show as not archived.

**Effort:** Already extracted. Just need to compare with new UISP plans.

### Priority 3: Products (11 items)

**Why:** These are one-time charge items used on invoices. Should be recreated on the new UISP to maintain consistency for future billing.

| ID | Name | Price (₱) |
|----|------|-----------|
| 1 | Reconnection fee | 100.00 |
| 2 | Installment | 100.00 |
| 4 | Installation balance | 500.00 |
| 5 | CHANGE DUE DATE | 180.00 |
| 6 | 7 DAYS PRORATED | 233.00 |
| 7 | Router/AP Extender | 1,500.00 |
| 8 | APPLY FOR NEW INSTALL/DOWNGRADE BELOW 999 | 500.00 |
| 9 | 8 days Pro-Rata | 326.67 |
| 10 | 7 Days Consumed | 373.33 |
| 12 | ACTIVATION FEE | 500.00 |
| 13 | 17 DAYS CONSUMED | 340.00 |

**Effort:** Small — can be created manually in UISP UI or via API. Only 11 items.

### Priority 4: Payment Methods (custom ones)

**Why:** The old UISP has custom payment methods specific to Imperial Networks. These need to be set up on the new UISP for future billing.

**Standard methods (already in UISP by default):**
- Check, Cash, Bank transfer, PayPal, Stripe, Authorize.Net, etc.

**Custom methods that need to be created on new UISP:**

| Name | ID | Notes |
|------|----|-------|
| EASTWEST IMPERIAL | `72271b72-5c0a-45e2-94d1-cdf4d7cf10e2` | Bank account |
| BPI | `d9ec3a55-ba19-4f81-8f15-0ee96fdd6a5c` | Bank account |
| GCASH/MAYA | `d8c1eae9-d41d-479f-aeaf-38497975d7b3` | E-wallet |
| Paymongo Payment Gateway | `35781b67-abfd-4ace-a4cd-3f4cc8a775d0` | Payment gateway |

**Effort:** Manual setup in UISP UI. Just 4 custom methods.

### Priority 5: Custom Attributes (5 definitions)

**Why:** Reference for understanding data structure. Some may need to be recreated on the new UISP.

| ID | Name | Key | Type |
|----|------|-----|------|
| 1 | PPPOE Username | `pppoeUsername` | client |
| 2 | Facility | `facility` | client |
| 3 | Address | `address` | client |
| 5 | Service Plan | `servicePlan` | payment |
| 7 | NOTE | `note` | client |

**Note:** The new UISP already has PPPoE attributes set up at the **service level** (not client level) as required by the ROS plugin. The old UISP stored PPPoE at the **client level** (attribute id=1).

**Effort:** Already extracted. Just need to verify new UISP has what's needed.

### Low Priority: Client Logs (~10 records)

Only ~10 log entries exist. Example:

```json
{
  "id": 3,
  "clientId": 16550351,
  "createdDate": "2025-06-24T14:20:10+0800",
  "message": "BLK 10 LOT 3 SOUTHGATE 1 SPRINGTOWN VILLAS TANZA"
}
```

Appears to be address notes, not operational logs. Not worth importing.

---

## Recommended Action Plan

| Step | Action | Effort | Priority |
|------|--------|--------|----------|
| 1 | ~~Export all services (~10,340) to JSON~~ | ✅ Done (Feb 11, 10:36 PHT) | **High** |
| 2 | ~~Compare service plans (old 74 vs new UISP)~~ | ✅ Done (Feb 11, 10:40 PHT) | **High** |
| 3 | ~~Build PPPoE import using services data~~ | ✅ Done (Feb 11, 11:23 PHT) — 9,603/9,603 | **High** |
| 4 | Create 11 products on new UISP | ~10 min (manual or script) | Medium |
| 5 | Create 4 custom payment methods on new UISP | ~5 min (manual) | Medium |
| 6 | Verify custom attributes on new UISP | ~5 min | Low |

**Steps 1-3 directly feed into the PPPoE import task** (`.claude/tasks/uisp-pppoe-import.md`).

Steps 4-5 can be done manually in the UISP UI by the team or scripted.

---

## What's Already Done (No Action Needed)

| Data | Status |
|------|--------|
| Clients (~10,113) | 9,826 imported, 45 failed (blank names) |
| Invoices (~64,301) | Import running (~91% as of Feb 11, 10:31 PHT) |
| Payments (~61,000) | Being created alongside invoices |
| Services (~10,340) | ✅ Exported to `scripts/services_export.json` (19.1 MB) |
| Service Plans (74) | ✅ Exported to `scripts/service_plans_export.json` (100.7 KB) |
| Sites & Devices | Not needed — auto-generated by ROS plugin |

---

## Service Plans Comparison Results (Feb 11, 10:40 PHT)

**Old UISP: 74 plans → New UISP: 38 plans**

### Matched by name: 34 plans — no action needed

All major residential plans present (Solo, Bronze, Silver, Gold, Platinum, Diamond, Ruby, Unlimited variants, Leased Lines, SME, Business, Imperial Bliz). IDs differ between old/new but names match exactly.

### Missing from new UISP: 23 plans — **skip (0 services)**

All 23 missing plans have zero active/suspended/blocked services:
- 12 Installment plans (Solo through Ruby, both old and new pricing tiers)
- 5 "ADD 500 1ST BILL" variants (Solo, Gold, Platinum, Bronze, Silver)
- 3 SME PLAN variants (2999, 3999, 4999) — duplicates of IMPERIAL SME
- DIAMOND UNLIMITED 1600, RUBY UNLIMITED 2000
- IMPERIAL SME 4999
- diamond 1600 add 500 to 1st bill

**No need to create these on the new UISP.**

### Duplicate-name plans: 17 old IDs → 32 active services

The old UISP has multiple plans with identical names under different IDs. The new UISP has one of each. Services referencing unmatched old IDs need consolidation during PPPoE import:

| Plan Name | Old IDs (unmatched) | Active Services | Matched New ID |
|-----------|-------------------|-----------------|----------------|
| DIA BGP TIM | 41,43,44,45,46,47,50,51,52 | 18 active | → new plan "DIA BGP TIM" (id=26) |
| DIA BGP VM2 | 49,53,54,55,56,57 | 14 active | → new plan "DIA BGP VM2" (id=25) |
| LEASED LINE 5GB | 59,60 | 0 active (2 blocked) | → new plan "LEASED LINE 5GB" (id=24) |

### New on new UISP (not in old): 3 plans

- Default (id=1), SAMPLE (id=2), ULTRA (id=3) — likely test plans from setup. Clean up later.

### Old → New Plan ID Mapping (for PPPoE import)

```
Old ID → New ID (matched plans)
3  → 5   (01. SOLO PLAN)
4  → 6   (02. BRONZE 799)
5  → 8   (03. SILVER 999)
6  → 9   (04. GOLD 1200)
7  → 7   (05. PLATINUM 1400)
8  → 10  (06. DIAMOND 1600)
9  → 4   (07. RUBY 2000)
10 → 18  (08. OLD 800)
13 → 31  (11. SILVER INSTALLMENT 1099)
20 → 37  (18. SILVER INSTALLMENT 1199)
25 → 28  (23. OLD 1000)
26 → 35  (24. Imperial Bliz)
28 → 38  (26. DIA 300 MBPS)
30 → 32  (28, BRONZE ADD 500 IST BILL)
31 → 29  (29, SILVER ADD 500 IST BILL)
34 → 36  (Imperial Bliz)
36 → 33  (IMPERIALBIZ500)
40 → 34  (Test)
42 → 27  (BUSINESS PLAN 500)
58 → 23  (LEASED LINE 4GB)
61 → 24  (LEASED LINE 5GB)
62 → 22  (LEASED LINE 3GB)
63 → 21  (LEASED LINE 2GB)
64 → 20  (LEASED LINE 1GB)
65 → 19  (LEASED LINE 10GB)
66 → 26  (DIA BGP TIM)
67 → 16  (IMPERIAL SME 2999)
68 → 17  (IMPERIAL SME 3999)
70 → 15  (SOLO UNLIMITED 599)
71 → 11  (BRONZE UNLIMITED 799)
72 → 14  (SILVER UNLIMITED 999)
73 → 13  (GOLD UNLIMITED 1200)
74 → 12  (PLATINUM UNLIMITED 1400)
80 → 25  (DIA BGP VM2)

Duplicate consolidation (same-name, map to single new plan):
41,43,44,45,46,47,50,51,52 → 26  (DIA BGP TIM)
49,53,54,55,56,57           → 25  (DIA BGP VM2)
59,60                       → 24  (LEASED LINE 5GB)
```

---

## Reference

| Item | Value |
|------|-------|
| Old UISP API | `https://uisp.imperial-networks.com/crm/api/v1.0` |
| Old UISP API key | See `scripts/config.py` → `OLD_UISP_API_KEY` |
| Old UISP access deadline | February 15, 2026 |
| PPPoE import task | `.claude/tasks/uisp-pppoe-import.md` |
| Invoice import task | `.claude/tasks/uisp-invoice-import.md` |
| Staging-to-prod task | `.claude/tasks/uisp-staging-to-prod-migration.md` |
