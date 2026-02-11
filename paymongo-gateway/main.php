<?php

declare(strict_types=1);

require_once __DIR__ . '/src/Logger.php';

// Load configuration
$configFile = __DIR__ . '/data/config.json';
$ucrmFile = __DIR__ . '/ucrm.json';
$sessionsFile = __DIR__ . '/data/sessions.json';
$logFile = __DIR__ . '/data/plugin.log';

$config = file_exists($configFile) ? json_decode(file_get_contents($configFile), true) : [];
$ucrm = file_exists($ucrmFile) ? json_decode(file_get_contents($ucrmFile), true) : [];

// Config status checks
$hasSecretKey = !empty($config['paymongoSecretKey']);
$hasWebhookSecret = !empty($config['paymongoWebhookSecret']);
$hasPaymentMethodId = !empty($config['paymentMethodId']);
$hasPaymentTypes = !empty($config['paymentMethodTypes']);
$isTestMode = $hasSecretKey && str_starts_with($config['paymongoSecretKey'], 'sk_test_');

// Session stats
$sessions = [];
if (file_exists($sessionsFile)) {
    $sessions = json_decode(file_get_contents($sessionsFile), true) ?: [];
}
$totalSessions = count($sessions);
$completedSessions = count(array_filter($sessions, fn($s) => ($s['status'] ?? '') === 'completed'));
$pendingSessions = $totalSessions - $completedSessions;

// Recent sessions (last 20)
$recentSessions = array_slice(array_reverse($sessions, true), 0, 20, true);

// Webhook URL for reference
$webhookUrl = ($ucrm['pluginPublicUrl'] ?? '<not configured>') . '?action=webhook';

// Log entries (last 30 lines)
$logEntries = [];
if (file_exists($logFile)) {
    $lines = file($logFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $logEntries = array_slice($lines, -30);
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PayMongo Payment Gateway</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f6fa; color: #333; padding: 20px; }
        h1 { font-size: 1.4em; margin-bottom: 20px; color: #2c3e50; }
        h2 { font-size: 1.1em; margin-bottom: 12px; color: #34495e; }
        .card { background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .status-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
        .status-item:last-child { border-bottom: none; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; font-weight: 600; }
        .badge-ok { background: #d4edda; color: #155724; }
        .badge-warn { background: #fff3cd; color: #856404; }
        .badge-error { background: #f8d7da; color: #721c24; }
        .badge-info { background: #d1ecf1; color: #0c5460; }
        .stat { text-align: center; padding: 15px; }
        .stat .number { font-size: 2em; font-weight: 700; color: #2c3e50; }
        .stat .label { font-size: 0.85em; color: #7f8c8d; }
        .webhook-url { background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 0.85em; word-break: break-all; }
        table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #eee; }
        th { font-weight: 600; color: #7f8c8d; font-size: 0.85em; text-transform: uppercase; }
        .log-box { background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 6px; font-family: 'Fira Code', 'Consolas', monospace; font-size: 0.8em; max-height: 400px; overflow-y: auto; white-space: pre-wrap; word-wrap: break-word; line-height: 1.5; }
    </style>
</head>
<body>
    <h1>PayMongo Payment Gateway</h1>

    <div class="grid">
        <div class="card">
            <h2>Configuration Status</h2>
            <div class="status-item">
                <span>Secret Key</span>
                <span class="badge <?= $hasSecretKey ? 'badge-ok' : 'badge-error' ?>">
                    <?= $hasSecretKey ? ($isTestMode ? 'Test Mode' : 'Configured') : 'Missing' ?>
                </span>
            </div>
            <div class="status-item">
                <span>Webhook Secret</span>
                <span class="badge <?= $hasWebhookSecret ? 'badge-ok' : 'badge-error' ?>">
                    <?= $hasWebhookSecret ? 'Configured' : 'Missing' ?>
                </span>
            </div>
            <div class="status-item">
                <span>Payment Method ID</span>
                <span class="badge <?= $hasPaymentMethodId ? 'badge-ok' : 'badge-error' ?>">
                    <?= $hasPaymentMethodId ? 'Configured' : 'Missing' ?>
                </span>
            </div>
            <div class="status-item">
                <span>Payment Types</span>
                <span class="badge <?= $hasPaymentTypes ? 'badge-ok' : 'badge-error' ?>">
                    <?= $hasPaymentTypes ? htmlspecialchars($config['paymentMethodTypes']) : 'Missing' ?>
                </span>
            </div>
            <?php if ($isTestMode): ?>
            <div class="status-item">
                <span>Mode</span>
                <span class="badge badge-warn">TEST MODE</span>
            </div>
            <?php endif; ?>
        </div>

        <div class="card">
            <h2>Session Statistics</h2>
            <div style="display: flex; justify-content: space-around;">
                <div class="stat">
                    <div class="number"><?= $totalSessions ?></div>
                    <div class="label">Total</div>
                </div>
                <div class="stat">
                    <div class="number"><?= $completedSessions ?></div>
                    <div class="label">Completed</div>
                </div>
                <div class="stat">
                    <div class="number"><?= $pendingSessions ?></div>
                    <div class="label">Pending</div>
                </div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>Webhook URL</h2>
        <p style="margin-bottom: 8px; font-size: 0.9em; color: #7f8c8d;">
            Configure this URL in your PayMongo dashboard under Webhooks:
        </p>
        <div class="webhook-url"><?= htmlspecialchars($webhookUrl) ?></div>
    </div>

    <?php if (!empty($recentSessions)): ?>
    <div class="card">
        <h2>Recent Sessions (Last 20)</h2>
        <table>
            <thead>
                <tr>
                    <th>Session ID</th>
                    <th>Invoice</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Created</th>
                </tr>
            </thead>
            <tbody>
                <?php foreach ($recentSessions as $sid => $s): ?>
                <tr>
                    <td style="font-family: monospace; font-size: 0.85em;"><?= htmlspecialchars(substr($sid, 0, 20)) ?>...</td>
                    <td><?= htmlspecialchars($s['invoice_number'] ?? $s['invoice_id'] ?? '?') ?></td>
                    <td>PHP <?= number_format((float)($s['amount'] ?? 0), 2) ?></td>
                    <td>
                        <span class="badge <?= ($s['status'] ?? '') === 'completed' ? 'badge-ok' : 'badge-info' ?>">
                            <?= htmlspecialchars($s['status'] ?? 'unknown') ?>
                        </span>
                    </td>
                    <td><?= htmlspecialchars($s['created_at'] ?? '') ?></td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    </div>
    <?php endif; ?>

    <div class="card">
        <h2>Recent Log Entries</h2>
        <div class="log-box"><?php
            if (empty($logEntries)) {
                echo 'No log entries yet.';
            } else {
                foreach ($logEntries as $line) {
                    echo htmlspecialchars($line) . "\n";
                }
            }
        ?></div>
    </div>
</body>
</html>
