#!/usr/bin/env python3
"""
UISP Services & Service Plans Export Script

Exports client services (~10,340) and service plans (74) from old McBroad UISP
before access expires on Feb 15, 2026.

Usage:
    1. Ensure config.py has OLD_UISP_BASE_URL and OLD_UISP_API_KEY
    2. python export_services.py --test       # Test with 10 services
    3. python export_services.py              # Full export
    4. python export_services.py --verbose    # Full export with per-record logging
"""

import argparse
import json
import logging
import os
import sys
import time
from collections import Counter
from datetime import datetime

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
log_file = f'export_services_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(__name__)


class UISPApi:
    """Generic UISP CRM API client"""

    def __init__(self, base_url, api_token, verify_ssl=False):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        self.session.headers.update({
            'X-Auth-App-Key': api_token,
            'Content-Type': 'application/json'
        })

    def _request(self, method, endpoint, data=None, retries=3):
        url = f"{self.base_url}/crm/api/v1.0{endpoint}"
        for attempt in range(retries):
            try:
                response = self.session.request(
                    method, url, json=data,
                    verify=self.verify_ssl, timeout=30
                )

                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited. Waiting {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                if response.status_code >= 400:
                    error_text = response.text[:500]
                    raise Exception(
                        f"HTTP {response.status_code}: {error_text}"
                    )

                return response.json() if response.text else {}

            except requests.exceptions.ConnectionError as e:
                if attempt < retries - 1:
                    wait = 5 * (attempt + 1)
                    logger.warning(f"Connection error, retrying in {wait}s... ({e})")
                    time.sleep(wait)
                else:
                    raise

        raise Exception(f"Failed after {retries} retries")

    def get(self, endpoint):
        return self._request('GET', endpoint)

    def test_connection(self):
        try:
            try:
                orgs = self.get('/organizations')
                logger.info(f"Connected to {self.base_url} ({len(orgs)} org(s))")
                return True
            except Exception:
                clients = self.get('/clients?limit=1')
                logger.info(f"Connected to {self.base_url} (verified via clients endpoint)")
                return True
        except Exception as e:
            logger.error(f"Connection failed to {self.base_url}: {e}")
            return False


def export_service_plans(api, export_file='service_plans_export.json'):
    """Export all service plans (single call, ~74 records)"""
    logger.info("=== Exporting service plans from old UISP ===")

    plans = api.get('/service-plans')
    logger.info(f"Fetched {len(plans)} service plans")

    with open(export_file, 'w') as f:
        json.dump(plans, f, indent=2)

    file_size_kb = os.path.getsize(export_file) / 1024
    logger.info(f"Saved to {export_file} ({file_size_kb:.1f} KB)")

    # Print plan summary
    for plan in plans:
        name = plan.get('name', '?')
        pid = plan.get('id', '?')
        period = plan.get('invoicingPeriodMonths', '?')
        logger.info(f"  Plan {pid}: {name} (period: {period} months)")

    return plans


def export_services(api, export_file='services_export.json', limit=None, offset=0, verbose=False):
    """Export all client services with pagination"""
    logger.info("=== Exporting client services from old UISP ===")

    all_services = []
    page_size = 500
    current_offset = offset
    total_exported = 0
    start_time = time.time()

    while True:
        if limit and total_exported >= limit:
            break

        batch_limit = min(page_size, limit - total_exported) if limit else page_size

        logger.info(f"Fetching services offset={current_offset}, limit={batch_limit}...")
        try:
            services = api.get(f'/clients/services?limit={batch_limit}&offset={current_offset}')
        except Exception as e:
            logger.error(f"Failed to fetch at offset {current_offset}: {e}")
            logger.info(f"Saved {total_exported} services so far. Resume with --offset {current_offset}")
            break

        if not services:
            break

        all_services.extend(services)
        total_exported += len(services)
        current_offset += len(services)

        if verbose:
            for s in services:
                logger.info(f"  Service {s.get('id')}: clientId={s.get('clientId')} plan={s.get('servicePlanId')} status={s.get('status')}")

        if total_exported % 1000 == 0 or len(services) < batch_limit:
            elapsed = time.time() - start_time
            rate = total_exported / elapsed if elapsed > 0 else 0
            logger.info(f"  Progress: {total_exported} services exported ({rate:.0f}/s)")

        if len(services) < batch_limit:
            break

    # Save to file
    with open(export_file, 'w') as f:
        json.dump(all_services, f)

    file_size_mb = os.path.getsize(export_file) / 1024 / 1024
    elapsed = time.time() - start_time
    logger.info(f"Exported {total_exported} services to {export_file} ({file_size_mb:.1f} MB) in {elapsed:.1f}s")

    # Print stats
    status_names = {0: 'Prepared', 1: 'Active', 2: 'Suspended', 3: 'Prepared blocked',
                    4: 'Ended', 5: 'Quoted', 6: 'Obsolete', 7: 'Deferred', 8: 'Suspended (going to end)'}

    status_counts = Counter(s.get('status', -1) for s in all_services)
    logger.info("\nService status distribution:")
    for status, count in sorted(status_counts.items()):
        logger.info(f"  {status_names.get(status, f'Unknown({status})')}: {count}")

    plan_counts = Counter(s.get('servicePlanId', -1) for s in all_services)
    logger.info(f"\nServices by plan (top 10 of {len(plan_counts)}):")
    for plan_id, count in plan_counts.most_common(10):
        plan_name = next((s.get('servicePlanName', s.get('name', '?'))
                         for s in all_services if s.get('servicePlanId') == plan_id), '?')
        logger.info(f"  Plan {plan_id} ({plan_name}): {count}")

    # Check for PPPoE-related attributes
    services_with_attrs = sum(1 for s in all_services if s.get('attributes'))
    logger.info(f"\nServices with custom attributes: {services_with_attrs}/{total_exported}")

    return all_services


def main():
    parser = argparse.ArgumentParser(
        description='Export services and service plans from old UISP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--test', action='store_true',
                        help='Export only 10 services')
    parser.add_argument('--limit', type=int, default=None,
                        help='Export only N services')
    parser.add_argument('--offset', type=int, default=0,
                        help='Start from service offset N (for resuming)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show each service record')
    parser.add_argument('--skip-plans', action='store_true',
                        help='Skip service plans export')

    args = parser.parse_args()

    # Load config
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import config
    except ImportError:
        logger.error("config.py not found. Ensure it exists in the scripts directory.")
        sys.exit(1)

    old_url = getattr(config, 'OLD_UISP_BASE_URL', None)
    old_token = getattr(config, 'OLD_UISP_API_KEY', None)
    if not old_url or not old_token:
        logger.error("OLD_UISP_BASE_URL and OLD_UISP_API_KEY must be set in config.py")
        sys.exit(1)

    # Connect
    api = UISPApi(old_url, old_token, verify_ssl=False)
    if not api.test_connection():
        logger.error("Cannot connect to old UISP. Check credentials.")
        sys.exit(1)

    limit = args.limit
    if args.test:
        limit = 10

    # Export service plans
    if not args.skip_plans:
        export_service_plans(api)

    # Export services
    export_services(api, limit=limit, offset=args.offset, verbose=args.verbose)

    logger.info(f"\nLog file: {log_file}")
    logger.info("Done!")


if __name__ == '__main__':
    main()
