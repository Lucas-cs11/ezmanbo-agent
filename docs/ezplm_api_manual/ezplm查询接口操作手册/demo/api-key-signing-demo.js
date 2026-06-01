#!/usr/bin/env node
import crypto from 'node:crypto';

const apiKey = '';
const baseUrl = 'https://www.ezplm.cn';
const keyword = 'TPS79301DBVR';
const pageSize = '10';

function canonicalQuery(params) {
  return Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && String(value) !== '')
    .map(([key, value]) => [String(key), String(value)])
    .sort(([leftKey, leftValue], [rightKey, rightValue]) =>
      leftKey === rightKey
        ? leftValue.localeCompare(rightValue)
        : leftKey.localeCompare(rightKey),
    )
    .map(
      ([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`,
    )
    .join('&');
}

function buildSignature({ method, path, params, timestamp, nonce }) {
  const canonical = [
    method.toUpperCase(),
    path,
    canonicalQuery(params),
    timestamp,
    nonce,
  ].join('\n');
  return crypto
    .createHmac('sha256', apiKey)
    .update(canonical)
    .digest('base64url');
}

async function requestJson(path, params) {
  const timestamp = Math.floor(Date.now() / 1000).toString();
  const nonce = crypto.randomUUID();
  const signature = buildSignature({ method: 'GET', path, params, timestamp, nonce });
  const query = canonicalQuery(params);
  const url = query ? `${baseUrl}${path}?${query}` : `${baseUrl}${path}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'X-API-Key': apiKey,
      'X-Timestamp': timestamp,
      'X-Nonce': nonce,
      'X-Signature': signature,
    },
  });

  const body = await response.text();
  let parsed;
  try {
    parsed = JSON.parse(body);
  } catch {
    parsed = { raw: body };
  }
  return { status: response.status, body: parsed };
}

const parts = await requestJson('/api/v1/api-key/parts', {
  keyword,
  pageSize,
});
console.log('parts_status =', parts.status);
console.log(JSON.stringify(parts.body, null, 2));

if (!Array.isArray(parts.body?.data) || parts.body.data.length === 0) {
  console.error('no part returned');
  process.exit(2);
}

const partlibId = parts.body.data[0].id;
const refs = await requestJson('/api/v1/api-key/reference-designs', {
  partlibId,
  pageSize,
});
console.log('reference_designs_status =', refs.status);
console.log(JSON.stringify(refs.body, null, 2));

process.exit(parts.status === 200 && refs.status === 200 ? 0 : 3);
