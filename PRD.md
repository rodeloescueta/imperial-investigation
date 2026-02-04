# Product Requirements Document
## UISP CRM System Handover & Migration

**Document Version:** 1.1
**Date:** February 4, 2026
**Status:** EMERGENCY - Active Vendor Dispute
**Project:** Imperial Networks UISP CRM System Handover
**Current URL:** https://uisp.imperial-networks.com/crm/
**Timeline:** Critical (Deadline: February 15, 2026)
**Target Environment:** On-Premise Server
**Previous Provider:** McBroad IT Solutions (AS151354)

---

## 1. Executive Summary

### 1.1 System Overview

UISP (Ubiquiti ISP Management Platform) is a comprehensive solution for Internet Service Providers (ISPs) and Wireless Internet Service Providers (WISPs). The platform consists of two integrated modules:

| Module | Function |
|--------|----------|
| **Network Module (UISP)** | Physical network infrastructure management - devices, towers, antennas, routers, and network topology |
| **CRM Module** | Customer relationship management - billing, invoicing, client services, support tickets, and communication |

### 1.2 Business Context

Imperial Networks (AS151066) operates an ISP serving approximately **9,871 clients**. The UISP CRM system is the core operational platform managing:
- Customer accounts and service subscriptions
- Network device monitoring and management
- Billing and invoice generation
- Support ticket handling
- Email communications
- Traffic monitoring and bandwidth management

### 1.3 Current Situation - CRITICAL

**Previous Provider:** McBroad IT Solutions
**Issue:** Vendor dispute over proprietary plugin ownership
**Impact:** Custom plugins DELETED on February 4, 2026 (before agreed Feb 15 deadline)

| Lost Component | Business Impact |
|----------------|-----------------|
| SMS Integration | No customer SMS notifications |
| MikroTik-UISP Integration | Manual network device management |
| PayMongo Payment Portal | **CRITICAL: Cannot collect online payments** |
| Custom Invoice Templates | Reverted to default format |

**See:** `SituationAnalysis.md` for full dispute documentation.

### 1.4 Handover Objectives

1. **Emergency data extraction** before February 15 deadline
2. **Complete data migration** to on-premise infrastructure
3. **Zero data loss** during transition
4. **Rebuild critical integrations** (PayMongo, SMS, MikroTik)
5. **Minimal service disruption** to existing clients
6. **Establish independent operations** free from vendor dependency

---

## 2. System Architecture

### 2.1 Platform Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        UISP Platform                            │
├─────────────────────────────┬───────────────────────────────────┤
│      Network Module         │         CRM Module                │
├─────────────────────────────┼───────────────────────────────────┤
│ • Device Management         │ • Client Management               │
│ • Site/Tower Topology       │ • Service Plans & Billing         │
│ • Firmware Updates          │ • Invoice Generation              │
│ • Network Monitoring        │ • Payment Processing              │
│ • Traffic Statistics        │ • Support Tickets                 │
│ • Outage Detection          │ • Email Notifications             │
│                             │ • Traffic Shaping                 │
│                             │ • Service Suspension              │
└─────────────────────────────┴───────────────────────────────────┘
```

### 2.2 Technical Stack

| Component | Technology |
|-----------|------------|
| **Deployment** | Docker containers |
| **Database** | PostgreSQL |
| **Web Server** | Nginx (reverse proxy) |
| **Backend** | PHP-based application |
| **API** | RESTful API with token authentication |
| **Plugins** | PHP-based extensibility system |

### 2.3 Plugin Architecture

UISP CRM supports plugins for extended functionality:

```
plugin/
├── manifest.json          # Plugin metadata & configuration schema
├── main.php               # Main execution script (scheduled/manual)
├── public.php             # Optional public-facing endpoint
├── hook_install.php       # Post-installation hook
├── hook_update.php        # Version update hook
├── hook_configure.php     # Configuration change hook
├── hook_enable.php        # Activation hook
├── hook_disable.php       # Deactivation hook
├── hook_remove.php        # Pre-removal hook
├── public/
│   ├── admin-zone.js      # Auto-loaded in admin pages
│   └── client-zone.js     # Auto-loaded in client portal
└── data/
    ├── config.json        # User-configured parameters
    ├── plugin.log         # Execution logs
    └── files/             # Uploaded configuration files
```

### 2.4 Key Integrations

| Integration Type | Purpose |
|------------------|---------|
| **Network Devices** | Ubiquiti hardware (airMAX, EdgeMax, UniFi) |
| **Payment Gateways** | Online payment processing |
| **Email Server** | SMTP for client notifications |
| **SMS Gateway** | Optional SMS notifications (via plugins) |
| **Accounting Software** | Optional QuickBooks integration (via plugins) |

---

## 3. Current State Documentation

### 3.1 Current VM Specifications (From McBroad)

```
VM Configuration:
├── OS: Ubuntu 22.04.2 LTS
├── Hypervisor: Proxmox VE 8.1.3
├── UISP Version: 2.4.206
├── Deployment: Docker containers
└── Database: PostgreSQL
```

### 3.2 System Metrics (From Dashboard)

| Metric | Value |
|--------|-------|
| **Total Clients** | ~9,871 |
| **Active Services** | ~523 (visible status indicator) |
| **Network Devices** | ~2,100 |
| **Connected Devices** | ~421 |
| **Email Statistics** | 3,794 tracked |

### 3.3 Plugin Status - CRITICAL UPDATE

**Status:** ALL CUSTOM PLUGINS DELETED (as of February 4, 2026)

#### Lost Plugins (McBroad Proprietary - Will NOT be provided)

| Plugin | Function | Replacement Needed |
|--------|----------|-------------------|
| **SMS Integration** | Customer SMS notifications | Yes - Twilio or custom |
| **MikroTik-UISP Integration** | Network device automation | Yes - RouterOS API |
| **PayMongo Payment Portal** | Online payment collection | Yes - CRITICAL PRIORITY |
| **Custom Invoice Templates** | Branded invoices | Yes - Recreate in UISP |
| **Other Automations** | Various workflows | Unknown scope |

#### Standard UISP Features (Still Available)

- Client database and management
- Invoice history and generation
- Payment record history
- Service plan management
- Support ticket system
- Email notifications (built-in)
- Network device inventory
- Traffic monitoring

#### Plugins to Install Post-Migration (Official Repository)

- [ ] Twilio SMS Gateway (replace custom SMS)
- [ ] Stripe/PayPal (temporary payment solution)
- [ ] QuickBooks Online (if needed)
- [ ] Client Signup Form
- [ ] Invoice CSV Export
- [ ] Revenue Report

### 3.4 Configuration Items to Document

**Before migration, export/document:**

- [ ] Organization settings
- [ ] Service plans and pricing
- [ ] Tax configurations
- [ ] Invoice templates (note: reverted to default)
- [ ] Email templates
- [ ] Payment gateway settings
- [ ] SMTP configuration
- [ ] User accounts and permissions
- [ ] API tokens in use
- [ ] Network device credentials
- [ ] SSL certificate details
- [ ] DNS configuration

### 3.5 Stakeholder Contacts

**Imperial Network Inc. (Client)**
| Role | Name | Contact |
|------|------|---------|
| Network Engineer | Ronaldo T. Marayag Jr. | noc@imperialnetworkph.com |
| (Additional contacts) | Jun Joseph Cacait | jj.cacait@imperialnetworkph.com |
| | Sernan Sargento | sp.sargento@imperialnetworkph.com |
| | Mok Alfonso | jmg.alfonso@imperialnetworkph.com |
| | Christian April Sarique | cg.sarique@imperialnetworkph.com |

**McBroad IT Solutions (Previous Provider)**
| Role | Name | Contact |
|------|------|---------|
| President & CTO | Roger Jayson Bourn Visto | roger.visto@mcbroad.com |
| Sr. Network Engineer | Ronmar Agbay | ronmar.agbay@mcbroad.com |
| | Jervy Delos Reyes | jervy.delosreyes@mcbroad.com |
| | Kert Rey Nikko Lumahang | nikko.lumahang@mcbroad.com |
| | Philip Niko Alvarado | philip.alvarado@mcbroad.com |

---

## 4. Migration Plan

### 4.1 Timeline Overview (14 Days)

```
Week 1                              Week 2
├─ Phase 1: Audit ─────┤├─ Phase 2: Prepare ───┤├─ Phase 3: Migrate ┤├─ Phase 4: Validate ─┤
   Days 1-3                Days 4-7               Days 8-10            Days 11-14
```

### 4.2 Phase 1: Audit & Backup (Days 1-3)

**Objectives:** Complete documentation of current state and full system backup

| Task | Priority | Owner | Status |
|------|----------|-------|--------|
| Export full database backup | Critical | - | [ ] |
| Document all system settings | Critical | - | [ ] |
| List all API integrations & tokens | High | - | [ ] |
| Export client data (CSV backup) | High | - | [ ] |
| Document network device inventory | High | - | [ ] |
| Screenshot all configuration pages | Medium | - | [ ] |
| Export invoice templates | Medium | - | [ ] |
| Document email templates | Medium | - | [ ] |
| List all installed plugins + configs | Medium | - | [ ] |
| Verify backup integrity | Critical | - | [ ] |

**Backup Commands (UISP):**
```bash
# Database backup (from UISP server)
docker exec -t ucrm-postgres pg_dumpall -c -U postgres > ucrm_backup_$(date +%Y%m%d).sql

# Full data directory backup
tar -czvf uisp_data_backup_$(date +%Y%m%d).tar.gz /home/unms/data
```

### 4.3 Phase 2: Prepare Target Environment (Days 4-7)

**Objectives:** Setup on-premise server with all dependencies

| Task | Priority | Owner | Status |
|------|----------|-------|--------|
| Provision on-premise server | Critical | - | [ ] |
| Install Ubuntu Server LTS | Critical | - | [ ] |
| Install Docker & Docker Compose | Critical | - | [ ] |
| Configure firewall rules | Critical | - | [ ] |
| Setup SSL certificates (Let's Encrypt) | Critical | - | [ ] |
| Configure static IP / DNS planning | High | - | [ ] |
| Install UISP fresh instance | High | - | [ ] |
| Test network connectivity | High | - | [ ] |
| Configure backup automation | Medium | - | [ ] |
| Setup monitoring (optional) | Low | - | [ ] |

**Server Requirements:**
```
Minimum Specs (up to 10,000 devices):
├── CPU: 4 cores
├── RAM: 8 GB (16 GB recommended)
├── Storage: 100 GB SSD
├── Network: 1 Gbps
└── OS: Ubuntu 20.04/22.04 LTS

Required Ports:
├── 80/TCP   - HTTP (redirects to HTTPS)
├── 443/TCP  - HTTPS (Web UI)
├── 2055/UDP - NetFlow
└── 8443/TCP - Device communication
```

### 4.4 Phase 3: Migration Execution (Days 8-10)

**Objectives:** Transfer all data to new environment

| Task | Priority | Owner | Status |
|------|----------|-------|--------|
| Stop UISP services on source | Critical | - | [ ] |
| Final database export | Critical | - | [ ] |
| Transfer database to target | Critical | - | [ ] |
| Restore database on target | Critical | - | [ ] |
| Transfer data files/media | High | - | [ ] |
| Reinstall and configure plugins | High | - | [ ] |
| Update API tokens if needed | High | - | [ ] |
| Configure SMTP settings | High | - | [ ] |
| Test admin login | Critical | - | [ ] |
| Prepare DNS cutover plan | High | - | [ ] |

**Migration Commands:**
```bash
# On source server - final backup
docker exec -t ucrm-postgres pg_dumpall -c -U postgres > final_backup.sql

# Transfer to target
scp final_backup.sql user@target-server:/path/to/restore/

# On target server - restore
cat final_backup.sql | docker exec -i ucrm-postgres psql -U postgres
```

### 4.5 Phase 4: Validation & Go-Live (Days 11-14)

**Objectives:** Verify functionality and complete cutover

| Task | Priority | Owner | Status |
|------|----------|-------|--------|
| Verify all client data migrated | Critical | - | [ ] |
| Test client portal login | Critical | - | [ ] |
| Test invoice generation | Critical | - | [ ] |
| Test payment processing | Critical | - | [ ] |
| Verify network device connectivity | Critical | - | [ ] |
| Test email notifications | High | - | [ ] |
| Test support ticket system | High | - | [ ] |
| Update DNS records | Critical | - | [ ] |
| Monitor for 24-48 hours | Critical | - | [ ] |
| Decommission old server | Low | - | [ ] |

---

## 5. Technical Requirements

### 5.1 On-Premise Server Specifications

**Recommended Configuration:**

```yaml
Hardware:
  CPU: 8 cores (Intel Xeon or AMD EPYC)
  RAM: 16 GB DDR4
  Storage:
    - OS: 50 GB SSD
    - Data: 200 GB SSD (NVMe preferred)
  Network: Dual 1 Gbps NICs (redundancy)
  UPS: Battery backup recommended

Software:
  OS: Ubuntu Server 22.04 LTS
  Docker: 24.x or later
  Docker Compose: 2.x or later
```

### 5.2 Network Requirements

```
Inbound Rules:
├── TCP 80    → Redirect to 443
├── TCP 443   → HTTPS Web Interface
├── TCP 8443  → Device Management
├── UDP 2055  → NetFlow Collection
└── TCP 22    → SSH (restricted IP)

Outbound Rules:
├── SMTP (25/465/587) → Email delivery
├── HTTPS (443)       → Updates, Let's Encrypt
└── NTP (123)         → Time synchronization
```

### 5.3 Backup Strategy

| Backup Type | Frequency | Retention | Storage |
|-------------|-----------|-----------|---------|
| Database full | Daily | 30 days | Off-site/Cloud |
| Database incremental | Hourly | 7 days | Local |
| Configuration | On change | 90 days | Version control |
| Full system snapshot | Weekly | 4 weeks | Off-site |

**Automated Backup Script:**
```bash
#!/bin/bash
# /opt/uisp-backup/daily-backup.sh

BACKUP_DIR="/backup/uisp"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
docker exec -t ucrm-postgres pg_dumpall -c -U postgres > "$BACKUP_DIR/db_$DATE.sql"

# Compress and retain 30 days
gzip "$BACKUP_DIR/db_$DATE.sql"
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +30 -delete

# Optional: Upload to cloud storage
# aws s3 cp "$BACKUP_DIR/db_$DATE.sql.gz" s3://your-bucket/uisp-backups/
```

### 5.4 Monitoring Setup

**Recommended Monitoring Points:**
- Server resources (CPU, RAM, Disk)
- Docker container health
- Database connection pool
- SSL certificate expiration
- Backup job status
- API response times

---

## 6. Risk Assessment

### 6.1 Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Cannot collect payments** | **Confirmed** | **Critical** | Rebuild PayMongo or use Stripe/PayPal immediately |
| **Data loss before Feb 15** | Medium | Critical | Export all data TODAY |
| **Limited admin access** | Confirmed | High | Document and escalate to McBroad |
| Data loss during migration | Low | Critical | Multiple verified backups, test restore |
| Extended downtime | Medium | High | Off-hours migration, DNS TTL reduction |
| Client portal inaccessible | Medium | High | Maintenance page, client notification |
| Network devices disconnect | Medium | Medium | Staged device reconfiguration |
| Email delivery issues | Medium | Medium | Test SMTP before cutover |
| MikroTik automation loss | Confirmed | Medium | Manual management until rebuilt |

### 6.2 Downtime Considerations

**Estimated Downtime:** 2-4 hours during final cutover

**Mitigation Steps:**
1. Reduce DNS TTL to 300 seconds (5 min) 48 hours before migration
2. Schedule migration during lowest usage window (typically 2-6 AM)
3. Send advance notification to clients 7 days and 24 hours before
4. Prepare maintenance page for old server during transition

### 6.3 Rollback Plan

**If critical issues arise post-migration:**

1. **Immediate (< 1 hour):** Revert DNS to original server
2. **Short-term (< 24 hours):** Keep source server running in read-only mode
3. **Recovery:** Restore latest backup to source if target is unrecoverable

**Rollback Checklist:**
- [ ] Source server still operational
- [ ] DNS revert commands prepared
- [ ] Team contact list for emergency
- [ ] Client communication template ready

### 6.4 Vendor Dispute Considerations

**Legal/Documentation Requirements:**
- [ ] Screenshot evidence of deleted plugins
- [ ] Archive all email correspondence (PDF)
- [ ] Document timeline of events
- [ ] Review original service agreement with McBroad
- [ ] Consult legal counsel if needed

**Key Dispute Points:**
1. Plugins deleted on Feb 4, deadline was Feb 15 (potential breach)
2. Admin access disputed - McBroad claims given, Imperial reports limited
3. No clear documentation of plugin IP ownership in original agreement

---

## 7. Integration Rebuild Requirements

### 7.1 PayMongo Payment Portal (CRITICAL)

**Priority:** CRITICAL - Revenue impact
**Timeline:** Must be operational within 1 week of migration

**Requirements:**
```
PayMongo Plugin:
├── public.php          # Public payment page for customers
├── main.php            # Payment processing logic
├── manifest.json       # Plugin configuration
├── Webhook handler     # Receive payment confirmations
├── UISP API integration # Update invoice status
└── Receipt generation  # Payment confirmation emails
```

**Alternative (Faster):**
- Install official Stripe or PayPal plugin
- Migrate to PayMongo after stabilization

### 7.2 SMS Integration

**Priority:** High
**Timeline:** Within 2 weeks of migration

**Option A: Twilio Plugin (Recommended)**
- Official plugin available in UCRM repository
- Well-documented, production-ready
- Cost: Twilio usage fees (~$0.0075/SMS)

**Option B: Local SMS Gateway**
- Build custom plugin for Philippine SMS providers
- Semaphore, Itexmo, or similar
- Lower cost per SMS, local support

### 7.3 MikroTik Integration

**Priority:** High
**Timeline:** Within 2 weeks of migration

**Functionality to Rebuild:**
- Automatic PPPoE account creation/deletion
- Bandwidth profile synchronization
- Service suspension/unsuspension
- Queue management for traffic shaping

**Approach:**
```
MikroTik Plugin:
├── RouterOS API connection
├── Client sync with UISP database
├── Webhook listeners for service changes
├── Scheduled sync jobs
└── Error handling and logging
```

### 7.4 Invoice Templates

**Priority:** Medium
**Timeline:** Before first billing cycle

**Tasks:**
- [ ] Recreate branded invoice template in UISP
- [ ] Add company logo and details
- [ ] Configure tax settings
- [ ] Test invoice generation
- [ ] Verify email delivery format

---

## 8. Handover Checklist (Updated for Vendor Dispute)

### 8.1 Credentials & Access

| Item | Location | Received |
|------|----------|----------|
| UISP Admin username/password | - | [ ] |
| Database root credentials | - | [ ] |
| Server SSH access | - | [ ] |
| SSL certificate files + keys | - | [ ] |
| Domain registrar access | - | [ ] |
| DNS provider credentials | - | [ ] |
| Payment gateway API keys | - | [ ] |
| SMTP credentials | - | [ ] |
| Cloud storage credentials (if any) | - | [ ] |

### 8.2 Documentation

| Document | Received |
|----------|----------|
| Network topology diagram | [ ] |
| IP address allocation | [ ] |
| Service plan definitions | [ ] |
| Custom workflow documentation | [ ] |
| Emergency contact list | [ ] |
| Vendor support contracts | [ ] |

### 8.3 Technical Assets

| Asset | Received |
|-------|----------|
| Full database backup | [ ] |
| Configuration exports | [ ] |
| Invoice/email templates | [ ] |
| Plugin configurations | [ ] |
| SSL certificates | [ ] |
| License keys (if applicable) | [ ] |

### 8.4 Knowledge Transfer

| Topic | Completed |
|-------|-----------|
| Daily operations walkthrough | [ ] |
| Billing cycle explanation | [ ] |
| Common support issues | [ ] |
| Plugin management | [ ] |
| Backup/restore procedures | [ ] |
| Troubleshooting guide | [ ] |

---

## 9. Reference Resources

### 9.1 Official Documentation

- [UISP Help Center](https://help.uisp.com/hc/en-us/sections/22589678486167-UISP-CRM)
- [UISP CRM API Documentation](https://help.uisp.com/hc/en-us/articles/22590956856087-UISP-CRM-API-Usage)
- [UCRM Plugins GitHub Repository](https://github.com/Ubiquiti-App/UCRM-plugins)
- [Plugin Development Documentation](https://github.com/Ubiquiti-App/UCRM-plugins/blob/master/docs/file-structure.md)

### 9.2 Community Resources

- [Ubiquiti Community Forums](https://community.ui.com/)
- [UISP Subreddit](https://www.reddit.com/r/UISP/)

---

## 10. Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| **UISP** | Ubiquiti ISP Management Platform |
| **UCRM** | Ubiquiti CRM (legacy name, now part of UISP) |
| **UNMS** | Ubiquiti Network Management System (legacy name) |
| **CPE** | Customer Premises Equipment |
| **WISP** | Wireless Internet Service Provider |
| **NetFlow** | Network protocol for collecting IP traffic information |

### B. Quick Reference Commands

```bash
# Check UISP status
docker ps | grep -E "(ucrm|unms)"

# View logs
docker logs -f unms

# Restart services
docker restart unms

# Access database CLI
docker exec -it ucrm-postgres psql -U postgres

# Check disk usage
docker system df
```

---

**Document Control:**
- Version 1.0 - Initial draft - February 4, 2026
- Version 1.1 - Updated with vendor dispute details, lost plugins, integration rebuild requirements - February 4, 2026
- Next review: Daily until migration complete

**Related Documents:**
- `SituationAnalysis.md` - Full vendor dispute documentation and emergency action plan
