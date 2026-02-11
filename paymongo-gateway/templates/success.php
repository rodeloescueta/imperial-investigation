<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment Successful - Imperial Networks</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f6fa; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .container { background: #fff; border-radius: 12px; padding: 40px; max-width: 480px; width: 100%; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .icon { font-size: 3em; margin-bottom: 16px; }
        h1 { font-size: 1.5em; color: #27ae60; margin-bottom: 12px; }
        p { color: #555; line-height: 1.6; margin-bottom: 20px; }
        .btn { display: inline-block; padding: 12px 32px; background: #3498db; color: #fff; text-decoration: none; border-radius: 6px; font-weight: 600; transition: background 0.2s; }
        .btn:hover { background: #2980b9; }
        .note { font-size: 0.85em; color: #999; margin-top: 16px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">&#10004;</div>
        <h1>Payment Successful</h1>
        <p>Your payment has been received and is being processed. Your invoice will be updated shortly.</p>
        <a href="<?= htmlspecialchars($clientZoneUrl ?? '#') ?>" class="btn">Return to Client Portal</a>
        <p class="note">If your invoice does not update within a few minutes, please contact support.</p>
    </div>
</body>
</html>
