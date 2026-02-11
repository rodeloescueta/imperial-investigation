<?php

declare(strict_types=1);

class UispClient
{
    private string $baseUrl;
    private string $appKey;

    public function __construct(string $baseUrl, string $appKey)
    {
        $this->baseUrl = rtrim($baseUrl, '/') . '/api/v1.0';
        $this->appKey = $appKey;
    }

    /**
     * Resolve a payment token to get invoice/client/amount details.
     *
     * Returns: { invoiceId, invoiceIds, clientId, amount, currency, ... }
     */
    public function resolvePaymentToken(string $token): array
    {
        return $this->request('GET', "/payment-tokens/{$token}");
    }

    /**
     * Get invoice details by ID.
     */
    public function getInvoice(int $invoiceId): array
    {
        return $this->request('GET', "/invoices/{$invoiceId}");
    }

    /**
     * Create a payment in UISP.
     *
     * Required fields: clientId, amount, methodId, currencyCode
     * Optional: invoiceIds (array), note, providerName, providerPaymentId, createdDate
     */
    public function createPayment(array $data): array
    {
        return $this->request('POST', '/payments', $data);
    }

    private function request(string $method, string $endpoint, ?array $data = null): array
    {
        $url = $this->baseUrl . $endpoint;
        $ch = curl_init($url);

        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_SSL_VERIFYPEER => false, // Localhost self-signed cert
            CURLOPT_SSL_VERIFYHOST => false,
            CURLOPT_HTTPHEADER => [
                'Content-Type: application/json',
                'X-Auth-App-Key: ' . $this->appKey,
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
            throw new RuntimeException("UISP API connection error: {$curlError}");
        }

        if ($httpCode >= 400) {
            throw new RuntimeException("UISP API error (HTTP {$httpCode}): {$response}");
        }

        $decoded = json_decode($response, true);
        if ($decoded === null && $response !== '') {
            throw new RuntimeException("UISP API returned invalid JSON: {$response}");
        }

        return $decoded ?? [];
    }
}
