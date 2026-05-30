# API Key 签名 Demo

这组示例演示如何用同一把 `API Key` 调用两个公开接口：

- `GET /api/v1/api-key/parts`
- `GET /api/v1/api-key/reference-designs`

签名规则：

- `X-API-Key` 作为 HMAC 密钥
- `X-Timestamp` 使用 Unix 秒级时间戳
- `X-Nonce` 为一次性随机串
- `X-Signature = base64url(HMAC-SHA256(X-API-Key, canonicalRequest))`

canonicalRequest 的拼接顺序：

1. 请求方法
2. 请求路径
3. 按 key 字典序排序后的查询串
4. `X-Timestamp`
5. `X-Nonce`

## 默认值

这三份脚本已经把默认值写死在文件开头，不依赖环境变量也能直接跑通：

- `API_KEY`：当前示例 key
- `BASE_URL`：`https://www.ezplm.cn`
- `PART_KEYWORD`：`TPS79301DBVR`
- `PAGE_SIZE`：`10`

## 运行示例

### Python

```bash
python3 samples/api-key-signing-demo.py
```

### Node.js

```bash
node samples/api-key-signing-demo.js
```

### PHP

```bash
php samples/api-key-signing-demo.php
```
