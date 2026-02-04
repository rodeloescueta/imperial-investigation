# Imperial Networks UISP Migration Progress

**Document Date:** February 4, 2026
**Status:** Phase 1 Complete - Fresh UISP Installed
**UISP Version:** 2.4.206

---

## Completed Tasks

### 1. Docker Installation ✓
- Installed Docker Engine v29.2.1
- Installed Docker Compose plugin
- Added `imperial` user to docker group

### 2. UISP Installation ✓
- Installed UISP version **2.4.206** (matching McBroad's version for database compatibility)
- Location: `/home/unms/`
- All containers running:

| Container | Image | Purpose |
|-----------|-------|---------|
| `unms` | ubnt/unms:2.4.206 | Main UISP application |
| `ucrm` | ubnt/unms-crm:4.4.31 | CRM module |
| `unms-nginx` | ubnt/unms-nginx:2.4.206 | Web server (ports 80, 443) |
| `unms-postgres` | ubnt/unms-postgres:2.4.206 | PostgreSQL database |
| `unms-netflow` | ubnt/unms-netflow:2.4.206 | NetFlow collector (port 2055) |
| `unms-siridb` | ubnt/unms-siridb:2.4.206 | Time-series database |
| `unms-rabbitmq` | rabbitmq:3.7.28-alpine | Message queue |
| `unms-fluentd` | ubnt/unms-fluentd:2.4.206 | Logging |

### 3. Firewall Configuration ✓
- UFW enabled with rules:

| Port | Protocol | Purpose |
|------|----------|---------|
| 22 | TCP | SSH access |
| 80 | TCP | HTTP (redirects to HTTPS) |
| 443 | TCP | HTTPS Web UI |
| 8443 | TCP | Device communication |
| 2055 | UDP | NetFlow collection |

### 4. Backup Automation ✓
- Backup script: `/opt/uisp-backup/daily-backup.sh`
- Backup location: `/backup/uisp/`
- Schedule: Daily at 2:00 AM via crontab
- Retention: 30 days
- First backup created: `db_20260204_193601.sql.gz` (112 KB)

---

## UISP Installation Structure

```
/home/unms/
├── app/                              # Application files
│   ├── docker-compose.yml            # Container orchestration
│   ├── unms-cli                      # Management CLI tool
│   └── unms.conf                     # Configuration
│
└── data/                             # Persistent data
    ├── postgres/                     # Database files
    ├── ucrm/                         # CRM data
    ├── cert/                         # SSL certificates
    ├── logs/                         # Application logs
    ├── firmwares/                    # Device firmware
    └── unms-backups/                 # Built-in backups
```

---

## Access Information

| Resource | URL |
|----------|-----|
| UISP Web Interface | https://10.255.255.86 |
| CRM Module | https://10.255.255.86/crm/ |
| Local Access | https://localhost |

---

## What's Next

### Immediate (Before Feb 15 Deadline)

- [ ] **Complete UISP initial setup wizard**
  - Create admin account
  - Set organization name: Imperial Networks
  - Set timezone: Asia/Manila
  - Configure basic settings

- [ ] **Export data from McBroad's UISP**
  - Database backup: `docker exec -t ucrm-postgres pg_dumpall -c -U postgres > backup.sql`
  - Export clients to CSV (via UISP UI)
  - Export invoices (via UISP UI)
  - Export payment history (via UISP UI)
  - Screenshot all configuration pages

- [ ] **Import database to new instance**
  - Stop UISP services
  - Restore database: `cat backup.sql | docker exec -i unms-postgres psql -U postgres`
  - Verify data integrity
  - Start services

### Post-Migration

- [ ] **Configure SMTP for email notifications**
  - SMTP server settings
  - Test email delivery

- [ ] **Install official plugins** (from UISP plugin repository)
  - [ ] Twilio SMS Gateway (replace McBroad's custom SMS)
  - [ ] Stripe or PayPal (temporary payment solution)
  - [ ] Invoice CSV Export
  - [ ] Revenue Report

- [ ] **Rebuild custom integrations**
  - [ ] PayMongo Payment Portal (CRITICAL - revenue impact)
  - [ ] MikroTik RouterOS integration
  - [ ] Custom invoice templates

- [ ] **DNS cutover**
  - Reduce TTL to 300 seconds (48 hours before)
  - Update DNS records to point to new server
  - Monitor for issues

- [ ] **SSL certificate setup**
  - Configure Let's Encrypt
  - Set up auto-renewal

---

## Useful Commands

```bash
# Check UISP status
docker ps | grep -E "(unms|ucrm)"

# View logs
docker logs -f unms

# View CRM logs
docker logs -f ucrm

# Restart UISP
docker restart unms

# Restart all UISP containers
cd /home/unms/app && sudo docker compose restart

# Manual database backup
sudo /opt/uisp-backup/daily-backup.sh

# Access PostgreSQL CLI
docker exec -it unms-postgres psql -U postgres

# UISP CLI tool
sudo /home/unms/app/unms-cli --help
```

---

## System Information

| Component | Value |
|-----------|-------|
| OS | Ubuntu 24.04.3 LTS |
| Docker | 29.2.1 |
| UISP Version | 2.4.206 |
| CRM Version | 4.4.31 |
| Server IP | 10.255.255.86 |
| RAM | 3.8 GB (⚠️ below 8GB recommended) |
| Disk | ~27 GB free (⚠️ below 100GB recommended) |

**Note:** Consider upgrading RAM and disk before importing the full database with ~9,871 clients.

---

## Risk Mitigation

### Before Database Import
1. Create full backup of fresh installation
2. Document current state
3. Test restore procedure

### Rollback Plan
If issues occur after database import:
1. Stop UISP services
2. Restore fresh database backup
3. Restart services

---

## Related Documents

- `Brief.md` - UISP platform overview
- `PRD.md` - Full product requirements and migration plan
- `SituationAnalysis.md` - Vendor dispute documentation

---

**Last Updated:** February 4, 2026
**Next Review:** After database migration
