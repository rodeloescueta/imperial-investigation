<?php

declare(strict_types=1);

class PayMongoClient
{
    private string $secretKey;
    private string $baseUrl = 'https://api.paymongo.com/v1';

    public function __construct(string $secretKey)
    {
        $this->secretKey = $secretKey;
    }

    /**
     * Create a PayMongo Checkout Session.
     *
     * @param int    $amountCentavos  Amount in centavos (e.g., 79900 = PHP 799.00)
     * @param string $description     Payment description shown to customer
     * @param array  $paymentMethods  e.g., ['card', 'gcash', 'paymaya', 'grab_pay']
     * @param string $successUrl      Redirect URL after successful payment
     * @param string $cancelUrl       Redirect URL if customer cancels
     * @param array  $metadata        Metadata attached to the session (invoice_id, client_id, etc.)
     */
    public function createCheckoutSession(
        int $amountCentavos,
        string $description,
        array $paymentMethods,
        string $successUrl,
        string $cancelUrl,
        array $metadata = []
    ): array {
        return $this->request('POST', '/checkout_sessions', [
            'data' => [
                'attributes' => [
                    'line_items' => [
                        [
                            'name' => $description,
                            'amount' => $amountCentavos,
                            'currency' => 'PHP',
                            'quantity' => 1,
                        ],
                    ],
                    'payment_method_types' => $paymentMethods,
                    'success_url' => $successUrl,
                    'cancel_url' => $cancelUrl,
                    'send_email_receipt' => false,
                    'show_description' => true,
                    'show_line_items' => true,
                    'description' => $description,
                    'metadata' => $metadata,
                ],
            ],
        ]);
    }

    /**
     * Retrieve a Checkout Session by ID.
     */
    public function retrieveCheckoutSession(string $id): array
    {
        return $this->request('GET', "/checkout_sessions/{$id}");
    }

    /**
     * Verify PayMongo webhook signature (HMAC-SHA256).
     *
     * PayMongo sends a Paymongo-Signature header in the format:
     *   t={timestamp},te={test_signature},li={live_signature}
     *
     * The signed payload is: {timestamp}.{raw_body}
     */
    public function verifyWebhookSignature(string $rawBody, string $signatureHeader, string $webhookSecret): bool
    {
        $parts = explode(',', $signatureHeader);
        $timestamp = null;
        $testSignature = null;
        $liveSignature = null;

        foreach ($parts as $part) {
            $pair = explode('=', $part, 2);
            if (count($pair) !== 2) {
                continue;
            }
            [$key, $value] = $pair;
            switch ($key) {
                case 't':
                    $timestamp = $value;
                    break;
                case 'te':
                    $testSignature = $value;
                    break;
                case 'li':
                    $liveSignature = $value;
                    break;
            }
        }

        // Use live signature if available, otherwise test
        $signature = $liveSignature ?? $testSignature;
        if ($timestamp === null || $signature === null) {
            return false;
        }

        $expectedSignature = hash_hmac('sha256', "{$timestamp}.{$rawBody}", $webhookSecret);

        return hash_equals($expectedSignature, $signature);
    }

    private function request(string $method, string $endpoint, ?array $data = null): array
    {
        $url = $this->baseUrl . $endpoint;
        $ch = curl_init($url);

        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_USERPWD => $this->secretKey . ':',
            CURLOPT_HTTPHEADER => [
                'Content-Type: application/json',
                'Accept: application/json',
            ],
            CURLOPT_TIMEOUT => 30,
            CURLOPT_CONNECTTIMEOUT => 10,
        ]);

        if ($method === 'POST' && $data !== null) {
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curlError = curl_error($ch);
        curl_close($ch);

        if ($curlError) {
            throw new RuntimeException("PayMongo API connection error: {$curlError}");
        }

        if ($httpCode >= 400) {
            throw new RuntimeException("PayMongo API error (HTTP {$httpCode}): {$response}");
        }

        $decoded = json_decode($response, true);
        if ($decoded === null) {
            throw new RuntimeException("PayMongo API returned invalid JSON: {$response}");
        }

        return $decoded;
    }
}
