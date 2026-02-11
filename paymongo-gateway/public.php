<?php

declare(strict_types=1);

require_once __DIR__ . '/src/Logger.php';
require_once __DIR__ . '/src/PayMongoClient.php';
require_once __DIR__ . '/src/UispClient.php';

$logger = new Logger();

// Load configuration
$configFile = __DIR__ . '/data/config.json';
$ucrmFile = __DIR__ . '/ucrm.json';

if (!file_exists($configFile) || !file_exists($ucrmFile)) {
    $logger->error('Missing configuration files', [
        'config_exists' => file_exists($configFile),
        'ucrm_exists' => file_exists($ucrmFile),
    ]);
    showError('Plugin is not configured. Please contact the administrator.');
    exit;
}

$config = json_decode(file_get_contents($configFile), true);
$ucrm = json_decode(file_get_contents($ucrmFile), true);

// Validate required config
$requiredKeys = ['paymongoSecretKey', 'paymongoWebhookSecret', 'paymentMethodId', 'paymentMethodTypes'];
foreach ($requiredKeys as $key) {
    if (empty($config[$key])) {
        $logger->error("Missing required configuration: {$key}");
        showError('Plugin is not fully configured. Please contact the administrator.');
        exit;
    }
}

$action = $_GET['action'] ?? 'pay';

try {
    switch ($action) {
        case 'pay':
            handlePayment($config, $ucrm, $logger);
            break;
        case 'webhook':
            handleWebhook($config, $ucrm, $logger);
            break;
        case 'success':
            handleSuccess($ucrm, $logger);
            break;
        case 'cancel':
            handleCancel($ucrm, $logger);
            break;
        default:
            http_response_code(400);
            showError('Invalid action.');
    }
} catch (Throwable $e) {
    $logger->error('Unhandled exception', [
        'message' => $e->getMessage(),
        'file' => $e->getFile(),
        'line' => $e->getLine(),
    ]);
    showError('An unexpected error occurred. Please try again or contact support.');
}

// ---------------------------------------------------------------------------
// Handlers
// ---------------------------------------------------------------------------

/**
 * Handle payment initiation.
 *
 * Customer clicks "Pay with PayMongo" -> UISP redirects here with _token.
 * We resolve the token, create a PayMongo checkout session, and redirect.
 */
function handlePayment(array $config, array $ucrm, Logger $logger): void
{
    $token = $_GET['_token'] ?? '';
    if ($token === '') {
        $logger->warning('Payment request missing _token');
        showError('Invalid payment request. Please try again from your invoice.');
        return;
    }

    $logger->info('Payment initiated', ['token' => substr($token, 0, 8) . '...']);

    // Resolve token via UISP API
    $uispClient = new UispClient($ucrm['ucrmLocalUrl'] ?? '', $ucrm['pluginAppKey'] ?? '');

    try {
        $tokenData = $uispClient->resolvePaymentToken($token);
    } catch (RuntimeException $e) {
        $logger->error('Failed to resolve payment token', ['error' => $e->getMessage()]);
        showError('Invalid or expired payment link. Please try again from your invoice.');
        return;
    }

    $invoiceId = $tokenData['invoiceId'] ?? null;
    $clientId = $tokenData['clientId'] ?? null;
    $amount = $tokenData['amount'] ?? null;
    $currency = $tokenData['currency'] ?? 'PHP';

    if (!$invoiceId || !$clientId || !$amount) {
        $logger->error('Token data missing required fields', ['tokenData' => $tokenData]);
        showError('Invalid payment data. Please try again from your invoice.');
        return;
    }

    // Get invoice details for description
    $invoiceNumber = '';
    try {
        $invoice = $uispClient->getInvoice((int)$invoiceId);
        $invoiceNumber = $invoice['number'] ?? "INV-{$invoiceId}";
    } catch (RuntimeException $e) {
        $logger->warning('Could not fetch invoice details', ['invoiceId' => $invoiceId, 'error' => $e->getMessage()]);
        $invoiceNumber = "INV-{$invoiceId}";
    }

    // Convert amount to centavos (PayMongo uses integer centavos)
    $amountCentavos = (int)round((float)$amount * 100);

    if ($amountCentavos < 100) {
        $logger->warning('Amount too small', ['amount' => $amount, 'centavos' => $amountCentavos]);
        showError('Payment amount is too small.');
        return;
    }

    // Build URLs
    $pluginPublicUrl = $ucrm['pluginPublicUrl'] ?? '';
    $successUrl = $pluginPublicUrl . '?action=success&invoice_id=' . urlencode((string)$invoiceId);
    $cancelUrl = $pluginPublicUrl . '?action=cancel&invoice_id=' . urlencode((string)$invoiceId);

    // Payment method types from config
    $paymentMethods = array_map('trim', explode(',', $config['paymentMethodTypes']));

    $description = "Invoice #{$invoiceNumber} - Imperial Networks";

    $paymongo = new PayMongoClient($config['paymongoSecretKey']);

    try {
        $session = $paymongo->createCheckoutSession(
            $amountCentavos,
            $description,
            $paymentMethods,
            $successUrl,
            $cancelUrl,
            [
                'invoice_id' => (string)$invoiceId,
                'client_id' => (string)$clientId,
                'amount' => (string)$amount,
                'invoice_number' => $invoiceNumber,
            ]
        );
    } catch (RuntimeException $e) {
        $logger->error('Failed to create PayMongo checkout session', [
            'invoiceId' => $invoiceId,
            'amount' => $amount,
            'error' => $e->getMessage(),
        ]);
        showError('Could not create payment session. Please try again later.');
        return;
    }

    $checkoutUrl = $session['data']['attributes']['checkout_url'] ?? null;
    $sessionId = $session['data']['id'] ?? null;

    if (!$checkoutUrl || !$sessionId) {
        $logger->error('PayMongo response missing checkout_url or session ID', ['response' => $session]);
        showError('Payment service returned an invalid response. Please try again.');
        return;
    }

    // Save session mapping for idempotency and tracking
    saveSession($sessionId, [
        'invoice_id' => $invoiceId,
        'client_id' => $clientId,
        'amount' => $amount,
        'amount_centavos' => $amountCentavos,
        'invoice_number' => $invoiceNumber,
        'status' => 'pending',
        'created_at' => date('c'),
    ], $logger);

    $logger->info('Checkout session created, redirecting customer', [
        'sessionId' => $sessionId,
        'invoiceId' => $invoiceId,
        'amount' => $amount,
    ]);

    // Redirect customer to PayMongo checkout
    header('Location: ' . $checkoutUrl);
    exit;
}

/**
 * Handle PayMongo webhook callback.
 *
 * PayMongo POSTs here when a payment event occurs.
 * We verify the signature, extract metadata, and create the payment in UISP.
 */
function handleWebhook(array $config, array $ucrm, Logger $logger): void
{
    // Must be POST
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        http_response_code(405);
        echo json_encode(['error' => 'Method not allowed']);
        return;
    }

    $rawBody = file_get_contents('php://input');
    $signatureHeader = $_SERVER['HTTP_PAYMONGO_SIGNATURE'] ?? '';

    if ($rawBody === '' || $signatureHeader === '') {
        $logger->warning('Webhook received with empty body or signature');
        http_response_code(400);
        echo json_encode(['error' => 'Missing body or signature']);
        return;
    }

    // Verify webhook signature
    $paymongo = new PayMongoClient($config['paymongoSecretKey']);
    if (!$paymongo->verifyWebhookSignature($rawBody, $signatureHeader, $config['paymongoWebhookSecret'])) {
        $logger->warning('Webhook signature verification failed');
        http_response_code(401);
        echo json_encode(['error' => 'Invalid signature']);
        return;
    }

    $payload = json_decode($rawBody, true);
    if (!$payload) {
        $logger->error('Webhook payload is not valid JSON');
        http_response_code(400);
        echo json_encode(['error' => 'Invalid JSON']);
        return;
    }

    $eventType = $payload['data']['attributes']['type'] ?? '';
    $logger->info('Webhook received', ['eventType' => $eventType]);

    // Only process successful payment events
    if ($eventType !== 'checkout_session.payment.paid') {
        $logger->info('Ignoring non-payment webhook event', ['eventType' => $eventType]);
        http_response_code(200);
        echo json_encode(['status' => 'ignored']);
        return;
    }

    // Extract checkout session data from the webhook payload
    $checkoutSession = $payload['data']['attributes']['data'] ?? [];
    $sessionId = $checkoutSession['id'] ?? '';
    $metadata = $checkoutSession['attributes']['metadata'] ?? [];
    $payments = $checkoutSession['attributes']['payments'] ?? [];

    $invoiceId = $metadata['invoice_id'] ?? null;
    $clientId = $metadata['client_id'] ?? null;
    $invoiceNumber = $metadata['invoice_number'] ?? '';

    if (!$invoiceId || !$clientId) {
        $logger->error('Webhook missing invoice_id or client_id in metadata', ['metadata' => $metadata]);
        http_response_code(200); // Return 200 to prevent retries for bad data
        echo json_encode(['status' => 'error', 'message' => 'Missing metadata']);
        return;
    }

    // Get payment details
    $paymentAmount = 0;
    $paymentMethod = 'unknown';
    $providerPaymentId = '';

    if (!empty($payments)) {
        $payment = $payments[0];
        $paymentAmount = $payment['attributes']['amount'] ?? 0;
        $paymentMethod = $payment['attributes']['source']['type'] ?? 'unknown';
        $providerPaymentId = $payment['id'] ?? '';
    } else {
        // Fallback to payment_intent
        $paymentIntent = $checkoutSession['attributes']['payment_intent'] ?? [];
        $paymentAmount = $paymentIntent['attributes']['amount'] ?? 0;
        $providerPaymentId = $paymentIntent['id'] ?? '';
    }

    // Idempotency check: don't record the same payment twice
    $sessionData = loadSession($sessionId, $logger);
    if ($sessionData && ($sessionData['status'] ?? '') === 'completed') {
        $logger->info('Duplicate webhook for already-completed session', ['sessionId' => $sessionId]);
        http_response_code(200);
        echo json_encode(['status' => 'already_processed']);
        return;
    }

    // Convert centavos to pesos
    $amountPesos = $paymentAmount / 100;

    $logger->info('Recording payment in UISP', [
        'invoiceId' => $invoiceId,
        'clientId' => $clientId,
        'amount' => $amountPesos,
        'paymentMethod' => $paymentMethod,
        'providerPaymentId' => $providerPaymentId,
    ]);

    $uispClient = new UispClient($ucrm['ucrmLocalUrl'] ?? '', $ucrm['pluginAppKey'] ?? '');

    try {
        $uispPayment = $uispClient->createPayment([
            'clientId' => (int)$clientId,
            'amount' => $amountPesos,
            'methodId' => $config['paymentMethodId'],
            'currencyCode' => 'PHP',
            'createdDate' => date('c'),
            'note' => "PayMongo - {$paymentMethod}",
            'providerName' => 'PayMongo',
            'providerPaymentId' => $providerPaymentId,
            'invoiceIds' => [(int)$invoiceId],
        ]);
    } catch (RuntimeException $e) {
        $logger->error('Failed to create payment in UISP', [
            'invoiceId' => $invoiceId,
            'error' => $e->getMessage(),
        ]);
        http_response_code(500);
        echo json_encode(['status' => 'error', 'message' => 'Failed to record payment']);
        return;
    }

    // Mark session as completed
    updateSessionStatus($sessionId, 'completed', $logger);

    $logger->info('Payment recorded successfully', [
        'invoiceId' => $invoiceId,
        'uispPaymentId' => $uispPayment['id'] ?? 'unknown',
        'amount' => $amountPesos,
    ]);

    http_response_code(200);
    echo json_encode(['status' => 'success']);
}

/**
 * Handle success redirect from PayMongo.
 *
 * This is informational only — actual payment recording happens via webhook.
 */
function handleSuccess(array $ucrm, Logger $logger): void
{
    $invoiceId = $_GET['invoice_id'] ?? '';
    $logger->info('Customer returned to success page', ['invoiceId' => $invoiceId]);

    $clientZoneUrl = ($ucrm['ucrmPublicUrl'] ?? '') . '/client-zone';
    include __DIR__ . '/templates/success.php';
}

/**
 * Handle cancel redirect from PayMongo.
 */
function handleCancel(array $ucrm, Logger $logger): void
{
    $invoiceId = $_GET['invoice_id'] ?? '';
    $logger->info('Customer cancelled payment', ['invoiceId' => $invoiceId]);

    $clientZoneUrl = ($ucrm['ucrmPublicUrl'] ?? '') . '/client-zone';
    $retryUrl = ($ucrm['ucrmPublicUrl'] ?? '') . '/client-zone';
    include __DIR__ . '/templates/cancel.php';
}

/**
 * Show error page.
 */
function showError(string $message): void
{
    http_response_code(500);
    include __DIR__ . '/templates/error.php';
}

// ---------------------------------------------------------------------------
// Session storage (JSON file with LOCK_EX for concurrency safety)
// ---------------------------------------------------------------------------

function getSessionsFile(): string
{
    return __DIR__ . '/data/sessions.json';
}

function loadSessions(Logger $logger): array
{
    $file = getSessionsFile();
    if (!file_exists($file)) {
        return [];
    }

    $content = file_get_contents($file);
    $data = json_decode($content, true);

    return is_array($data) ? $data : [];
}

function saveSessions(array $sessions, Logger $logger): void
{
    $file = getSessionsFile();
    $dir = dirname($file);
    if (!is_dir($dir)) {
        mkdir($dir, 0755, true);
    }

    // Prune to last 1000 entries
    if (count($sessions) > 1000) {
        $sessions = array_slice($sessions, -1000, null, true);
    }

    file_put_contents($file, json_encode($sessions, JSON_PRETTY_PRINT), LOCK_EX);
}

function saveSession(string $sessionId, array $data, Logger $logger): void
{
    $sessions = loadSessions($logger);
    $sessions[$sessionId] = $data;
    saveSessions($sessions, $logger);
}

function loadSession(string $sessionId, Logger $logger): ?array
{
    $sessions = loadSessions($logger);
    return $sessions[$sessionId] ?? null;
}

function updateSessionStatus(string $sessionId, string $status, Logger $logger): void
{
    $sessions = loadSessions($logger);
    if (isset($sessions[$sessionId])) {
        $sessions[$sessionId]['status'] = $status;
        $sessions[$sessionId]['completed_at'] = date('c');
        saveSessions($sessions, $logger);
    }
}
