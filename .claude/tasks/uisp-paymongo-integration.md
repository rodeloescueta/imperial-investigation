# UISP PayMongo Payment Gateway Integration

## Status: IMPLEMENTED (v1.0.0)
## Priority: CRITICAL
## Created: 2026-02-11

---

## 1. Background & Business Impact

### Why This Is Critical

PayMongo was the **#1 payment method** for Imperial Networks, accounting for **44.2% of all payments** (26,098 out of 59,041 total) over the 10-month period from March 2025 to February 2026. Digital/online methods combined (PayMongo + ecPay + GCASH/MAYA) represented **65% of all payments**.

| Payment Method | Count | Percentage |
|----------------|-------|------------|
| **PayMongo Payment Gateway** | **26,098** | **44.2%** |
| Cash | 19,076 | 32.3% |
| ecPay | 10,706 | 18.1% |
| GCASH/MAYA | 1,575 | 2.7% |
| Bank transfer | 283 | 0.5% |
| Other | 1,303 | 2.2% |

### What Happened

McBroad IT Solutions (the previous managed service provider) **deleted all custom plugins on February 4, 2026**, before the agreed handoff deadline of February 15. The PayMongo plugin was proprietary (never shared with Imperial Networks) and **no source code was recovered**. McBroad stated plugins are "intellectual property" and refused to provide them.

### Impact

Without a PayMongo integration, Imperial Networks **cannot collect online payments** from nearly half of its ~9,871 customer base. Rebuilding this integration is the highest-priority revenue-recovery task.

---

## 2. PayMongo API Integration

### Overview

PayMongo is a Philippine payment gateway supporting GCash, Maya, GrabPay, credit/debit cards, online banking, and QR code payments. The integration uses the **Checkout Sessions API** to create hosted payment pages.

### API Basics

- **Base URL:** `https://api.paymongo.com/v1/`
- **Authentication:** HTTP Basic Auth — Secret Key as username, empty password
  - Format: `-u sk_live_YOUR_SECRET_KEY:` (trailing colon, no password)
  - Test mode: Use `sk_test_` prefixed keys
- **Content-Type:** `application/json`
- **Currency:** PHP (Philippine Peso), amounts in **centavos** (e.g., 79900 = PHP 799.00)

### Checkout Sessions API

**Create a Checkout Session:**

```
POST https://api.paymongo.com/v1/checkout_sessions
```

**Request Body:**

```json
{
  "data": {
    "attributes": {
      "line_items": [
        {
          "name": "Invoice #INV-2026-00001",
          "amount": 79900,
          "currency": "PHP",
          "quantity": 1,
          "description": "Imperial Networks - Internet Service"
        }
      ],
      "payment_method_types": ["card", "gcash", "paymaya", "grab_pay"],
      "success_url": "https://<uisp-host>/crm/_plugins/paymongo-gateway/public.php?action=success&invoice_id=123",
      "cancel_url": "https://<uisp-host>/crm/_plugins/paymongo-gateway/public.php?action=cancel&invoice_id=123",
      "send_email_receipt": true,
      "show_description": true,
      "show_line_items": true,
      "description": "Payment for Invoice #INV-2026-00001",
      "billing": {
        "name": "Customer Name",
        "email": "customer@example.com",
        "phone": "+639171234567"
      },
      "metadata": {
        "invoice_id": "123",
        "client_id": "456",
        "uisp_instance": "imperial-networks"
      }
    }
  }
}
```

**Response:**

```json
{
  "data": {
    "id": "cs_xxxxxxxxxxxxxxxxxxxxxxxx",
    "type": "checkout_session",
    "attributes": {
      "checkout_url": "https://checkout.paymongo.com/cs_xxxxxxxx",
      "line_items": [...],
      "payment_method_types": ["card", "gcash", "paymaya", "grab_pay"],
      "status": "pending",
      "payment_intent_id": "pi_xxxxxxxxxxxxxxxxxxxxxxxx",
      "success_url": "...",
      "cancel_url": "..."
    }
  }
}
```

The `checkout_url` is what the customer is redirected to. PayMongo hosts the entire payment page.

### Retrieve a Checkout Session

```
GET https://api.paymongo.com/v1/checkout_sessions/{id}
```

Use this to verify payment status after receiving a webhook or success redirect.

### Supported Payment Methods

| Method | API Value | Description |
|--------|-----------|-------------|
| Credit/Debit Cards | `card` | Visa, Mastercard |
| GCash | `gcash` | Most popular Philippine e-wallet |
| Maya | `paymaya` | Formerly PayMaya e-wallet |
| GrabPay | `grab_pay` | GrabPay e-wallet |
| Direct Online Banking | `dob` | Bank-specific |
| Buy Now Pay Later | `billease` | Installment options |

### PayMongo Webhooks

PayMongo sends POST requests to a configured webhook URL when events occur.

**Key Events:**
- `checkout_session.payment.paid` — Payment completed successfully
- `payment.paid` — Generic payment success
- `payment.failed` — Payment failed

**Webhook Payload Structure:**

```json
{
  "data": {
    "id": "evt_xxxxxxxx",
    "type": "event",
    "attributes": {
      "type": "checkout_session.payment.paid",
      "data": {
        "id": "cs_xxxxxxxx",
        "type": "checkout_session",
        "attributes": {
          "payment_intent": {
            "id": "pi_xxxxxxxx",
            "attributes": {
              "amount": 79900,
              "status": "succeeded",
              "metadata": {
                "invoice_id": "123",
                "client_id": "456"
              }
            }
          },
          "payments": [
            {
              "id": "pay_xxxxxxxx",
              "attributes": {
                "amount": 79900,
                "status": "paid",
                "source": {
                  "type": "gcash"
                }
              }
            }
          ]
        }
      }
    }
  }
}
```

**Webhook Verification:**
- PayMongo signs webhooks with `Paymongo-Signature` header
- Verify using the webhook secret key to prevent spoofing

---

## 3. UISP/UCRM Plugin Architecture

### Plugin Directory Structure

Plugins live at: `/home/unms/data/ucrm/ucrm/data/plugins/<plugin-name>/`

```
paymongo-gateway/
├── manifest.json          # Plugin metadata & configuration (REQUIRED)
├── main.php               # Main execution script (REQUIRED)
├── public.php             # Public-facing endpoint (REQUIRED for payment gateway)
├── hook_install.php       # Post-installation hook
├── hook_configure.php     # Configuration change hook
├── hook_enable.php        # Activation hook
├── public/
│   └── client-zone.js     # Auto-loaded in client portal (Pay button)
├── src/
│   ├── PayMongoClient.php # PayMongo API wrapper
│   ├── UispClient.php     # UISP CRM API wrapper
│   └── WebhookHandler.php # Webhook processing logic
└── data/                  # Protected during updates
    ├── config.json        # Auto-generated from manifest configuration
    └── plugin.log         # Log file (visible in UISP admin)
```

### manifest.json Structure

```json
{
  "version": "1",
  "information": {
    "name": "paymongo-gateway",
    "displayName": "PayMongo Payment Gateway",
    "description": "Accept payments via PayMongo (GCash, Maya, GrabPay, Credit Cards) for UISP invoices",
    "url": "https://github.com/imperial-networks/uisp-paymongo-gateway",
    "version": "1.0.0",
    "ucrmVersionCompliancy": {
      "min": "2.14.0",
      "max": null
    },
    "unmsVersionCompliancy": {
      "min": "1.0.0",
      "max": null
    },
    "author": "Imperial Networks"
  },
  "configuration": [
    {
      "key": "paymongoSecretKey",
      "label": "PayMongo Secret Key",
      "description": "Your PayMongo secret API key (starts with sk_live_ or sk_test_)",
      "required": 1,
      "type": "text"
    },
    {
      "key": "paymongoPublicKey",
      "label": "PayMongo Public Key",
      "description": "Your PayMongo public API key (starts with pk_live_ or pk_test_)",
      "required": 1,
      "type": "text"
    },
    {
      "key": "paymongoWebhookSecret",
      "label": "PayMongo Webhook Secret Key",
      "description": "Webhook signing secret from PayMongo dashboard",
      "required": 1,
      "type": "text"
    },
    {
      "key": "paymentMethodTypes",
      "label": "Payment Methods",
      "description": "Comma-separated: card,gcash,paymaya,grab_pay",
      "required": 1,
      "type": "text"
    },
    {
      "key": "paymentMethodId",
      "label": "UISP Payment Method UUID",
      "description": "UUID of the payment method in UISP for recording payments (use Custom method)",
      "required": 1,
      "type": "text"
    }
  ],
  "menu": [
    {
      "type": "admin",
      "target": "iframe",
      "key": "Billing",
      "label": "PayMongo Gateway"
    }
  ],
  "paymentButton": {
    "label": "PayMongo",
    "urlParameters": {
      "organizationId": "organizationId",
      "invoiceId": "invoiceId",
      "clientId": "clientId",
      "amount": "amount",
      "invoiceNumber": "invoiceNumber",
      "clientFirstName": "clientFirstName",
      "clientLastName": "clientLastName",
      "clientEmail": "email",
      "_token": "_token"
    }
  },
  "supportsWebhookEvents": true
}
```

### Key Plugin Concepts

**`paymentButton`** — When configured, UISP automatically adds a "Pay with PayMongo" button on unpaid invoices in the client zone. Clicking it redirects to `public.php` with the URL parameters specified. The `_token` parameter is always included for CSRF protection.

**`public.php`** — Accessible without authentication at:
```
https://<uisp-host>/crm/_plugins/paymongo-gateway/public.php
```
This is the entry point for both the payment button redirect and PayMongo webhook callbacks.

**`supportsWebhookEvents: true`** — Enables the "Add webhook" button in UISP plugin management, allowing UISP events (invoice created, payment received, etc.) to be forwarded to the plugin.

### Auto-Generated Files

**`data/config.json`** — Auto-populated from admin configuration:
```json
{
  "paymongoSecretKey": "sk_live_xxxxx",
  "paymongoPublicKey": "pk_live_xxxxx",
  "paymongoWebhookSecret": "whsec_xxxxx",
  "paymentMethodTypes": "card,gcash,paymaya,grab_pay",
  "paymentMethodId": "d8c1eae9-d41d-479f-aeaf-38497975d7b3"
}
```

**`ucrm.json`** — Auto-generated system configuration:
```json
{
  "ucrmPublicUrl": "https://uisp.imperial-networks.com/crm",
  "ucrmLocalUrl": "http://localhost/crm",
  "pluginPublicUrl": "https://uisp.imperial-networks.com/crm/_plugins/paymongo-gateway/public.php",
  "pluginAppKey": "auto-generated-api-key",
  "pluginId": "paymongo-gateway"
}
```

---

## 4. Implementation Plan

### Phase 1: Core Plugin Structure

**Step 1.1 — Create manifest.json**
- Define plugin metadata, configuration fields, payment button, and webhook support
- Configuration fields: PayMongo API keys, webhook secret, payment method types, UISP payment method UUID

**Step 1.2 — Create public.php (Payment Entry Point)**

This file handles three actions:
1. **Payment initiation** — When customer clicks "Pay with PayMongo" button
2. **Success redirect** — When PayMongo redirects back after payment
3. **Webhook callback** — When PayMongo sends payment confirmation

```php
<?php
// public.php — Entry point for all payment interactions

require_once __DIR__ . '/src/PayMongoClient.php';
require_once __DIR__ . '/src/UispClient.php';
require_once __DIR__ . '/src/WebhookHandler.php';

// Load configuration
$config = json_decode(file_get_contents(__DIR__ . '/data/config.json'), true);
$ucrm = json_decode(file_get_contents(__DIR__ . '/ucrm.json'), true);

$action = $_GET['action'] ?? 'pay';

switch ($action) {
    case 'pay':
        // Customer clicked "Pay with PayMongo" — create checkout session
        handlePaymentInitiation($config, $ucrm);
        break;

    case 'success':
        // PayMongo redirected back after payment
        handlePaymentSuccess($config, $ucrm);
        break;

    case 'cancel':
        // Customer cancelled payment
        handlePaymentCancel($ucrm);
        break;

    case 'webhook':
        // PayMongo webhook callback
        handleWebhook($config, $ucrm);
        break;

    default:
        http_response_code(400);
        echo 'Invalid action';
}
```

**Step 1.3 — Create PayMongoClient.php**

```php
<?php
// src/PayMongoClient.php — PayMongo API wrapper

class PayMongoClient
{
    private string $secretKey;
    private string $baseUrl = 'https://api.paymongo.com/v1';

    public function __construct(string $secretKey)
    {
        $this->secretKey = $secretKey;
    }

    public function createCheckoutSession(array $params): array
    {
        return $this->request('POST', '/checkout_sessions', [
            'data' => [
                'attributes' => $params
            ]
        ]);
    }

    public function retrieveCheckoutSession(string $id): array
    {
        return $this->request('GET', "/checkout_sessions/{$id}");
    }

    public function verifyWebhookSignature(string $payload, string $signature, string $webhookSecret): bool
    {
        // PayMongo webhook signature verification
        $parts = explode(',', $signature);
        $timestamp = null;
        $testSignature = null;
        $liveSignature = null;

        foreach ($parts as $part) {
            [$key, $value] = explode('=', $part, 2);
            if ($key === 't') $timestamp = $value;
            if ($key === 'te') $testSignature = $value;
            if ($key === 'li') $liveSignature = $value;
        }

        $sig = $liveSignature ?? $testSignature;
        if (!$timestamp || !$sig) return false;

        $expectedSig = hash_hmac('sha256', "{$timestamp}.{$payload}", $webhookSecret);
        return hash_equals($expectedSig, $sig);
    }

    private function request(string $method, string $endpoint, ?array $data = null): array
    {
        $ch = curl_init($this->baseUrl . $endpoint);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_USERPWD => $this->secretKey . ':',
            CURLOPT_HTTPHEADER => ['Content-Type: application/json', 'Accept: application/json'],
        ]);

        if ($method === 'POST') {
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode >= 400) {
            throw new RuntimeException("PayMongo API error (HTTP {$httpCode}): {$response}");
        }

        return json_decode($response, true);
    }
}
```

**Step 1.4 — Create UispClient.php**

```php
<?php
// src/UispClient.php — UISP CRM API wrapper

class UispClient
{
    private string $baseUrl;
    private string $appKey;

    public function __construct(string $baseUrl, string $appKey)
    {
        // Use local URL for server-to-server calls
        $this->baseUrl = rtrim($baseUrl, '/') . '/api/v1.0';
        $this->appKey = $appKey;
    }

    public function getInvoice(int $invoiceId): array
    {
        return $this->request('GET', "/invoices/{$invoiceId}");
    }

    public function getClient(int $clientId): array
    {
        return $this->request('GET', "/clients/{$clientId}");
    }

    public function createPayment(array $payment): array
    {
        // POST /crm/api/v1.0/payments
        return $this->request('POST', '/payments', $payment);
    }

    private function request(string $method, string $endpoint, ?array $data = null): array
    {
        $ch = curl_init($this->baseUrl . $endpoint);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_SSL_VERIFYPEER => false, // Local/self-signed cert
            CURLOPT_HTTPHEADER => [
                'Content-Type: application/json',
                'X-Auth-App-Key: ' . $this->appKey,
            ],
        ]);

        if ($method === 'POST') {
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode >= 400) {
            throw new RuntimeException("UISP API error (HTTP {$httpCode}): {$response}");
        }

        return json_decode($response, true);
    }
}
```

### Phase 2: Payment Flow Implementation

**Step 2.1 — Payment Initiation (Customer clicks "Pay with PayMongo")**

When the customer clicks the pay button, UISP redirects to `public.php` with these URL parameters:
- `invoiceId` — UISP invoice ID
- `clientId` — UISP client ID
- `amount` — Invoice amount
- `invoiceNumber` — Human-readable invoice number
- `clientFirstName`, `clientLastName`, `clientEmail`
- `_token` — CSRF token

The plugin then:
1. Validates the request parameters
2. Creates a PayMongo Checkout Session with the invoice details
3. Stores the checkout session ID mapped to the invoice ID (in a local JSON file or SQLite)
4. Redirects the customer to PayMongo's `checkout_url`

**Step 2.2 — Webhook Processing (PayMongo confirms payment)**

When PayMongo sends a `checkout_session.payment.paid` webhook:
1. Verify the webhook signature using the webhook secret
2. Extract the checkout session ID and payment details from the payload
3. Look up the corresponding UISP invoice ID from metadata
4. Create a payment in UISP CRM API:

```php
$uisp->createPayment([
    'clientId' => (int) $metadata['client_id'],
    'amount' => $paymentAmount / 100, // Convert centavos to PHP
    'methodId' => $config['paymentMethodId'], // Custom method UUID
    'createdDate' => date('c'), // ISO 8601
    'currencyCode' => 'PHP',
    'note' => "PayMongo - {$paymentMethod}", // e.g., "PayMongo - gcash"
    'providerName' => 'PayMongo',
    'providerPaymentId' => $paymongoPaymentId, // pay_xxxxxxxx
    'invoiceId' => (int) $metadata['invoice_id'],
]);
```

**Step 2.3 — Success/Cancel Redirects**

- **Success:** Display a confirmation page showing the payment was received, with a link back to the client zone
- **Cancel:** Display a message that the payment was cancelled, with a retry link

### Phase 3: Client Zone Integration

**Step 3.1 — Payment Button**

The `paymentButton` in manifest.json automatically adds "Pay with PayMongo" to unpaid invoices. No additional JavaScript needed for the basic button.

**Step 3.2 — Optional: client-zone.js**

For enhanced UX, a `public/client-zone.js` can:
- Add PayMongo branding/icons next to the payment button
- Show supported payment methods (GCash, Maya, etc.) as icons
- Display payment status updates

### Phase 4: Admin Interface

**Step 4.1 — main.php (Admin Dashboard)**

- Show recent PayMongo transactions and their status
- Display webhook event log
- Show configuration status and API connectivity test
- List pending/failed payments for manual review

---

## 5. Configuration Requirements

### PayMongo Dashboard Setup

1. **Create a PayMongo account** at https://dashboard.paymongo.com
2. **Get API keys** from Settings > API Keys:
   - Secret key: `sk_live_xxxxxxxx` (server-side)
   - Public key: `pk_live_xxxxxxxx` (client-side, for JS SDK if used)
3. **Create a webhook** in Settings > Webhooks:
   - URL: `https://<uisp-host>/crm/_plugins/paymongo-gateway/public.php?action=webhook`
   - Events: `checkout_session.payment.paid`, `payment.failed`
   - Copy the webhook secret key: `whsec_xxxxxxxx`

### UISP Plugin Configuration

After installing the plugin in UISP (System > Plugins > Add Plugin):

| Field | Value |
|-------|-------|
| PayMongo Secret Key | `sk_live_xxxxxxxx` |
| PayMongo Public Key | `pk_live_xxxxxxxx` |
| PayMongo Webhook Secret | `whsec_xxxxxxxx` |
| Payment Methods | `card,gcash,paymaya,grab_pay` |
| UISP Payment Method UUID | `d8c1eae9-d41d-479f-aeaf-38497975d7b3` (Custom) |

### UISP Payment Method Setup

Create a custom payment method in UISP (System > Billing > Payment Methods) named **"Paymongo Payment Gateway"**. Use its UUID in the plugin configuration.

Known UUIDs from the current UISP instance:
- **Custom:** `d8c1eae9-d41d-479f-aeaf-38497975d7b3`
- A dedicated "Paymongo Payment Gateway" method should be created for cleaner reporting

### UISP API Access

The plugin uses `pluginAppKey` from the auto-generated `ucrm.json` for API access. No additional API key configuration is needed for UISP — the plugin system handles this automatically.

---

## 6. UISP CRM API Reference (Relevant Endpoints)

### Create Payment
```
POST /crm/api/v1.0/payments
Header: X-Auth-App-Key: <pluginAppKey>
```
```json
{
  "clientId": 2668,
  "amount": 799.00,
  "methodId": "d8c1eae9-d41d-479f-aeaf-38497975d7b3",
  "createdDate": "2026-02-11T10:00:00+0800",
  "note": "PayMongo - gcash",
  "currencyCode": "PHP",
  "providerName": "PayMongo",
  "providerPaymentId": "pay_xxxxxxxx",
  "invoiceId": 12345
}
```

### Get Invoice
```
GET /crm/api/v1.0/invoices/{id}
```

### Get Client
```
GET /crm/api/v1.0/clients/{id}
```

### List Payment Methods
```
GET /crm/api/v1.0/payment-methods
```

### Current UISP API Base
- **Production server:** `https://uisp.imperialnetworkph.com/crm/api/v1.0`
- **Plugin local access:** Uses `ucrmLocalUrl` from `ucrm.json`

---

## 7. Testing & Verification

### Phase T1: Local Development Testing

1. **PayMongo Test Mode:**
   - Use `sk_test_` and `pk_test_` keys (from PayMongo dashboard)
   - Test payments don't charge real money
   - Test card number: `4343434343434345` (Visa, always succeeds)
   - GCash/Maya test mode: Simulated approval flow

2. **cURL Smoke Test — Create Checkout Session:**
   ```bash
   curl -X POST https://api.paymongo.com/v1/checkout_sessions \
     -u sk_test_YOUR_KEY: \
     -H "Content-Type: application/json" \
     -d '{
       "data": {
         "attributes": {
           "line_items": [{
             "name": "Test Invoice",
             "amount": 10000,
             "currency": "PHP",
             "quantity": 1
           }],
           "payment_method_types": ["card", "gcash"],
           "success_url": "https://example.com/success",
           "cancel_url": "https://example.com/cancel",
           "metadata": {
             "invoice_id": "test-001",
             "client_id": "test-001"
           }
         }
       }
     }'
   ```

3. **Verify response contains `checkout_url`** — Open it in a browser to see the PayMongo checkout page.

### Phase T2: Plugin Installation Testing

1. **Package the plugin:**
   ```bash
   cd /path/to/paymongo-gateway
   zip -r paymongo-gateway.zip . -x "*.git*" "data/*"
   ```

2. **Install in UISP:**
   - Go to System > Plugins > Add Plugin
   - Upload `paymongo-gateway.zip`
   - Configure API keys in plugin settings

3. **Verify plugin is accessible:**
   ```bash
   curl -sk "https://uisp.imperialnetworkph.com/crm/_plugins/paymongo-gateway/public.php?action=test"
   ```

4. **Check plugin logs:**
   ```bash
   cat /home/unms/data/ucrm/ucrm/data/plugins/paymongo-gateway/data/plugin.log
   ```

### Phase T3: End-to-End Payment Testing

1. **Create a test invoice** in UISP for a test client
2. **Log in as the test client** in the client zone
3. **Click "Pay with PayMongo"** on the unpaid invoice
4. **Complete payment** using PayMongo test mode
5. **Verify:**
   - PayMongo webhook is received (check plugin.log)
   - Payment is created in UISP (check invoice status)
   - Payment amount matches invoice amount
   - Payment method is recorded correctly
   - `providerName` = "PayMongo" and `providerPaymentId` is set

### Phase T4: Production Deployment

1. **Switch to live API keys** (`sk_live_`, `pk_live_`)
2. **Update webhook URL** in PayMongo dashboard to production URL
3. **Test with a real small payment** (PHP 1.00 if possible)
4. **Monitor first 10 real payments** for any issues
5. **Verify payment reconciliation** between PayMongo dashboard and UISP

### Verification Queries

```bash
# Count payments in UISP database
sudo docker exec unms-postgres psql -U postgres -d unms -c \
  "SELECT COUNT(*) FROM ucrm.payment WHERE provider_name = 'PayMongo';"

# Check recent PayMongo payments via API
curl -sk "https://uisp.imperialnetworkph.com/crm/api/v1.0/payments?limit=10" \
  -H "X-Auth-App-Key: <API_TOKEN>" | python3 -m json.tool

# Check PayMongo webhook delivery in their dashboard
# Dashboard > Developers > Webhooks > View recent events
```

---

## 8. File Inventory (To Be Created)

```
paymongo-gateway/
├── manifest.json              # Plugin manifest with paymentButton config
├── main.php                   # Admin dashboard / status page
├── public.php                 # Payment entry point + webhook handler
├── hook_install.php           # Initial setup (create data directories)
├── hook_configure.php         # Validate config on save
├── src/
│   ├── PayMongoClient.php     # PayMongo API wrapper
│   ├── UispClient.php         # UISP CRM API wrapper
│   └── WebhookHandler.php     # Webhook signature verification & processing
├── public/
│   └── client-zone.js         # Optional: Payment method icons in client zone
├── templates/
│   ├── success.html           # Payment success page
│   ├── cancel.html            # Payment cancelled page
│   └── error.html             # Error page
└── data/                      # Auto-managed by UISP
    ├── config.json            # Plugin configuration (auto-generated)
    ├── plugin.log             # Plugin log file
    └── sessions.json          # Checkout session -> invoice mapping
```

---

## 9. References

- **PayMongo Developer Docs:** https://developers.paymongo.com
- **PayMongo API Reference:** https://developers.paymongo.com/reference
- **UISP Plugin File Structure:** https://github.com/Ubiquiti-App/UCRM-plugins/blob/master/docs/file-structure.md
- **UISP Plugin Manifest:** https://github.com/Ubiquiti-App/UCRM-plugins/blob/master/docs/manifest.md
- **UISP Plugin Repository:** https://github.com/Ubiquiti-App/UCRM-plugins
- **UISP CRM API:** https://uisp.ui.com/api/crm (or local: `https://uisp.imperialnetworkph.com/crm/api-docs`)
- **Existing ROS Plugin (reference implementation):** `/home/unms/data/ucrm/ucrm/data/plugins/ros-plugin/`

---

## 10. Open Questions (Resolved)

- [x] Do we have a PayMongo account? — **Yes, API keys available**
- [ ] What PayMongo plan/pricing tier is appropriate for Imperial's volume (~2,600 payments/month)?
- [x] Should we create a dedicated "Paymongo Payment Gateway" payment method in UISP, or reuse "Custom"? — **Create dedicated method**
- [x] Do we need ecPay integration as well? — **Skip for now, PayMongo only**
- [x] What is the public-facing domain/URL? — **`uisp.imperialnetworkph.com`**
- [x] Should the plugin support partial payments? — **No, full invoice amount only**
- [x] Do we need to handle refunds through the plugin? — **No, handle manually via PayMongo dashboard**

---

## 11. Implementation Notes (2026-02-11)

### Key Corrections Applied

1. **`_token` replaces URL parameters** — The UISP `paymentButton` system automatically passes a `_token` parameter. The plugin resolves it via `GET /api/v1.0/payment-tokens/{token}` to get `invoiceId`, `clientId`, `amount`, `currency`. This is more secure than passing individual URL params. The `manifest.json` `paymentButton` only needs `"label": "PayMongo"` (no `urlParameters` needed).

2. **`invoiceIds` (array), not `invoiceId`** — The UISP `POST /payments` API uses `invoiceIds` as an array, not singular `invoiceId`.

3. **`supportsWebhookEvents` omitted** — We use PayMongo's own webhooks, not UISP event forwarding. This flag was removed from manifest.json.

4. **`send_email_receipt: false`** — UISP sends its own receipts; PayMongo email receipts disabled to prevent duplicates.

5. **`paymongoPublicKey` removed** — Not needed for server-side checkout sessions flow.

6. **Idempotency check** — `sessions.json` tracks checkout session status. Duplicate webhooks are detected and ignored.

### Architecture: Webhook-Only Payment Recording

Payment recording happens ONLY via the PayMongo webhook (`checkout_session.payment.paid`), NOT on the success redirect. This ensures payments are recorded even if the customer closes the browser before reaching the success page.

### Plugin Location

Source: `/home/imperial/projects/imperial-investigation/paymongo-gateway/`

### Files Created

| File | Purpose |
|------|---------|
| `manifest.json` | Plugin metadata, config fields, payment button definition |
| `public.php` | Core entry point: payment initiation, webhook handler, success/cancel pages |
| `main.php` | Admin dashboard: config status, session stats, webhook URL, log viewer |
| `src/Logger.php` | File logger with info/warning/error levels, LOCK_EX for concurrency |
| `src/PayMongoClient.php` | PayMongo API: create/retrieve checkout sessions, verify webhook signatures |
| `src/UispClient.php` | UISP API: resolve payment tokens, get invoices, create payments |
| `templates/success.php` | Success page shown after payment (informational only) |
| `templates/cancel.php` | Cancel page shown when customer cancels |
| `templates/error.php` | Error page for configuration or processing errors |

### Deployment Steps

1. Package: `cd paymongo-gateway && zip -r paymongo-gateway.zip manifest.json main.php public.php src/ templates/`
2. Upload ZIP via UISP admin: System > Plugins > Add Plugin
3. Configure: Enter PayMongo secret key, webhook secret, payment method UUID, payment types
4. Create webhook in PayMongo dashboard pointing to: `https://<host>/crm/_plugins/paymongo-gateway/public.php?action=webhook`
5. Test with PayMongo test mode keys and card `4343434343434345`

### Webhook URL

PayMongo webhooks should be configured to: `https://uisp.imperialnetworkph.com/crm/_plugins/paymongo-gateway/public.php?action=webhook`

Ensure DNS for `uisp.imperialnetworkph.com` resolves to the UISP server and SSL is configured.
