<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - Imperial Networks</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f6fa; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
        .container { background: #fff; border-radius: 12px; padding: 40px; max-width: 480px; width: 100%; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .icon { font-size: 3em; margin-bottom: 16px; }
        h1 { font-size: 1.5em; color: #e74c3c; margin-bottom: 12px; }
        p { color: #555; line-height: 1.6; margin-bottom: 20px; }
        .error-message { background: #f8f9fa; border-left: 4px solid #e74c3c; padding: 12px 16px; text-align: left; margin-bottom: 20px; font-size: 0.9em; color: #333; border-radius: 0 4px 4px 0; }
        .btn { display: inline-block; padding: 12px 32px; background: #3498db; color: #fff; text-decoration: none; border-radius: 6px; font-weight: 600; transition: background 0.2s; }
        .btn:hover { background: #2980b9; }
        .note { font-size: 0.85em; color: #999; margin-top: 16px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">&#9888;</div>
        <h1>Something Went Wrong</h1>
        <?php if (!empty($message)): ?>
        <div class="error-message"><?= htmlspecialchars($message) ?></div>
        <?php endif; ?>
        <p>We encountered an error while processing your request. Please try again.</p>
        <a href="javascript:history.back()" class="btn">Go Back</a>
        <p class="note">If this problem persists, please contact Imperial Networks support.</p>
    </div>
</body>
</html>
