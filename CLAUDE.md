# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a **documentation repository** for Imperial Networks' UISP (Ubiquiti ISP Management Platform) migration project. It tracks the emergency migration from McBroad IT Solutions' hosted UISP to an on-premise installation due to a vendor dispute.

**This repository contains no executable code** - only markdown documentation files.


## Plan & Review

### Before starting work

- Write a plan to .claude/tasks/TASK_NAME.md.
- The plan should be a detailed implementation plan and the reasoning behind them, as well as tasks broken down.
- Don't over plan it, always think MVP.
- Once you write the plan, firstly ask me to review it. Do not continue until I approve the plan.

### While implementing

- You should update the plan as you work.
- After you complete tasks in the plan, you should update and append detailed descriptions of the changes you made, so following tasks can be easily hand over to other engineers.


## Key Documents

| File | Purpose |
|------|---------|
| `PROGRESS.md` | Current migration status, completed tasks, troubleshooting guides, useful commands |
| `PRD.md` | Full product requirements, migration phases, technical specifications |
| `SituationAnalysis.md` | Vendor dispute documentation, timeline of events, recovery strategy |
| `Brief.md` | UISP platform overview for context |

## Project Context

- **Client**: Imperial Networks (AS151066) - ISP with ~9,871 customers
- **Platform**: UISP v2.4.206 (Ubiquiti ISP Management)
- **Deadline**: February 15, 2026 (access to McBroad system ends)
- **Server IP**: 10.255.255.86 (new on-premise installation)

## Current System Architecture

UISP runs as Docker containers on Ubuntu 24.04:
- `unms` - Main UISP application
- `ucrm` - CRM module
- `unms-postgres` - PostgreSQL database
- `unms-nginx` - Web server (ports 80, 443)
- `unms-netflow` - NetFlow collector (port 2055)

## Key Integrations

The MikroTik RouterOS integration (`ros-plugin`) is configured with:
- Plugin location: `/home/unms/data/ucrm/ucrm/data/plugins/ros-plugin/`
- Custom attributes: `device`, `pppoeusername`, `pppoepassword` (service-level)
- Router: `main-ac` at 10.86.0.23 (API port 8728)

## Useful Commands (on UISP server)

```bash
# UISP status
docker ps | grep -E "(unms|ucrm)"

# View logs
docker logs -f unms
docker logs -f ucrm

# Restart all containers
cd /home/unms/app && sudo docker compose restart

# Access PostgreSQL
docker exec -it unms-postgres psql -U postgres

# Check custom attribute keys
docker exec -it unms-postgres psql -U postgres -c \
  "SELECT id, name, key FROM ucrm.custom_attribute;"

# RouterOS plugin - check config
sudo sqlite3 /home/unms/data/ucrm/ucrm/data/plugins/ros-plugin/data/data.db \
  "SELECT key, value FROM config;"

# RouterOS plugin - force cache refresh
sudo sqlite3 /home/unms/data/ucrm/ucrm/data/plugins/ros-plugin/data/data.db \
  "UPDATE config SET value='2020-01-01' WHERE key='next_cache';"

# Trigger plugin rebuild
curl -k -X POST "https://localhost/crm/_plugins/ros-plugin/public.php" \
  -H "Content-Type: application/json" \
  -d '{"changeType":"update","target":"system","action":"insert","data":{"type":"device","id":1}}'

# Manual backup
sudo /opt/uisp-backup/daily-backup.sh
```

## Outstanding Tasks

See `PROGRESS.md` "What's Next" section for current priorities:
1. Export/import database from McBroad's UISP
2. Configure SMTP for email notifications
3. Install SMS plugin (Twilio)
4. Rebuild PayMongo payment integration
5. DNS cutover and SSL certificate setup
