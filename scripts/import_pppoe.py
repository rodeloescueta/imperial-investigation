#!/usr/bin/env python3
"""
UISP PPPoE Username Import Script

Reads PPPoE usernames from old UISP (client-level attribute) and sets them
on services in the new UISP (service-level attribute) via PATCH API.

Usage:
    1. Ensure config.py has both OLD and NEW UISP credentials
    2. python3 import_pppoe.py --test          # Test with 5 services
    3. python3 import_pppoe.py --dry-run       # Show what would be updated
    4. python3 import_pppoe.py                 # Full import
    5. python3 import_pppoe.py --resume-from N # Resume from index N

Flow:
    Old UISP clients (pppoeUsername attr) → mapping via userIdent →
    New UISP services → PATCH pppoeusername (customAttributeId=2)
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
log_file = f'import_pppoe_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(__name__)

# PPPoE username custom attribute ID on new UISP (service-level)
PPPOE_ATTR_ID = 2


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

    def patch(self, endpoint, data):
        return self._request('PATCH', endpoint, data)

    def test_connection(self):
        try:
            try:
                self.get('/organizations')
            except Exception:
                self.get('/clients?limit=1')
            logger.info(f"Connected to {self.base_url}")
            return True
        except Exception as e:
            logger.error(f"Connection failed to {self.base_url}: {e}")
            return False


def fetch_all_paginated(api, endpoint, page_size=10000):
    """Fetch all records from a paginated endpoint"""
    all_records = []
    offset = 0
    while True:
        records = api.get(f'{endpoint}?limit={page_size}&offset={offset}')
        if not records:
            break
        all_records.extend(records)
        offset += len(records)
        if len(records) < page_size:
            break
    return all_records


def build_pppoe_mapping(old_api):
    """Extract PPPoE usernames from old UISP client attributes.
    Returns {old_client_id_str: pppoe_username}"""
    logger.info("=== Step 1: Fetching PPPoE usernames from old UISP ===")

    clients = fetch_all_paginated(old_api, '/clients')
    logger.info(f"Fetched {len(clients)} clients from old UISP")

    mapping = {}
    for c in clients:
        client_id = str(c.get('id', ''))
        for attr in c.get('attributes', []):
            if attr.get('customAttributeId') == 1 and attr.get('value'):
                mapping[client_id] = attr['value'].strip()
                break

    logger.info(f"Found {len(mapping)} clients with PPPoE usernames")
    return mapping


def build_client_id_mapping(new_api):
    """Map original client ID → new UISP client ID via userIdent.
    Returns {old_client_id_str: new_client_id_int}"""
    logger.info("=== Step 2: Building client ID mapping from new UISP ===")

    clients = fetch_all_paginated(new_api, '/clients')
    logger.info(f"Fetched {len(clients)} clients from new UISP")

    mapping = {}
    for c in clients:
        user_ident = c.get('userIdent')
        if user_ident:
            mapping[str(user_ident)] = c['id']

    logger.info(f"Built mapping for {len(mapping)} clients (userIdent → new ID)")
    return mapping


def build_service_mapping(new_api):
    """Map new client ID → service ID(s) on new UISP.
    Returns {new_client_id: [service_ids]}"""
    logger.info("=== Step 3: Building service mapping from new UISP ===")

    services = fetch_all_paginated(new_api, '/clients/services')
    logger.info(f"Fetched {len(services)} services from new UISP")

    mapping = {}
    for s in services:
        client_id = s.get('clientId')
        if client_id:
            if client_id not in mapping:
                mapping[client_id] = []
            mapping[client_id].append({
                'id': s['id'],
                'name': s.get('servicePlanName', s.get('name', '?')),
                'status': s.get('status'),
                'attributes': s.get('attributes', []),
            })

    logger.info(f"Built service mapping for {len(mapping)} clients")
    return mapping


def import_pppoe(new_api, pppoe_map, client_map, service_map,
                 dry_run=False, limit=None, resume_from=0, verbose=False):
    """Set PPPoE usernames on new UISP services"""
    logger.info("=== Step 4: Importing PPPoE usernames ===")
    if dry_run:
        logger.info("DRY RUN — no changes will be made")

    # Build the work list: (service_id, pppoe_username, old_client_id, service_name)
    work = []
    skipped_no_client = 0
    skipped_no_service = 0
    skipped_already_set = 0
    multi_service_clients = 0

    for old_client_id, pppoe_username in pppoe_map.items():
        new_client_id = client_map.get(old_client_id)
        if not new_client_id:
            skipped_no_client += 1
            continue

        services = service_map.get(new_client_id)
        if not services:
            skipped_no_service += 1
            continue

        if len(services) > 1:
            multi_service_clients += 1

        for svc in services:
            # Check if already set
            existing_pppoe = None
            for attr in svc.get('attributes', []):
                if attr.get('customAttributeId') == PPPOE_ATTR_ID:
                    existing_pppoe = attr.get('value')
                    break

            if existing_pppoe:
                skipped_already_set += 1
                continue

            work.append((svc['id'], pppoe_username, old_client_id, svc['name']))

    logger.info(f"\nWork summary:")
    logger.info(f"  PPPoE usernames available: {len(pppoe_map)}")
    logger.info(f"  Matched to new client: {len(pppoe_map) - skipped_no_client}")
    logger.info(f"  Skipped (no client mapping): {skipped_no_client}")
    logger.info(f"  Skipped (no service): {skipped_no_service}")
    logger.info(f"  Skipped (already set): {skipped_already_set}")
    logger.info(f"  Clients with multiple services: {multi_service_clients}")
    logger.info(f"  Services to update: {len(work)}")

    if limit:
        work = work[:limit]
        logger.info(f"  Limited to: {limit}")

    if dry_run:
        logger.info("\nDry run — first 20 updates that would be made:")
        for svc_id, pppoe, old_id, svc_name in work[:20]:
            logger.info(f"  Service {svc_id} ({svc_name}): pppoeusername = '{pppoe}' (old client {old_id})")
        logger.info(f"\nTotal: {len(work)} services would be updated")
        return {'would_update': len(work)}

    # Execute updates
    stats = {'updated': 0, 'failed': 0}
    failed = []
    start_time = time.time()

    for i, (svc_id, pppoe_username, old_client_id, svc_name) in enumerate(work):
        if i < resume_from:
            continue

        payload = {
            'attributes': [
                {'customAttributeId': PPPOE_ATTR_ID, 'value': pppoe_username}
            ]
        }

        try:
            new_api.patch(f'/clients/services/{svc_id}', payload)
            stats['updated'] += 1

            if verbose or (i + 1) % 500 == 0:
                logger.info(f"  [{i+1}/{len(work)}] Service {svc_id}: pppoeusername = '{pppoe_username}'")

        except Exception as e:
            stats['failed'] += 1
            failed.append({
                'service_id': svc_id,
                'pppoe': pppoe_username,
                'old_client_id': old_client_id,
                'error': str(e)[:200]
            })
            if verbose:
                logger.error(f"  [{i+1}/{len(work)}] Failed service {svc_id}: {e}")

        # Progress every 500
        if (i + 1) % 500 == 0:
            elapsed = time.time() - start_time
            done = i + 1 - resume_from
            rate = done / elapsed if elapsed > 0 else 0
            remaining = (len(work) - i - 1) / rate if rate > 0 else 0
            logger.info(
                f"Progress: {i+1}/{len(work)} | "
                f"Updated: {stats['updated']} | Failed: {stats['failed']} | "
                f"Rate: {rate:.1f}/s | ETA: {remaining/60:.0f}min"
            )

        time.sleep(0.05)

    # Summary
    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 60)
    logger.info("PPPOE IMPORT SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Services updated:  {stats['updated']}")
    logger.info(f"Services failed:   {stats['failed']}")
    logger.info(f"Total time:        {elapsed/60:.1f} minutes")
    logger.info("=" * 60)

    if failed:
        failed_file = f'failed_pppoe_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(failed_file, 'w') as f:
            json.dump(failed, f, indent=2)
        logger.info(f"Failed records saved to: {failed_file}")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Import PPPoE usernames from old UISP to new UISP services',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--test', action='store_true',
                        help='Update only 5 services')
    parser.add_argument('--limit', type=int, default=None,
                        help='Update only N services')
    parser.add_argument('--resume-from', type=int, default=0,
                        help='Resume from work item index N')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be updated without making changes')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Log each update')

    args = parser.parse_args()

    # Load config
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import config
    except ImportError:
        logger.error("config.py not found.")
        sys.exit(1)

    old_url = getattr(config, 'OLD_UISP_BASE_URL', None)
    old_token = getattr(config, 'OLD_UISP_API_KEY', None)
    new_url = getattr(config, 'UISP_BASE_URL', None)
    new_token = getattr(config, 'UISP_API_TOKEN', None)

    if not all([old_url, old_token, new_url, new_token]):
        logger.error("Missing config values. Need OLD_UISP_BASE_URL, OLD_UISP_API_KEY, UISP_BASE_URL, UISP_API_TOKEN")
        sys.exit(1)

    # Connect to both
    old_api = UISPApi(old_url, old_token, verify_ssl=False)
    new_api = UISPApi(new_url, new_token, verify_ssl=False)

    if not old_api.test_connection():
        logger.error("Cannot connect to old UISP.")
        sys.exit(1)
    if not new_api.test_connection():
        logger.error("Cannot connect to new UISP.")
        sys.exit(1)

    limit = args.limit
    if args.test:
        limit = 5

    # Step 1: Get PPPoE usernames from old UISP
    pppoe_map = build_pppoe_mapping(old_api)

    # Step 2: Build client ID mapping from new UISP
    client_map = build_client_id_mapping(new_api)

    # Step 3: Build service mapping from new UISP
    service_map = build_service_mapping(new_api)

    # Step 4: Import
    import_pppoe(new_api, pppoe_map, client_map, service_map,
                 dry_run=args.dry_run, limit=limit,
                 resume_from=args.resume_from, verbose=args.verbose)

    logger.info(f"\nLog file: {log_file}")


if __name__ == '__main__':
    main()
