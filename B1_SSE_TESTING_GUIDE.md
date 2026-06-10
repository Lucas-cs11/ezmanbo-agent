# B1：FastAPI SSE 流式输出接口 - 测试指南

## 🎯 完成的功能

已在 `app/main.py` 中实现：

### 1. 新增 `/analyze/stream` 端点（POST）
- 接受 JSON 请求：`{"user_input": "..."}`
- 返回 SSE 流式响应（`text/event-stream`）

### 2. 实现 `_stream_analyze()` 异步生成器
按照以下阶段逐级推送 SSE 事件：

```
parse_done        → 需求解析完成 + 约束条件
  ↓
search_done       → 搜索完成 + 候选器件数量
  ↓
score_update      → 每个器件评分完成（多次）
  ↓
evidence_done     → 证据链构建完成 + 证据条数
  ↓
risk_done         → 风险评估完成 + RiskIR
  ↓
text_delta        → 报告文本片段逐行推送
  ↓
done              → 分析完成 + 总耗时 + 完整报告
```

### 3. CORS 配置
已配置允许以下来源：
- `http://localhost:3000`（Next.js dev server）
- `http://localhost:3001`（备用）

### 4. SSE 响应头
```
Cache-Control: no-cache
X-Accel-Buffering: no
Connection: keep-alive
```

---

## 📝 测试方法

### 方法 1：使用 Python 测试脚本（推荐）

```bash
# 1. 启动后端服务
cd d:/python\ project/ezplm-component-risk-agent
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 2. 在另一个终端运行测试脚本
python test_b1_sse.py
```

### 方法 2：使用 curl

```bash
# 基础测试（检查连接）
curl -X POST http://localhost:8000/analyze/stream \
  -H "Content-Type: application/json" \
  -d '{"user_input": "我需要一个24V到5V的降压芯片"}' \
  --no-buffer

# 保存到文件，便于查看事件流
curl -X POST http://localhost:8000/analyze/stream \
  -H "Content-Type: application/json" \
  -d '{"user_input": "5V/1A的LDO"}' \
  --no-buffer > /tmp/sse_output.txt

# 实时查看事件流（使用 jq 解析 JSON）
curl -X POST http://localhost:8000/analyze/stream \
  -H "Content-Type: application/json" \
  -d '{"user_input": "车规级12V降压"}' \
  --no-buffer | grep "^data:" | sed 's/^data: //' | jq .
```

### 方法 3：使用 PowerShell（Windows）

```powershell
# 发送请求
$uri = "http://localhost:8000/analyze/stream"
$body = @{ user_input = "我需要一个5V/3A的降压芯片" } | ConvertTo-Json
$response = Invoke-WebRequest -Uri $uri -Method POST -Body $body -ContentType "application/json" -UseBasicParsing

# 读取流式响应
$response.RawContent | Write-Host
```

### 方法 4：使用浏览器 (使用 EventSource)

创建一个 HTML 文件 `test_sse.html`：

```html
<!DOCTYPE html>
<html>
<head>
    <title>B1 SSE 流式测试</title>
    <style>
        body { font-family: monospace; margin: 20px; }
        #events { border: 1px solid #ccc; padding: 10px; height: 400px; overflow-y: auto; }
        .event { margin: 5px 0; padding: 5px; border-left: 3px solid #0066cc; }
    </style>
</head>
<body>
    <h2>B1 SSE 流式输出测试</h2>
    <div>
        <input type="text" id="input" placeholder="输入需求..." value="我需要一个5V/1A的LDO">
        <button onclick="startStream()">开始分析</button>
    </div>
    <div id="events"></div>

    <script>
        function startStream() {
            const input = document.getElementById('input').value;
            const eventsDiv = document.getElementById('events');
            eventsDiv.innerHTML = '<p>连接中...</p>';

            fetch('http://localhost:8000/analyze/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_input: input })
            })
            .then(response => {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                return reader.read().then(function process({ done, value }) {
                    if (done) return;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop();

                    for (const line of lines) {
                        if (line.startsWith('event: ')) {
                            const eventType = line.slice(7);
                            console.log('Event:', eventType);
                        }
                        if (line.startsWith('data: ')) {
                            const data = JSON.parse(line.slice(6));
                            const eventDiv = document.createElement('div');
                            eventDiv.className = 'event';
                            eventDiv.textContent = JSON.stringify(data, null, 2);
                            eventsDiv.appendChild(eventDiv);
                            eventsDiv.scrollTop = eventsDiv.scrollHeight;
                        }
                    }

                    return reader.read().then(process);
                });
            })
            .catch(err => {
                eventsDiv.innerHTML = `<p style="color: red;">错误: ${err.message}</p>`;
            });
        }
    </script>
</body>
</html>
```

在浏览器中打开此文件，输入需求并点击按钮观看实时事件流。

---

## 🔍 预期行为

### 成功流程
1. ✅ 连接建立，状态码 200
2. ✅ Content-Type: `text/event-stream`
3. ✅ 逐个接收事件，无阻塞
4. ✅ 最后接收 `done` 事件，包含完整报告

### 事件样例

```json
// parse_done
{
  "status": "需求解析完成",
  "constraint": {
    "raw_input": "...",
    "topology": "buck",
    "output_voltage_v": 5.0
  }
}

// search_done
{
  "status": "搜索完成",
  "candidate_count": 12
}

// score_update
{
  "status": "评分完成: SY8240ABC",
  "index": 0,
  "total": 12,
  "part_number": "SY8240ABC",
  "score": 92.5
}

// done
{
  "status": "分析完成",
  "elapsed_seconds": 4.32,
  "report": {
    "request_id": "...",
    "user_input": "...",
    "candidates": [...],
    "recommended_parts": [...]
  }
}
```

---

## 🐛 常见问题排查

| 问题 | 排查步骤 |
|------|--------|
| **无法连接** | 1. 检查后端是否运行：`curl http://localhost:8000/health` 2. 检查端口是否正确 |
| **CORS 错误** | CORS 中间件已配置，如仍有问题检查浏览器跨域设置 |
| **流式响应中断** | 检查网络连接，确保请求未超时（timeout 设置为 30s） |
| **数据为空** | 检查 mock 数据源（`ezplm_client.py`）是否正确初始化 |

---

## ✅ 任务完成清单

- [x] 新增 `/analyze/stream` 端点
- [x] 实现 `_stream_analyze()` 生成器
- [x] 配置 CORS（localhost:3000）
- [x] 设置正确的 SSE 响应头
- [x] 提供多种测试方法
- [ ] 与前端集成（队友 A 的 F2 任务）

---

## 📌 后续接入前端（队友 A）

前端将使用 `EventSource` 或 `fetch` 对接：

```javascript
// 前端 F2：Claude 风对话界面
const eventSource = new EventSource('http://localhost:8000/analyze/stream', {
  method: 'POST',
  body: JSON.stringify({ user_input: userInput })
});

eventSource.addEventListener('parse_done', (e) => {
  const data = JSON.parse(e.data);
  console.log('需求已解析:', data.constraint);
});

eventSource.addEventListener('text_delta', (e) => {
  const data = JSON.parse(e.data);
  // 追加到消息气泡
  appendToMessage(data.text);
});

eventSource.addEventListener('done', (e) => {
  const data = JSON.parse(e.data);
  // 显示完整报告
  displayReport(data.report);
});
```

---

## 📚 相关文件

- `app/main.py` - 主入口，包含 SSE 端点和生成器
- `test_b1_sse.py` - Python 测试脚本
- `test_sse.html` - 浏览器测试页面（可选）

---

**B1 任务完成！** 🎉 SSE 流式输出接口已可用。
下一步：队友 A 完成 F2（前端打字效果）对接。
