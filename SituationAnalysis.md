# Situation Analysis
## Imperial Networks UISP CRM - Vendor Dispute & Recovery

**Document Date:** February 4, 2026
**Status:** URGENT - Critical Business Impact
**Deadline:** February 15, 2026 (System Access Ends)

---

## 1. Executive Summary

Imperial Networks is experiencing an emergency situation with their UISP CRM system. The previous service provider (McBroad IT Solutions) has prematurely deleted custom plugins and integrations before the agreed February 15 deadline, causing immediate operational impact.

### Key Stakeholders

| Party | Role | Contact |
|-------|------|---------|
| **Imperial Network Inc.** | System Owner (Client) | NOC: noc@imperialnetworkph.com |
| **Ronaldo T. Marayag Jr.** | Network Engineer, Imperial | AS151066 |
| **McBroad IT Solutions** | Previous Provider | AS151354 |
| **Roger Jayson Bourn Visto** | President & CTO, McBroad | roger.visto@mcbroad.com |
| **Ronmar Agbay** | Sr. Network Engineer, McBroad | ronmar.agbay@mcbroad.com |

---

## 2. Timeline of Events

| Date | Event |
|------|-------|
| **Feb 3, 2026 4:04 PM** | Imperial formally requests UISP virtual image/container and admin account turnover |
| **Feb 3, 2026 4:16 PM** | McBroad agrees to provide backup BUT excludes proprietary plugins (SMS, MikroTik, PayMongo integrations) |
| **Feb 3, 2026 5:01 PM** | Imperial requests breakdown of excluded custom modules |
| **Feb 3, 2026 6:05 PM** | McBroad states all standard UISP features available, refers to Ubiquiti documentation |
| **Feb 3, 2026 9:21 PM** | McBroad provides VM specs: Ubuntu 22.04.2 LTS, UISP 2.4.206 |
| **Feb 4, 2026 9:13 AM** | Imperial acknowledges and prepares for migration |
| **Feb 4, 2026 5:23 PM** | Imperial requests full admin credentials in advance |
| **Feb 4, 2026 5:25 PM** | McBroad claims admin access was provided "since the beginning" |
| **Feb 4, 2026 5:34 PM** | Imperial reports cannot see Plugins tab, backup showing limited access error |
| **Feb 4, 2026 5:42 PM** | McBroad reiterates plugins are proprietary, will not be provided |
| **Feb 4, 2026 5:54 PM** | **CRITICAL:** Imperial discovers all plugins DELETED, invoice template reverted |
| **Feb 4, 2026 6:02 PM** | McBroad confirms removal, states plugins are "intellectual property" |

---

## 3. Current System State

### What Was DELETED (Premature - Before Feb 15 Deadline)

| Component | Function | Business Impact |
|-----------|----------|-----------------|
| **SMS Integration** | Customer notifications via SMS | Customers won't receive service alerts |
| **MikroTik-UISP Integration** | Network device automation | Manual device management required |
| **PayMongo / Payment Portal** | Online payment collection | **CRITICAL:** Cannot collect online payments |
| **Custom Invoice Templates** | Branded invoice generation | Invoices reverted to default format |
| **Other Custom Automations** | Various workflow automations | Unknown scope of impact |

### What Remains Available

| Component | Status |
|-----------|--------|
| Customer database | Available |
| Invoice/payment history | Available |
| Service plan configurations | Available |
| Network device inventory | Available |
| Support ticket history | Available |
| Standard UISP features | Available |
| Admin access | Disputed (Imperial reports limited) |

### System Specifications (From McBroad)

```
VM Configuration:
- OS: Ubuntu 22.04.2 LTS
- Hypervisor: Proxmox VE 8.1.3
- UISP Version: 2.4.206
```

---

## 4. Dispute Analysis

### McBroad's Position

1. Plugins are proprietary intellectual property of McBroad
2. Imperial never paid for development, provisioning, or maintenance
3. Plugins are not part of standard UISP (free Ubiquiti platform)
4. Willing to help migrate Imperial's own data only
5. System available until February 15

### Imperial's Position

1. Plugins were deleted BEFORE the agreed February 15 deadline
2. Cannot access Plugins tab despite claimed "admin access"
3. Backup function shows "limited access" error
4. Transition period was supposed to be ongoing

### Key Issues

| Issue | Description |
|-------|-------------|
| **Premature Deletion** | Plugins removed on Feb 4, deadline was Feb 15 |
| **Access Dispute** | McBroad claims admin given; Imperial reports limited access |
| **No Prior Agreement** | Unclear if plugin ownership was documented in original contract |
| **Business Continuity** | Payment collection capability compromised |

---

## 5. Risk Assessment

### Immediate Risks

| Risk | Severity | Likelihood | Impact |
|------|----------|------------|--------|
| Cannot collect payments | **Critical** | Confirmed | Revenue loss |
| Customer communication down | High | Confirmed | Service complaints |
| Data loss before Feb 15 | High | Possible | Operational failure |
| Extended downtime | High | Likely | Customer churn |

### Legal Considerations

- **Potential breach:** Early deletion before agreed deadline
- **Documentation needed:** Screenshots, emails, system logs
- **Contract review:** Original service agreement with McBroad
- **Evidence preservation:** Document current state immediately

---

## 6. Immediate Action Plan

### Priority 1: Emergency Data Export (DO TODAY)

```
Export Checklist:
[ ] System > Tools > Database Backup (attempt despite error)
[ ] Clients > Export all client data to CSV
[ ] Invoicing > Export all invoices
[ ] Payments > Export complete payment history
[ ] Services > Export service plan definitions
[ ] Network > Export device inventory
[ ] Settings > Screenshot ALL configuration pages
[ ] Templates > Copy/screenshot invoice templates
[ ] Email > Export email templates if possible
```

### Priority 2: Evidence Documentation

```
Document for Legal/Records:
[ ] Screenshot empty Plugins page
[ ] Screenshot any error messages
[ ] Screenshot current invoice template (reverted state)
[ ] Save all email correspondence (PDF)
[ ] Document timeline of events
[ ] Note any witnesses to system state
```

### Priority 3: Formal Communication

**Recommended Response to McBroad:**

```
Subject: Formal Notice - Premature System Modification Before Agreed Deadline

Dear Roger and McBroad Team,

We are writing to formally document that on February 4, 2026,
we discovered that all plugins and custom invoice templates
have been removed from our UISP system.

This action was taken BEFORE the agreed deadline of February 15, 2026,
as stated in your own communication: "the UISP standard features
and its hosting will remain available until 15 February."

We request:
1. Immediate restoration of system functionality until February 15
2. Full administrator access to perform our own backups
3. Written explanation for the premature modification

This premature action has caused immediate business impact to our
operations, including our ability to collect customer payments.

We reserve all rights regarding this matter.

[Signature]
```

---

## 7. Recovery Strategy

### Phase 1: Emergency Stabilization (Feb 4-5)

| Task | Owner | Deadline | Status |
|------|-------|----------|--------|
| Export all available data | Imperial NOC | Feb 4 | [ ] |
| Document evidence of deletion | Imperial NOC | Feb 4 | [ ] |
| Send formal notice to McBroad | Management | Feb 5 | [ ] |
| Consult legal if needed | Management | Feb 5 | [ ] |
| Identify alternative payment collection | Finance | Feb 5 | [ ] |

### Phase 2: New Infrastructure (Feb 5-10)

| Task | Owner | Deadline | Status |
|------|-------|----------|--------|
| Provision on-premise server | IT Team | Feb 6 | [ ] |
| Install Ubuntu 22.04 LTS | IT Team | Feb 6 | [ ] |
| Install Docker environment | IT Team | Feb 7 | [ ] |
| Install UISP 2.4.206 | IT Team | Feb 7 | [ ] |
| Configure network/firewall | IT Team | Feb 8 | [ ] |
| Setup SSL certificates | IT Team | Feb 8 | [ ] |
| Test base installation | IT Team | Feb 9 | [ ] |

### Phase 3: Data Migration (Feb 10-12)

| Task | Owner | Deadline | Status |
|------|-------|----------|--------|
| Obtain database backup from McBroad | Imperial NOC | Feb 10 | [ ] |
| Restore database to new instance | IT Team | Feb 10 | [ ] |
| Verify client data integrity | IT Team | Feb 11 | [ ] |
| Verify invoice/payment history | Finance | Feb 11 | [ ] |
| Test admin functions | IT Team | Feb 12 | [ ] |

### Phase 4: Integration Rebuild (Feb 12-15+)

| Integration | Replacement Approach | Priority | Status |
|-------------|---------------------|----------|--------|
| **PayMongo Payment** | Build custom plugin or use alternative gateway | Critical | [ ] |
| **SMS Notifications** | Install Twilio plugin (official) | High | [ ] |
| **MikroTik Integration** | RouterOS API plugin or custom build | High | [ ] |
| **Invoice Templates** | Recreate in UISP CRM settings | Medium | [ ] |

---

## 8. Replacement Solutions

### SMS Integration

**Option A: Twilio Plugin (Recommended)**
- Official plugin available in UCRM repository
- Well-documented, widely used
- Cost: Twilio usage fees only

**Option B: Custom SMS Gateway**
- Build PHP plugin for local SMS provider
- More control, potentially lower cost
- Development time: 2-3 days

### PayMongo Payment Portal

**Rebuild Strategy:**
```
PayMongo Plugin Requirements:
- Public payment page (public.php)
- PayMongo API integration
- Webhook handler for payment confirmation
- Invoice status update via UISP API
- Payment receipt generation
```

**Alternative Gateways:**
- Stripe (official plugin exists)
- PayPal (official plugin exists)
- DragonPay (custom build needed)
- GCash direct (custom build needed)

### MikroTik Integration

**Option A: Existing Plugins**
- Check UCRM-plugins repo for RouterOS integration
- May need customization

**Option B: Custom Build**
- Use MikroTik RouterOS API
- Sync with UISP client database
- Automate service suspension/activation

---

## 9. Resource Requirements

### Technical Resources Needed

| Resource | Purpose | Priority |
|----------|---------|----------|
| On-premise server | Host new UISP instance | Critical |
| PHP Developer | Rebuild custom plugins | High |
| Network Engineer | Migration & device reconfiguration | High |
| Database Administrator | Data migration & verification | High |

### Server Specifications (Minimum)

```
Hardware:
- CPU: 4 cores minimum (8 recommended)
- RAM: 8 GB minimum (16 GB recommended)
- Storage: 100 GB SSD
- Network: 1 Gbps connection
- Backup: External storage or cloud

Software:
- Ubuntu 22.04 LTS
- Docker & Docker Compose
- UISP 2.4.206 (match current version)
- SSL certificates (Let's Encrypt)
```

---

## 10. Business Continuity - Interim Measures

### Payment Collection (Immediate)

While PayMongo integration is rebuilt:
1. Enable bank transfer payments (manual posting)
2. Setup GCash/Maya direct payments with manual reconciliation
3. Consider temporary Stripe/PayPal if faster to deploy

### Customer Communication

While SMS integration is rebuilt:
1. Use email notifications (built into UISP)
2. Manual SMS for critical notices
3. Social media announcements for service updates

---

## 11. Lessons Learned & Recommendations

### For Future Vendor Relationships

1. **Document all custom development** in contracts
2. **Clarify IP ownership** before development begins
3. **Maintain own backups** independent of vendor
4. **Request source code** for custom integrations
5. **Include transition clauses** in service agreements

### For This Situation

1. **Prioritize data extraction** over plugin recovery
2. **Don't delay migration** waiting for resolution
3. **Build in-house capability** to avoid future dependency
4. **Document everything** for potential legal action

---

## 12. Appendices

### A. Email Thread Summary

Full email correspondence archived separately. Key communications:
- Feb 3: Initial turnover request
- Feb 3: McBroad excludes proprietary plugins
- Feb 4: Plugin deletion discovered
- Feb 4: McBroad confirms intentional removal

### B. Technical References

- [UISP Official Documentation](https://help.uisp.com/)
- [UCRM Plugins Repository](https://github.com/Ubiquiti-App/UCRM-plugins)
- [UISP API Documentation](https://help.uisp.com/hc/en-us/articles/22590956856087-UISP-CRM-API-Usage)

### C. Contact Information

**Imperial Network Inc.**
- NOC: noc@imperialnetworkph.com
- AS Number: AS151066

**McBroad IT Solutions**
- Roger Jayson Bourn Visto (President & CTO): roger.visto@mcbroad.com
- Ronmar Agbay (Sr. Network Engineer): ronmar.agbay@mcbroad.com
- AS Number: AS151354

---

**Document Control:**
- Version 1.0 - Initial Analysis - February 4, 2026
- Status: Active Emergency
- Next Review: Daily until resolution
