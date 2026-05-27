<?php
declare(strict_types=1);

const API_KEY = '';
const BASE_URL = 'https://www.ezplm.cn';
const PART_KEYWORD = 'TPS79301DBVR';
const PAGE_SIZE = '10';

function canonical_query(array $params): string
{
    $items = [];
    foreach ($params as $key => $value) {
        if ($value === null || $value === '') {
            continue;
        }
        $items[] = [(string)$key, (string)$value];
    }
    usort($items, function (array $left, array $right): int {
        if ($left[0] === $right[0]) {
            return strcmp($left[1], $right[1]);
        }
        return strcmp($left[0], $right[0]);
    });
    $pairs = array_map(function (array $item): string {
        return rawurlencode($item[0]) . '=' . rawurlencode($item[1]);
    }, $items);
    return implode('&', $pairs);
}

function base64url_encode(string $binary): string
{
    return rtrim(strtr(base64_encode($binary), '+/', '-_'), '=');
}

function build_signature(string $apiKey, string $method, string $path, array $params, string $timestamp, string $nonce): string
{
    $canonical = implode("\n", [
        strtoupper($method),
        $path,
        canonical_query($params),
        $timestamp,
        $nonce,
    ]);
    return base64url_encode(hash_hmac('sha256', $canonical, $apiKey, true));
}

function request_json(string $baseUrl, string $apiKey, string $path, array $params): array
{
    $timestamp = (string)time();
    $nonce = bin2hex(random_bytes(16));
    $signature = build_signature($apiKey, 'GET', $path, $params, $timestamp, $nonce);
    $query = canonical_query($params);
    $url = $baseUrl . $path . ($query !== '' ? '?' . $query : '');

    $headers = [
        'X-API-Key: ' . $apiKey,
        'X-Timestamp: ' . $timestamp,
        'X-Nonce: ' . $nonce,
        'X-Signature: ' . $signature,
    ];

    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_TIMEOUT => 30,
    ]);

    $body = curl_exec($ch);
    $status = (int)curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    if ($body === false) {
        $body = json_encode(['raw' => curl_error($ch)], JSON_UNESCAPED_UNICODE);
    }
    curl_close($ch);

    $parsed = json_decode((string)$body, true);
    if (!is_array($parsed)) {
        $parsed = ['raw' => (string)$body];
    }

    return [$status, $parsed];
}

$apiKey = API_KEY;
$baseUrl = BASE_URL;
$keyword = PART_KEYWORD;
$pageSize = PAGE_SIZE;

[$partsStatus, $partsBody] = request_json($baseUrl, $apiKey, '/api/v1/api-key/parts', [
    'keyword' => $keyword,
    'pageSize' => $pageSize,
]);

echo "parts_status = {$partsStatus}\n";
echo json_encode($partsBody, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\n";

if (!isset($partsBody['data']) || !is_array($partsBody['data']) || count($partsBody['data']) === 0) {
    fwrite(STDERR, "no part returned\n");
    exit(2);
}

$partlibId = (string)$partsBody['data'][0]['id'];
[$refsStatus, $refsBody] = request_json($baseUrl, $apiKey, '/api/v1/api-key/reference-designs', [
    'partlibId' => $partlibId,
    'pageSize' => $pageSize,
]);

echo "reference_designs_status = {$refsStatus}\n";
echo json_encode($refsBody, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) . "\n";

exit($partsStatus === 200 && $refsStatus === 200 ? 0 : 3);
