<?php

declare(strict_types=1);

class Logger
{
    private string $logFile;

    public function __construct(string $logFile = null)
    {
        $this->logFile = $logFile ?? __DIR__ . '/../data/plugin.log';
    }

    public function info(string $message, array $context = []): void
    {
        $this->log('INFO', $message, $context);
    }

    public function warning(string $message, array $context = []): void
    {
        $this->log('WARNING', $message, $context);
    }

    public function error(string $message, array $context = []): void
    {
        $this->log('ERROR', $message, $context);
    }

    private function log(string $level, string $message, array $context): void
    {
        $timestamp = date('Y-m-d H:i:s');
        $entry = "[{$timestamp}] [{$level}] {$message}";

        if (!empty($context)) {
            $entry .= ' ' . json_encode($context, JSON_UNESCAPED_SLASHES);
        }

        $entry .= PHP_EOL;

        $dir = dirname($this->logFile);
        if (!is_dir($dir)) {
            mkdir($dir, 0755, true);
        }

        file_put_contents($this->logFile, $entry, FILE_APPEND | LOCK_EX);
    }
}
