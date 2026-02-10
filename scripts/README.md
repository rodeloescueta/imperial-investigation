# UISP Client Import Scripts

Import ~10K clients with services from McBroad CSV exports into UISP CRM via REST API.

## Prerequisites

1. **Python 3.8+** installed
2. **UISP CRM API Token** - Generate from UISP:
   - Login to https://10.255.255.86/crm/
   - Navigate to: **System > Security > Users**
   - Edit admin user or create a dedicated API user
   - Generate App Key (API token)
3. **Service Plans** created in UISP matching CSV service names

## Setup

```bash
# Navigate to scripts directory
cd /home/imperial/projects/imperial-investigation/scripts

# Install dependencies
pip install -r requirements.txt

# Create config file
cp config.py.example config.py

# Edit config.py with your API token
nano config.py
```

## Configuration

Edit `config.py`:

```python
UISP_BASE_URL = "https://10.255.255.86"
UISP_API_TOKEN = "your-api-token-here"
CSV_FILE_PATH = "/home/imperial/projects/414_export_2026-02-04_200703.csv"
VERIFY_SSL = False  # Set to True if using valid SSL certificate
TEST_MODE = True
TEST_LIMIT = 10
```

## Service Plans

Before importing, create these service plans in UISP (System > Service Plans):

### Main Plans (High Volume)
| Plan Name | Count | Notes |
|-----------|-------|-------|
| 03. SILVER 999 | 2,603 | |
| 02.  BRONZE 799 | 2,451 | Note: double space after "02." |
| 01. SOLO PLAN | 1,656 | |
| 04. GOLD 1200 | 1,290 | |
| 05. PLATINUM 1400 | 794 | |
| 06. DIAMOND 1600 | 676 | |
| 08. OLD 800 | 175 | Legacy plan |
| 07. RUBY 2000 | 153 | |

### Business/Enterprise Plans (Low Volume)
| Plan Name | Count | Notes |
|-----------|-------|-------|
| DIA BGP TIM | 23 | Dedicated Internet Access |
| DIA BGP VM2 | 19 | Dedicated Internet Access |
| 23. OLD 1000 | 9 | Legacy |
| LEASED LINE 5GB | 3 | |
| BRONZE UNLIMITED 799 | 2 | |
| IMPERIAL SME 2999 | 2 | |
| 24. Imperial Bliz | 2 | |
| PLATINUM UNLIMITED 1400 | 1 | |
| GOLD UNLIMITED 1200 | 1 | |
| SILVER UNLIMITED 999 | 1 | |
| SOLO UNLIMITED 599 | 1 | |
| IMPERIAL SME 3999 | 1 | |
| LEASED LINE 10GB | 1 | |
| LEASED LINE 1GB | 1 | |
| LEASED LINE 2GB | 1 | |
| LEASED LINE 3GB | 1 | |
| LEASED LINE 4GB | 1 | |
| BUSINESS PLAN 500 | 1 | |
| 29, SILVER ADD 500 IST BILL | 1 | |
| 11. SILVER INSTALLMENT 1099 | 1 | |
| 28, BRONZE ADD 500 IST BILL | 1 | |
| IMPERIALBIZ500 | 1 | |
| Imperial Bliz | 1 | |
| 18. SILVER INSTALLMENT 1199 | 1 | |
| 26. DIA 300 MBPS | 1 | |
| Test | 1 | Can skip |

**Total: 9,870 services for 9,871 clients**

**Note:** The plan names must match exactly (the script does fuzzy matching but exact is better).

## Usage

### 1. Dry Run (Preview)
See what will be imported without making API calls:

```bash
python import_clients.py --dry-run
```

### 2. List Available Plans
Check which service plans exist in UISP:

```bash
python import_clients.py --list-plans
```

### 3. Test Import (10 clients)
Import a small batch to verify everything works:

```bash
python import_clients.py --test --verbose
```

### 4. Full Import
Import all clients:

```bash
python import_clients.py --verbose
```

### 5. Resume Import (if interrupted)
Start from a specific client number:

```bash
python import_clients.py --start 500 --verbose
```

### 6. Batch Import
Import in batches of 500:

```bash
# First batch
python import_clients.py --limit 500 --verbose

# Second batch
python import_clients.py --start 500 --limit 500 --verbose

# Third batch
python import_clients.py --start 1000 --limit 500 --verbose
# ... continue as needed
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--test` | Import only TEST_LIMIT clients (default: 10) |
| `--dry-run` | Parse CSV, show report, no API calls |
| `--start N` | Start from client N (0-indexed) |
| `--limit N` | Import only N clients |
| `--verbose, -v` | Show detailed progress |
| `--list-plans` | List available UISP service plans |

## Output Files

The script generates:
- `import_YYYYMMDD_HHMMSS.log` - Full import log
- `failed_clients_YYYYMMDD_HHMMSS.json` - Failed imports (if any)

## CSV Format

The import expects McBroad/UISP CSV export format with:
- Client rows have `Id` in first column
- Service rows follow client rows with empty `Id`
- One client may have multiple services

Example structure:
```
Id,First name,Last name,...,Service
12345,John,Doe,...,
,,,,...,01. SOLO PLAN
,,,,...,02. BRONZE 799
12346,Jane,Smith,...,
,,,,...,03. SILVER 999
```

## Custom Attributes Mapping

| CSV Column | UISP Field |
|------------|------------|
| PPPOE Username (custom attribute) | pppoeUsername |
| Facility (custom attribute) | facility |
| Address (custom attribute) | customAddress |
| NOTE (custom attribute) | customNote |

**Note:** You may need to create custom attribute fields in UISP first:
- Navigate to **System > Customization > Custom Attributes**
- Create attributes matching the keys above

## Troubleshooting

### API Connection Failed
- Verify UISP is accessible at the configured URL
- Check API token is valid
- Try `VERIFY_SSL = False` if using self-signed certificate

### Rate Limiting
The script automatically handles rate limits by waiting and retrying.

### Missing Service Plans
Run with `--dry-run` first to see which plans are needed:
```bash
python import_clients.py --dry-run
```

### Import Interrupted
Check the log file for the last successful import, then use `--start N` to resume.

## Limitations

| Data Type | Importable? | Notes |
|-----------|-------------|-------|
| Clients | ✅ Yes | Full contact info |
| Services | ✅ Yes | Linked to plans |
| Custom attributes | ⚠️ Partial | Fields must exist in UISP |
| Payment history | ❌ No | Requires database migration |
| Invoices | ❌ No | Requires database migration |
| Account balance | ❌ No | Must set manually |
