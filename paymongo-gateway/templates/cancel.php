<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment Cancelled - Imperial Networks</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f6fa; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .container { background: #fff; border-radius: 12px; padding: 40px; max-width: 480px; width: 100%; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .icon { font-size: 3em; margin-bottom: 16px; }
        h1 { font-size: 1.5em; color: #e67e22; margin-bottom: 12px; }
        p { color: #555; line-height: 1.6; margin-bottom: 20px; }
        .btn { display: inline-block; padding: 12px 32px; background: #3498db; color: #fff; text-decoration: none; border-radius: 6px; font-weight: 600; transition: background 0.2s; margin: 0 8px; }
        .btn:hover { background: #2980b9; }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">&#10060;</div>
        <h1>Payment Cancelled</h1>
        <p>Your payment was not completed. No charges have been made to your account.</p>
        <a href="<?= htmlspecialchars($retryUrl ?? $clientZoneUrl ?? '#') ?>" class="btn">Return to Client Portal</a>
    </div>
</body>
</html>
