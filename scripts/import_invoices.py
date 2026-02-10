#!/usr/bin/env python3
"""
UISP Invoice Import Script

Imports invoices from old McBroad UISP into new on-premise UISP via CRM API.
For paid invoices, creates linked payments so invoice status reflects correctly.

Usage:
    1. Ensure config.py has both OLD and NEW UISP credentials
    2. pip install -r requirements.txt
    3. python import_invoices.py --test          # Test with 10 invoices
    4. python import_invoices.py --verbose        # Full import

Options:
    --test          Import only 10 invoices
    --limit N       Import only N invoices
    --offset N      Start from invoice offset N (for resuming)
    --dry-run       Export invoices from old UISP without importing
    --export-only   Just export all invoices to JSON file, don't import
    --import-from FILE  Import from previously exported JSON file
    --verbose       Show detailed progress
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
log_file = f'import_invoices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(__name__)

# Default payment method for imported payments
# Using "Cash" because "Custom" requires providerName/providerPaymentId fields
DEFAULT_PAYMENT_METHOD_ID = "6efe0fa8-36b2-4dd1-b049-427bffc7d369"  # Cash


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

    def post(self, endpoint, data):
        return self._request('POST', endpoint, data)

    def delete(self, endpoint):
        return self._request('DELETE', endpoint)

    def test_connection(self):
        try:
            # Try /organizations first, fall back to /clients?limit=1
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


def export_invoices(old_api, export_file='invoices_export.json', limit=None, offset=0):
    """Export all invoices from old UISP to a JSON file"""
    logger.info("=== Exporting invoices from old UISP ===")

    all_invoices = []
    page_size = 500
    current_offset = offset
    total_exported = 0

    while True:
        if limit and total_exported >= limit:
            break

        batch_limit = min(page_size, limit - total_exported) if limit else page_size

        logger.info(f"Fetching invoices offset={current_offset}, limit={batch_limit}...")
        try:
            invoices = old_api.get(f'/invoices?limit={batch_limit}&offset={current_offset}')
        except Exception as e:
            logger.error(f"Failed to fetch at offset {current_offset}: {e}")
            logger.info(f"Saved {total_exported} invoices so far. You can resume with --offset {current_offset}")
            break

        if not invoices:
            break

        all_invoices.extend(invoices)
        total_exported += len(invoices)
        current_offset += len(invoices)

        if total_exported % 5000 == 0:
            logger.info(f"  Exported {total_exported} invoices so far...")

        if len(invoices) < batch_limit:
            break

    # Save to file
    with open(export_file, 'w') as f:
        json.dump(all_invoices, f)

    file_size_mb = os.path.getsize(export_file) / 1024 / 1024
    logger.info(f"Exported {total_exported} invoices to {export_file} ({file_size_mb:.1f} MB)")

    # Print stats
    statuses = {}
    for inv in all_invoices:
        s = inv.get('status', -1)
        statuses[s] = statuses.get(s, 0) + 1

    status_names = {0: 'Draft', 1: 'Unpaid', 2: 'Partial', 3: 'Paid', 4: 'Void'}
    logger.info("Status distribution:")
    for s, count in sorted(statuses.items()):
        logger.info(f"  {status_names.get(s, f'Unknown({s})')}: {count}")

    return all_invoices


def build_client_mapping(new_api):
    """Build mapping from original client ID to new UISP client ID"""
    logger.info("=== Building client ID mapping from new UISP ===")

    mapping = {}  # {original_client_id_str: new_client_id_int}
    offset = 0
    page_size = 10000

    while True:
        clients = new_api.get(f'/clients?limit={page_size}&offset={offset}')
        if not clients:
            break

        for c in clients:
            user_ident = c.get('userIdent')
            if user_ident:
                mapping[str(user_ident)] = c['id']

        offset += len(clients)
        if len(clients) < page_size:
            break

    logger.info(f"Built mapping for {len(mapping)} clients (userIdent → new ID)")
    return mapping


def build_service_mapping(new_api):
    """Build mapping from new client ID to service ID(s)"""
    logger.info("=== Building service mapping from new UISP ===")

    mapping = {}  # {new_client_id: [service_ids]}
    offset = 0
    page_size = 10000

    while True:
        services = new_api.get(f'/clients/services?limit={page_size}&offset={offset}')
        if not services:
            break

        for s in services:
            client_id = s.get('clientId')
            if client_id:
                if client_id not in mapping:
                    mapping[client_id] = []
                mapping[client_id].append(s['id'])

        offset += len(services)
        if len(services) < page_size:
            break

    logger.info(f"Built service mapping for {len(mapping)} clients")
    return mapping


def import_invoices(new_api, invoices, client_mapping, resume_from=0, verbose=False):
    """Import invoices into new UISP with linked payments for paid ones"""
    logger.info("=== Importing invoices into new UISP ===")

    stats = {
        'invoices_created': 0,
        'invoices_failed': 0,
        'invoices_skipped_no_client': 0,
        'payments_created': 0,
        'payments_failed': 0,
        'void_skipped': 0,
    }
    failed = []

    total = len(invoices)
    start_time = time.time()

    for i, inv in enumerate(invoices):
        if i < resume_from:
            continue

        old_client_id = str(inv.get('clientId', ''))
        inv_number = inv.get('number', '?')
        inv_id = inv.get('id', '?')

        # Skip void invoices
        if inv.get('status') == 4:
            stats['void_skipped'] += 1
            continue

        # Look up new client ID
        new_client_id = client_mapping.get(old_client_id)
        if not new_client_id:
            stats['invoices_skipped_no_client'] += 1
            if verbose:
                logger.warning(f"  [{i+1}/{total}] Skipped invoice {inv_number} - client {old_client_id} not found")
            continue

        # Build invoice payload
        items = []
        for item in inv.get('items', []):
            item_payload = {
                'label': item.get('label', 'Imported item'),
                'price': item.get('price', 0),
                'quantity': item.get('quantity', 1),
            }
            if item.get('unit'):
                item_payload['unit'] = item['unit']
            items.append(item_payload)

        if not items:
            stats['invoices_failed'] += 1
            failed.append({
                'old_id': inv_id, 'number': inv_number,
                'error': 'No items'
            })
            continue

        invoice_payload = {
            'number': str(inv_number),
            'items': items,
            'createdDate': inv.get('createdDate'),
            'maturityDays': inv.get('maturityDays', 14),
            'adminNotes': f"Imported from old UISP (ID: {inv_id})",
        }

        if inv.get('notes'):
            invoice_payload['notes'] = inv['notes']

        # Create invoice
        try:
            new_inv = new_api.post(f'/clients/{new_client_id}/invoices', invoice_payload)
            new_inv_id = new_inv.get('id')
            stats['invoices_created'] += 1

            if verbose:
                logger.info(f"  [{i+1}/{total}] Invoice {inv_number} → new ID {new_inv_id}")

        except Exception as e:
            stats['invoices_failed'] += 1
            failed.append({
                'old_id': inv_id, 'number': inv_number,
                'client': old_client_id, 'error': str(e)[:200]
            })
            if verbose:
                logger.error(f"  [{i+1}/{total}] Failed invoice {inv_number}: {e}")
            time.sleep(0.05)
            continue

        # Create linked payment for paid/partially paid invoices
        if inv.get('status') in (2, 3) and inv.get('amountPaid', 0) > 0:
            amount_paid = inv['amountPaid']

            # Use the first payment cover date if available, else invoice created date
            payment_date = inv.get('createdDate')
            covers = inv.get('paymentCovers', [])
            if covers:
                # We don't have the original payment date directly,
                # but we can use the invoice's emailSentDate as an approximation
                # or just the created date
                pass

            payment_payload = {
                'clientId': new_client_id,
                'amount': amount_paid,
                'currencyCode': inv.get('currencyCode', 'PHP'),
                'methodId': DEFAULT_PAYMENT_METHOD_ID,
                'createdDate': payment_date,
                'note': f"Imported - Invoice #{inv_number}",
                'invoiceIds': [new_inv_id],
            }

            try:
                new_api.post('/payments', payment_payload)
                stats['payments_created'] += 1
            except Exception as e:
                stats['payments_failed'] += 1
                if verbose:
                    logger.error(f"    Payment failed for invoice {inv_number}: {e}")

        # Progress logging
        if (i + 1) % 500 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1 - resume_from) / elapsed if elapsed > 0 else 0
            remaining = (total - i - 1) / rate if rate > 0 else 0
            logger.info(
                f"Progress: {i+1}/{total} | "
                f"Created: {stats['invoices_created']} inv + {stats['payments_created']} pay | "
                f"Failed: {stats['invoices_failed']} | "
                f"Rate: {rate:.1f}/s | "
                f"ETA: {remaining/3600:.1f}h"
            )

        # Small delay between requests
        time.sleep(0.05)

    # Final summary
    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 60)
    logger.info("IMPORT SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Invoices created:           {stats['invoices_created']}")
    logger.info(f"Invoices failed:            {stats['invoices_failed']}")
    logger.info(f"Invoices skipped (no client): {stats['invoices_skipped_no_client']}")
    logger.info(f"Void invoices skipped:      {stats['void_skipped']}")
    logger.info(f"Payments created:           {stats['payments_created']}")
    logger.info(f"Payments failed:            {stats['payments_failed']}")
    logger.info(f"Total time:                 {elapsed/3600:.1f} hours")
    logger.info("=" * 60)

    # Save failed invoices
    if failed:
        failed_file = f'failed_invoices_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(failed_file, 'w') as f:
            json.dump(failed, f, indent=2)
        logger.info(f"Failed invoices saved to: {failed_file}")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Import invoices from old UISP to new UISP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--test', action='store_true',
                        help='Import only 10 invoices')
    parser.add_argument('--limit', type=int, default=None,
                        help='Import only N invoices')
    parser.add_argument('--offset', type=int, default=0,
                        help='Start from invoice offset N (for resuming export)')
    parser.add_argument('--resume-from', type=int, default=0,
                        help='Resume import from invoice index N (skip first N)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Export and show stats without importing')
    parser.add_argument('--export-only', action='store_true',
                        help='Just export invoices to JSON file')
    parser.add_argument('--import-from', type=str, default=None,
                        help='Import from previously exported JSON file')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed progress')

    args = parser.parse_args()

    # Load config
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import config
    except ImportError:
        logger.error("config.py not found. Ensure it exists in the scripts directory.")
        sys.exit(1)

    # Check required config
    old_url = getattr(config, 'OLD_UISP_BASE_URL', None)
    old_token = getattr(config, 'OLD_UISP_API_KEY', None)
    if not old_url or not old_token:
        logger.error("OLD_UISP_BASE_URL and OLD_UISP_API_KEY must be set in config.py")
        sys.exit(1)

    limit = args.limit
    if args.test:
        limit = 10

    # Step 1: Get invoices (from export or API)
    if args.import_from:
        logger.info(f"Loading invoices from {args.import_from}...")
        with open(args.import_from, 'r') as f:
            invoices = json.load(f)
        logger.info(f"Loaded {len(invoices)} invoices from file")
        if limit:
            invoices = invoices[:limit]
    else:
        # Connect to old UISP
        old_api = UISPApi(old_url, old_token, verify_ssl=False)
        if not old_api.test_connection():
            logger.error("Cannot connect to old UISP. Check OLD_UISP_BASE_URL and OLD_UISP_API_KEY.")
            sys.exit(1)

        # Export invoices
        export_file = 'invoices_export.json'
        invoices = export_invoices(old_api, export_file, limit=limit, offset=args.offset)

        if args.export_only:
            logger.info("Export complete. Use --import-from to import later.")
            sys.exit(0)

    if args.dry_run:
        logger.info(f"\nDRY RUN: Would import {len(invoices)} invoices")
        paid = sum(1 for inv in invoices if inv.get('status') == 3)
        unpaid = sum(1 for inv in invoices if inv.get('status') == 1)
        partial = sum(1 for inv in invoices if inv.get('status') == 2)
        void = sum(1 for inv in invoices if inv.get('status') == 4)
        logger.info(f"  Paid: {paid}, Unpaid: {unpaid}, Partial: {partial}, Void (skip): {void}")
        total_amount = sum(inv.get('total', 0) for inv in invoices)
        logger.info(f"  Total amount: ₱{total_amount:,.2f}")
        sys.exit(0)

    # Step 2: Connect to new UISP
    new_api = UISPApi(
        config.UISP_BASE_URL,
        config.UISP_API_TOKEN,
        verify_ssl=getattr(config, 'VERIFY_SSL', False)
    )
    if not new_api.test_connection():
        logger.error("Cannot connect to new UISP.")
        sys.exit(1)

    # Step 3: Build client ID mapping
    client_mapping = build_client_mapping(new_api)
    if not client_mapping:
        logger.error("No client mapping found. Run client import first.")
        sys.exit(1)

    # Step 4: Import invoices
    logger.info(f"\nStarting import of {len(invoices)} invoices...")
    logger.info(f"Log file: {log_file}")
    import_invoices(new_api, invoices, client_mapping,
                    resume_from=args.resume_from, verbose=args.verbose)


if __name__ == '__main__':
    main()
