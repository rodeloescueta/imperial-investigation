#!/usr/bin/env python3
"""
UISP CRM Client Import Script

Imports clients and services from McBroad CSV export into UISP CRM via REST API.

Usage:
    1. Copy config.py.example to config.py and fill in your API token
    2. pip install -r requirements.txt
    3. python import_clients.py [--test] [--dry-run] [--start N] [--limit N]

Options:
    --test      Import only TEST_LIMIT clients (default: 10)
    --dry-run   Parse CSV and show what would be imported without making API calls
    --start N   Start importing from client number N (1-indexed)
    --limit N   Import only N clients
    --verbose   Show detailed progress
"""

import argparse
import csv
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)


class UISPClient:
    """UISP CRM API Client"""

    def __init__(self, base_url: str, api_token: str, verify_ssl: bool = False):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update({
            'X-Auth-App-Key': api_token,
            'Content-Type': 'application/json'
        })
        self.service_plans = {}  # Cache for service plan mapping

    def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make API request with error handling"""
        url = f"{self.base_url}/crm/api/v1.0{endpoint}"
        try:
            response = self.session.request(
                method,
                url,
                json=data,
                verify=self.verify_ssl,
                timeout=30
            )

            if response.status_code == 429:  # Rate limited
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self._request(method, endpoint, data)

            response.raise_for_status()
            return response.json() if response.text else {}

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {method} {url}")
            logger.error(f"Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def get_service_plans(self) -> dict:
        """Fetch all service plans and create name-to-period-id mapping"""
        if self.service_plans:
            return self.service_plans

        logger.info("Fetching service plans from UISP...")
        plans = self._request('GET', '/service-plans')

        for plan in plans:
            name = plan.get('name', '')
            # Get the first enabled period (typically 1-month)
            periods = plan.get('periods', [])
            period_id = None
            for period in periods:
                if period.get('enabled'):
                    period_id = period.get('id')
                    break
            if period_id:
                self.service_plans[name] = period_id
                # Also map normalized names (lowercase)
                normalized = name.lower().strip()
                self.service_plans[normalized] = period_id

        logger.info(f"Found {len(plans)} service plans")
        return self.service_plans

    def find_service_plan_period_id(self, service_name: str) -> Optional[int]:
        """Find service plan period ID by name with fuzzy matching"""
        if not self.service_plans:
            self.get_service_plans()

        # Try exact match first
        if service_name in self.service_plans:
            return self.service_plans[service_name]

        # Try normalized match
        normalized = service_name.lower().strip()
        if normalized in self.service_plans:
            return self.service_plans[normalized]

        # Try partial match
        for plan_name, period_id in self.service_plans.items():
            if service_name.lower() in plan_name.lower() or plan_name.lower() in service_name.lower():
                return period_id

        logger.warning(f"No matching service plan found for: {service_name}")
        return None

    def create_client(self, client_data: dict) -> dict:
        """Create a new client in UISP"""
        return self._request('POST', '/clients', client_data)

    def create_service(self, client_id: int, service_data: dict) -> dict:
        """Create a service for a client"""
        return self._request('POST', f'/clients/{client_id}/services', service_data)

    def get_organizations(self) -> list:
        """Get list of organizations"""
        return self._request('GET', '/organizations')

    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            orgs = self.get_organizations()
            logger.info(f"API connection successful. Found {len(orgs)} organization(s)")
            return True
        except Exception as e:
            logger.error(f"API connection failed: {e}")
            return False


class CSVParser:
    """Parse McBroad CSV export into client/service objects"""

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.clients = []

    def parse(self) -> list:
        """Parse CSV file and return list of client dicts with their services"""
        logger.info(f"Parsing CSV: {self.csv_path}")

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            current_client = None

            for row in reader:
                client_id = row.get('Id', '').strip()

                if client_id:  # This is a client row
                    # Save previous client if exists
                    if current_client:
                        self.clients.append(current_client)

                    # Start new client
                    current_client = self._parse_client_row(row)

                    # Check if this row also has embedded service data
                    service_name = row.get('Service', '').strip()
                    if service_name:
                        service = self._parse_service_from_row(row)
                        if service:
                            current_client['services'].append(service)

                else:  # This is a service row for current client
                    if current_client:
                        service = self._parse_service_from_row(row)
                        if service:
                            current_client['services'].append(service)

            # Don't forget the last client
            if current_client:
                self.clients.append(current_client)

        logger.info(f"Parsed {len(self.clients)} clients from CSV")
        return self.clients

    def _parse_client_row(self, row: dict) -> dict:
        """Extract client data from CSV row"""
        # Parse email (may be comma-separated)
        emails = row.get('Emails', '').strip()
        email = emails.split(',')[0].strip() if emails else ''

        # Parse phone (may have multiple separated by /)
        phones = row.get('Phones', '').strip()
        phone = phones.split('/')[0].strip() if phones else ''

        # Parse coordinates
        lat = row.get('Client latitude', '').strip()
        lon = row.get('Client longitude', '').strip()

        client = {
            'original_id': row.get('Id', '').strip(),
            'firstName': row.get('First name', '').strip(),
            'lastName': row.get('Last name', '').strip(),
            'username': row.get('Username', '').strip() or email,
            'companyName': row.get('Company name', '').strip(),
            'isLead': row.get('Is Lead', '').strip() == '1',
            'contacts': [],
            'street1': row.get('Street 1', '').strip(),
            'street2': row.get('Street 2', '').strip(),
            'city': row.get('City', '').strip(),
            'country': row.get('Country', '').strip() or 'Philippines',
            'state': row.get('State', '').strip(),
            'zipCode': row.get('ZIP code', '').strip(),
            'note': row.get('Note', '').strip(),
            'registrationDate': self._parse_date(row.get('Registration date', '')),
            # Custom attributes
            'attributes': {},
            'services': []
        }

        # Add contact info
        if email:
            client['contacts'].append({
                'email': email,
                'phone': phone,
                'name': f"{client['firstName']} {client['lastName']}".strip(),
                'isContact': True
            })

        # Add coordinates if available
        if lat and lon:
            try:
                client['addressGpsLat'] = float(lat)
                client['addressGpsLon'] = float(lon)
            except ValueError:
                pass

        # Custom attributes from CSV
        pppoe_username = row.get('PPPOE Username (custom attribute)', '').strip()
        facility = row.get('Facility (custom attribute)', '').strip()
        address_attr = row.get('Address (custom attribute)', '').strip()
        note_attr = row.get('NOTE (custom attribute)', '').strip()

        if pppoe_username:
            client['attributes']['pppoeUsername'] = pppoe_username
        if facility:
            client['attributes']['facility'] = facility
        if address_attr:
            client['attributes']['customAddress'] = address_attr
        if note_attr:
            client['attributes']['customNote'] = note_attr

        return client

    def _parse_service_from_row(self, row: dict) -> Optional[dict]:
        """Extract service data from CSV row"""
        service_name = row.get('Service', '').strip()
        if not service_name:
            return None

        service = {
            'name': service_name,
            'invoiceLabel': row.get('Service invoice label', '').strip() or service_name,
            'note': row.get('Service note', '').strip(),
            'activeFrom': self._parse_date(row.get('Service active from (Y-m-d)', '')),
            'activeTo': self._parse_date(row.get('Service active to (Y-m-d)', '')),
            'invoicingStart': self._parse_date(row.get('Service invoicing from (Y-m-d)', '')),
            'contractType': row.get('Service contract type (open/closed)', 'open').strip(),
            'invoicingPeriodType': 'backward' if row.get('Service invoicing type (backward/forward)', '').lower().startswith('back') else 'forward',
        }

        # Service coordinates
        lat = row.get('Service latitude', '').strip()
        lon = row.get('Service longitude', '').strip()
        if lat and lon:
            try:
                service['addressGpsLat'] = float(lat)
                service['addressGpsLon'] = float(lon)
            except ValueError:
                pass

        # Period and pricing
        try:
            period = int(row.get('Service period (months)', '1').strip() or '1')
            service['invoicingPeriodMonths'] = period
        except ValueError:
            service['invoicingPeriodMonths'] = 1

        # Individual price (if specified)
        price_str = row.get('Service individual price', '').strip()
        if price_str:
            try:
                service['individualPrice'] = float(price_str.replace(',', '').replace('₱', ''))
            except ValueError:
                pass

        return service

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse various date formats to ISO 8601 format with timezone (required by UISP API)"""
        if not date_str:
            return None

        date_str = date_str.strip()

        # Try ISO format with timezone - keep as-is if already in correct format
        if 'T' in date_str and ('+' in date_str or 'Z' in date_str):
            return date_str

        # Try ISO format with timezone but extract and reformat
        if 'T' in date_str:
            try:
                # Parse and add timezone
                dt = datetime.fromisoformat(date_str.replace('+08:00', '').replace('Z', ''))
                return dt.strftime('%Y-%m-%dT%H:%M:%S') + '+0800'
            except ValueError:
                pass

        # Try Y-m-d format - convert to full ISO with timezone
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%Y-%m-%dT00:00:00') + '+0800'
        except ValueError:
            pass

        return None


class ClientImporter:
    """Orchestrates the import process"""

    def __init__(self, uisp: UISPClient, parser: CSVParser):
        self.uisp = uisp
        self.parser = parser
        self.stats = {
            'clients_created': 0,
            'clients_failed': 0,
            'services_created': 0,
            'services_failed': 0,
            'services_no_plan': 0
        }
        self.failed_clients = []
        self.plan_mismatches = set()

    def run(self, dry_run: bool = False, start: int = 0, limit: int = None, verbose: bool = False):
        """Run the import process"""
        # Parse CSV
        clients = self.parser.parse()

        # Apply start/limit
        if start > 0:
            clients = clients[start:]
        if limit:
            clients = clients[:limit]

        total = len(clients)
        logger.info(f"Importing {total} clients...")

        if dry_run:
            logger.info("DRY RUN MODE - No API calls will be made")
            self._dry_run_report(clients)
            return

        # Fetch service plans
        try:
            self.uisp.get_service_plans()
        except Exception as e:
            logger.error(f"Failed to fetch service plans: {e}")
            logger.info("Available plans will need to be created in UISP first")
            return

        # Import clients
        for i, client in enumerate(clients, 1):
            try:
                self._import_client(client, verbose)

                if i % 50 == 0:
                    logger.info(f"Progress: {i}/{total} clients processed")

            except KeyboardInterrupt:
                logger.info("Import interrupted by user")
                break
            except Exception as e:
                logger.error(f"Failed to import client {client.get('original_id')}: {e}")
                self.stats['clients_failed'] += 1
                self.failed_clients.append({
                    'original_id': client.get('original_id'),
                    'name': f"{client.get('firstName')} {client.get('lastName')}",
                    'error': str(e)
                })

            # Small delay to avoid overwhelming API
            time.sleep(0.1)

        self._print_summary()

    def _import_client(self, client: dict, verbose: bool = False):
        """Import a single client with their services"""
        # Build client payload for UISP API
        payload = {
            'firstName': client['firstName'],
            'lastName': client['lastName'],
            'isLead': client['isLead'],
            'street1': client['street1'],
            'city': client['city'],
            'countryId': 170,  # Philippines - adjust as needed
            'zipCode': client['zipCode'],
            'userIdent': client.get('original_id'),  # Preserve original client ID
        }

        # Add optional fields
        if client.get('street2'):
            payload['street2'] = client['street2']
        if client.get('companyName'):
            payload['companyName'] = client['companyName']
        if client.get('note'):
            payload['note'] = client['note']
        if client.get('addressGpsLat'):
            payload['addressGpsLat'] = client['addressGpsLat']
        if client.get('addressGpsLon'):
            payload['addressGpsLon'] = client['addressGpsLon']

        # Add contacts
        if client.get('contacts'):
            payload['contacts'] = client['contacts']

        # Note: Custom attributes from CSV are stored in client['attributes'] but
        # UISP custom attributes are service-level (for PPPoE). We store the PPPoE username
        # in the client note field for reference, and it can be manually set on services later.
        pppoe_username = client.get('attributes', {}).get('pppoeUsername', '')
        if pppoe_username:
            existing_note = payload.get('note', '')
            pppoe_note = f"PPPoE: {pppoe_username}"
            payload['note'] = f"{existing_note}\n{pppoe_note}".strip() if existing_note else pppoe_note

        if verbose:
            logger.info(f"Creating client: {client['firstName']} {client['lastName']}")

        # Create client
        response = self.uisp.create_client(payload)
        new_client_id = response.get('id')

        if not new_client_id:
            raise Exception("No client ID returned from API")

        self.stats['clients_created'] += 1

        if verbose:
            logger.info(f"  Created client ID: {new_client_id}")

        # Create services
        for service in client.get('services', []):
            try:
                self._import_service(new_client_id, service, verbose)
            except Exception as e:
                logger.warning(f"  Failed to create service '{service.get('name')}': {e}")
                self.stats['services_failed'] += 1

    def _import_service(self, client_id: int, service: dict, verbose: bool = False):
        """Import a service for a client"""
        period_id = self.uisp.find_service_plan_period_id(service['name'])

        if not period_id:
            self.stats['services_no_plan'] += 1
            self.plan_mismatches.add(service['name'])
            logger.warning(f"  No plan found for service: {service['name']}")
            return

        # UISP API requires servicePlanPeriodId (not servicePlanId)
        payload = {
            'servicePlanPeriodId': period_id,
        }

        # Add optional fields
        if service.get('activeFrom'):
            payload['activeFrom'] = service['activeFrom']
        if service.get('activeTo'):
            payload['activeTo'] = service['activeTo']
        if service.get('note'):
            payload['note'] = service['note']
        if service.get('addressGpsLat'):
            payload['addressGpsLat'] = service['addressGpsLat']
        if service.get('addressGpsLon'):
            payload['addressGpsLon'] = service['addressGpsLon']

        if verbose:
            logger.info(f"  Creating service: {service['name']} (period ID: {period_id})")

        self.uisp.create_service(client_id, payload)
        self.stats['services_created'] += 1

    def _dry_run_report(self, clients: list):
        """Generate report for dry run"""
        services_by_plan = {}
        total_services = 0

        for client in clients:
            for service in client.get('services', []):
                plan_name = service.get('name', 'Unknown')
                services_by_plan[plan_name] = services_by_plan.get(plan_name, 0) + 1
                total_services += 1

        logger.info("\n" + "="*60)
        logger.info("DRY RUN REPORT")
        logger.info("="*60)
        logger.info(f"Total clients to import: {len(clients)}")
        logger.info(f"Total services to import: {total_services}")
        logger.info("\nServices by plan:")
        for plan, count in sorted(services_by_plan.items(), key=lambda x: -x[1]):
            logger.info(f"  {plan}: {count}")
        logger.info("="*60)

        # Show sample client
        if clients:
            logger.info("\nSample client (first in list):")
            sample = clients[0]
            logger.info(f"  Name: {sample['firstName']} {sample['lastName']}")
            logger.info(f"  Email: {sample['contacts'][0]['email'] if sample.get('contacts') else 'N/A'}")
            logger.info(f"  Address: {sample['street1']}, {sample['city']}")
            logger.info(f"  Services: {len(sample.get('services', []))}")
            for svc in sample.get('services', []):
                logger.info(f"    - {svc['name']}")

    def _print_summary(self):
        """Print import summary"""
        logger.info("\n" + "="*60)
        logger.info("IMPORT SUMMARY")
        logger.info("="*60)
        logger.info(f"Clients created:     {self.stats['clients_created']}")
        logger.info(f"Clients failed:      {self.stats['clients_failed']}")
        logger.info(f"Services created:    {self.stats['services_created']}")
        logger.info(f"Services failed:     {self.stats['services_failed']}")
        logger.info(f"Services (no plan):  {self.stats['services_no_plan']}")

        if self.plan_mismatches:
            logger.info("\nUnmatched service plans (need to be created in UISP):")
            for plan in sorted(self.plan_mismatches):
                logger.info(f"  - {plan}")

        if self.failed_clients:
            logger.info(f"\nFailed clients ({len(self.failed_clients)}):")
            for fc in self.failed_clients[:10]:  # Show first 10
                logger.info(f"  - {fc['name']} (ID: {fc['original_id']}): {fc['error']}")
            if len(self.failed_clients) > 10:
                logger.info(f"  ... and {len(self.failed_clients) - 10} more")

        # Save failed clients to file
        if self.failed_clients:
            failed_file = f'failed_clients_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(failed_file, 'w') as f:
                json.dump(self.failed_clients, f, indent=2)
            logger.info(f"\nFailed clients saved to: {failed_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Import clients from CSV to UISP CRM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--test', action='store_true',
                       help='Import only test limit of clients')
    parser.add_argument('--dry-run', action='store_true',
                       help='Parse CSV and show what would be imported')
    parser.add_argument('--start', type=int, default=0,
                       help='Start from client number N (0-indexed)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Import only N clients')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed progress')
    parser.add_argument('--list-plans', action='store_true',
                       help='List available service plans and exit')

    args = parser.parse_args()

    # Load configuration
    try:
        import config
    except ImportError:
        logger.error("config.py not found. Copy config.py.example to config.py and fill in your settings.")
        sys.exit(1)

    # Create API client
    uisp = UISPClient(
        base_url=config.UISP_BASE_URL,
        api_token=config.UISP_API_TOKEN,
        verify_ssl=getattr(config, 'VERIFY_SSL', False)
    )

    # Test connection first (unless dry run)
    if not args.dry_run:
        if not uisp.test_connection():
            logger.error("Cannot connect to UISP API. Check your settings.")
            sys.exit(1)

    # List plans if requested
    if args.list_plans:
        plans = uisp.get_service_plans()
        logger.info(f"\nAvailable service plans ({len(plans)}):")
        for name, period_id in sorted(plans.items()):
            logger.info(f"  {period_id}: {name}")
        sys.exit(0)

    # Create parser
    csv_parser = CSVParser(config.CSV_FILE_PATH)

    # Create importer
    importer = ClientImporter(uisp, csv_parser)

    # Determine limit
    limit = args.limit
    if args.test and not limit:
        limit = getattr(config, 'TEST_LIMIT', 10)

    # Run import
    importer.run(
        dry_run=args.dry_run,
        start=args.start,
        limit=limit,
        verbose=args.verbose
    )


if __name__ == '__main__':
    main()
