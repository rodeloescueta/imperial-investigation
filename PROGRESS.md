# Imperial Networks UISP Migration Progress

**Document Date:** February 4, 2026
**Status:** Phase 2 Complete - MikroTik Integration Working
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

### 5. UISP Initial Setup ✓
- Admin account created
- Organization configured
- Timezone set to Asia/Manila
- Basic settings configured

### 6. RouterOS Plugin Installation ✓
- Installed **ros-plugin v2.3.5** from [MadaMzandu/uisp-ros-plugin](https://github.com/MadaMzandu/uisp-ros-plugin)
- Plugin provides real-time PPPoE provisioning for MikroTik RouterOS
- Replaces the deleted `routeros-suspension` plugin from McBroad

**Plugin Location:** `/home/unms/data/ucrm/ucrm/data/plugins/ros-plugin/`

### 7. Custom Attributes Configuration ✓
Created service-level custom attributes in UISP:

| Attribute Name | Key | Type | Purpose |
|----------------|-----|------|---------|
| Device | `device` | Choice | Select MikroTik router |
| PPPoE Username | `pppoeusername` | Text | PPPoE account username |
| PPPoE Password | `pppoepassword` | Text | PPPoE account password |

### 8. MikroTik Integration ✓
- Router added to plugin: `main-ac` (10.86.0.23)
- API connection working on port 8728
- Webhook configured and receiving events
- PPPoE secrets syncing to MikroTik automatically

**Required MikroTik Configuration:**
```
/ppp profile add name=SAMPLE rate-limit=35M/35M
/ppp profile add name=ULTRA rate-limit=100M/100M
```

**Plugin Attribute Mapping (in data.db):**
| Setting | Value |
|---------|-------|
| device_name_attr | `device` |
| pppoe_user_attr | `pppoeusername` |
| pppoe_pass_attr | `pppoepassword` |

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
    │   └── ucrm/data/plugins/        # Installed plugins
    │       └── ros-plugin/           # RouterOS plugin
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
| RouterOS Plugin Panel | https://10.255.255.86/crm/_plugins/ros-plugin/public.php?page=panel |
| Local Access | https://localhost |

---

## How the MikroTik Integration Works

1. **Add Client** in UISP with a service
2. **Fill Custom Attributes**: Device (router), PPPoE Username, PPPoE Password
3. **Webhook fires** automatically on save
4. **Plugin creates PPPoE secret** on the assigned MikroTik router
5. **Suspend/Unsuspend** actions automatically disable/enable the PPPoE account

**Supported Actions:**
- Insert (new service) → Creates PPPoE secret
- Edit (modify service) → Updates PPPoE secret
- Suspend → Disables PPPoE account
- Unsuspend → Re-enables PPPoE account
- Delete → Removes PPPoE secret

---

## What's Next

### Immediate (Before Feb 15 Deadline)

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
  - Re-run plugin cache sync
  - Start services

### Post-Migration

- [ ] **Configure SMTP for email notifications**
  - SMTP server settings
  - Test email delivery

- [ ] **Install additional plugins** (from UISP plugin repository)
  - [ ] Twilio SMS Gateway (replace McBroad's custom SMS)
  - [ ] Stripe or PayPal (temporary payment solution)
  - [ ] Invoice CSV Export
  - [ ] Revenue Report

- [ ] **Rebuild PayMongo integration** (CRITICAL - revenue impact)
  - Build custom plugin or find alternative
  - Test payment processing

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

# Check RouterOS plugin logs
sudo cat /home/unms/data/ucrm/ucrm/data/plugins/ros-plugin/data/plugin.log

# Check plugin job queue
sudo cat /home/unms/data/ucrm/ucrm/data/plugins/ros-plugin/data/queue.json

# Trigger plugin cache refresh
curl -k -X POST "https://localhost/crm/_plugins/ros-plugin/public.php" \
  -H "Content-Type: application/json" \
  -d '{"changeType":"admin","target":"cache"}'

# Trigger device rebuild
curl -k -X POST "https://localhost/crm/_plugins/ros-plugin/public.php" \
  -H "Content-Type: application/json" \
  -d '{"changeType":"update","target":"system","action":"insert","data":{"type":"device","id":1}}'
```

---

## RouterOS Plugin Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "input does not match any value of profile" | PPPoE profile doesn't exist on MikroTik | Create matching profiles on router |
| Services not syncing | Cache needs refresh | Set `next_cache` to past date in data.db |
| Webhook not firing | Webhook not configured | Click "Add webhook" in plugin settings |
| Panel not loading | Service worker cache issue | Clear browser cache or use incognito |

### Plugin Database Commands

```bash
# Check plugin config
sudo sqlite3 /home/unms/data/ucrm/ucrm/data/plugins/ros-plugin/data/data.db \
  "SELECT key, value FROM config WHERE key LIKE '%attr%';"

# Check synced services
sudo sqlite3 /home/unms/data/ucrm/ucrm/data/plugins/ros-plugin/data/data.db \
  "SELECT * FROM services;"

# Check cached services
sudo sqlite3 /home/unms/data/ucrm/ucrm/data/plugins/ros-plugin/data/cache.db \
  "SELECT id, username, password, device FROM services;"

# Force cache refresh
sudo sqlite3 /home/unms/data/ucrm/ucrm/data/plugins/ros-plugin/data/data.db \
  "UPDATE config SET value='2020-01-01' WHERE key='next_cache';"
```

---

## System Information

| Component | Value |
|-----------|-------|
| OS | Ubuntu 24.04.3 LTS |
| Docker | 29.2.1 |
| UISP Version | 2.4.206 |
| CRM Version | 4.4.31 |
| RouterOS Plugin | 2.3.5 |
| Server IP | 10.255.255.86 |
| MikroTik Router | 10.86.0.23 (main-ac) |
| RAM | 3.8 GB (⚠️ below 8GB recommended) |
| Disk | ~27 GB free (⚠️ below 100GB recommended) |

**Note:** Consider upgrading RAM and disk before importing the full database with ~9,871 clients.

---

## Risk Mitigation

### Before Database Import
1. Create full backup of fresh installation
2. Document current state
3. Test restore procedure
4. Note plugin configurations (will need reconfiguration)

### Rollback Plan
If issues occur after database import:
1. Stop UISP services
2. Restore fresh database backup
3. Reconfigure RouterOS plugin
4. Restart services

---

## Related Documents

- `Brief.md` - UISP platform overview
- `PRD.md` - Full product requirements and migration plan
- `SituationAnalysis.md` - Vendor dispute documentation

---

**Last Updated:** February 4, 2026 (22:45 PHT)
**Next Review:** After database migration
