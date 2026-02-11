# Task: Migrate Staging UISP to Production Server

**Date:** February 11, 2026
**Status:** Planning — waiting for team decision on version
**Depends on:** All data imports completed on staging
**Priority:** High — must be done before DNS cutover

---

## Background

The current UISP at `10.255.255.86` is a **staging server**. All data imports (clients, invoices, payments) are being done here first. Once verified, everything needs to move to the production server.

---

## Key Finding: Old UISP Backup Not Available

We investigated whether we could use UISP's built-in backup/restore to clone the old UISP (McBroad) directly. **This is not possible.**

- The old UISP at `uisp.imperial-networks.com` is version **2.4.206**
- Our account has admin access but the **Backup feature is not visible** (searched "backup" → 0/0 results in Settings > General)
- McBroad likely restricted backup access to the super admin/owner account
- This confirms that the API extraction approach (scripts) was the correct path

**Screenshot evidence:** `Screenshot from 2026-02-11 09-10-47.png` — Settings > General page with 0/0 backup search results.

---

## Version Situation

| Instance | Version | Notes |
|----------|---------|-------|
| Old UISP (McBroad) | **2.4.206** | Access expires Feb 15, 2026 |
| Staging UISP | **3.0.151** | `10.255.255.86` — all data being imported here |
| Production UISP | **TBD** | Needs team decision |

### Version Decision Needed

- **Option 1 (Recommended):** Install **3.0.151** on production → backup/restore from staging is seamless
- **Option 2:** Install **2.4.206** on production → cannot restore 3.0.151 backup, would need to re-run all import scripts or do pg_dump with potential schema issues

**Preference:** Use 3.0.151 (latest) for production. No reason to downgrade unless a specific compatibility issue is found.

---

## Migration Approach: UISP Built-in Backup/Restore

UISP has a native backup/restore feature under **Settings > Backup** that captures everything — database, config, plugins, certificates.

### Steps

```
1. Finish all data imports on staging (clients ✓, invoices ✓, PPPoE pending)
2. Verify all data in UISP UI
3. On staging: Settings > Backup > Create Backup > Download file
4. Install fresh UISP 3.0.151 on production server
5. On production: Settings > Backup > Restore from File > Upload
6. Wait for restore to complete (may take several minutes with 60K+ invoices)
7. Log in with same credentials as staging
8. Update Hostname/IP in UISP settings to match production
9. Update DNS records
10. Connect production MikroTik router
11. Configure SSL certificate
```

### What the Backup Includes

- All clients, invoices, payments
- UISP NMS + CRM settings
- ROS plugin configuration
- Custom attributes
- User accounts
- SSL certificates (may need reissue for new domain/IP)

### What May Need Reconfiguration After Restore

- Hostname/IP (will reflect staging IP, needs update)
- DNS records
- SSL certificate (if domain changes)
- MikroTik router connection (if IP changes)
- SMTP settings (if different on prod)

---

## Alternative Approaches (If Backup/Restore Doesn't Work)

### Option B: pg_dump / pg_restore

```bash
# On staging
docker exec -t unms-postgres pg_dumpall -c -U postgres > full_backup.sql
gzip full_backup.sql

# Transfer to prod
scp full_backup.sql.gz user@prod-server:/tmp/

# On prod (after fresh UISP install)
gunzip full_backup.sql.gz
docker exec -i unms-postgres psql -U postgres < full_backup.sql
docker restart $(docker ps -q)
```

**Pros:** Fast, reliable
**Cons:** Only captures database — misses plugin configs, UISP settings, SSL certs. Versions must match exactly.

### Option C: Re-run Import Scripts

```bash
# Export from staging or old UISP, then run on prod
python3 import_invoices.py --import-from invoices_export.json --verbose
```

**Pros:** Clean slate, no version dependency
**Cons:** 14+ hours for invoices alone. Old UISP API access may be expired by then. Unnecessary repeat of work.

### Option D: Full Docker Data Copy

```bash
# On staging
sudo tar czf uisp-data.tar.gz /home/unms/data/

# Transfer to prod
scp uisp-data.tar.gz user@prod-server:/tmp/

# On prod (after fresh UISP install, containers stopped)
sudo systemctl stop uisp  # or docker compose down
sudo tar xzf /tmp/uisp-data.tar.gz -C /
sudo systemctl start uisp
```

**Pros:** Exact clone of everything
**Cons:** Path/permission issues possible, not officially supported, fragile

---

## SMTP Configuration (from Old UISP)

Found on old UISP Settings > General page. Save for production setup:

| Setting | Value |
|---------|-------|
| SMTP Server | Custom SMTP |
| Hostname | `smtp.hostinger.com` |
| Port | 465 |
| Security mode | SSL |
| Authentication | Enabled |
| Username | `customercare@imperial-networks.com` |
| Sender address | `customercare@imperial-networks.com` |
| Password | (not visible — ask team) |

---

## Old UISP Migration Tool (NMS Only)

The old UISP has a **Migration Mode** under Settings > Devices > Migration. This is specifically for **migrating Ubiquiti devices** (re-pointing them to a new UISP server), NOT for data migration.

How it works:
1. Enable Migration Mode on old UISP
2. Enter new UISP hostname/IP and port
3. Click "Apply Settings"
4. Old UISP pushes new UISP key to all connected Ubiquiti devices
5. Devices reconnect to new UISP

**Important:** This only applies to Ubiquiti network devices (AirMax, EdgeRouter, etc.), NOT CRM data. And it requires the backup/restore to be done first so devices have something to connect to.

**Note:** This may not be relevant if Imperial Networks primarily uses MikroTik routers (not Ubiquiti devices).

---

## Data Import Status (Prerequisites)

These must all be completed on staging before migrating to prod:

| Import | Status | Notes |
|--------|--------|-------|
| Clients | **Completed** | 9,826 imported, 45 failed (blank names) |
| Invoices | **Running** (~80%) | ~64,301 total, ETA ~12:00 PM PHT Feb 11 |
| Payments | **Running** (with invoices) | Created alongside each paid invoice |
| PPPoE Usernames | **Pending** | Waiting for team confirmation |
| Sites & Devices | **Not needed** | Auto-generated by ROS plugin |

---

## Checklist Before Migration

- [ ] All data imports completed and verified on staging
- [ ] Team decides on UISP version for production (recommend 3.0.151)
- [ ] Production server provisioned and accessible
- [ ] Fresh UISP installed on production (same version as staging)
- [ ] Staging backup created and downloaded
- [ ] Backup restored on production
- [ ] Hostname/IP updated on production
- [ ] DNS records updated
- [ ] SSL certificate configured
- [ ] MikroTik router connected
- [ ] SMTP configured (see settings above)
- [ ] Final verification of all data in production UI

---

## Reference

| Item | Value |
|------|-------|
| Staging server | `10.255.255.86` (UISP 3.0.151) |
| Old UISP | `uisp.imperial-networks.com` (UISP 2.4.206) |
| Old UISP access deadline | February 15, 2026 |
| Client import task | `.claude/tasks/uisp-csv-client-import.md` |
| Invoice import task | `.claude/tasks/uisp-invoice-import.md` |
| PPPoE import task | `.claude/tasks/uisp-pppoe-import.md` |
| Migration documentation | `.claude/docs/uisp-migration-data-import.md` |
