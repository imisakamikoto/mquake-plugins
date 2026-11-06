# 04 · 四种数据通道

`transport.type` 决定宿主怎么拿到数据。四种通道输出**同一套报文**
（见 [03](03-protocol.md)），可以随时切换而不改数据结构。

---

## 1. `file` · 静态文件（最简单，全平台）

```json
"transport": { "type": "file", "file": "data.json", "intervalSeconds": 60 }
```

- 读包内相对路径；支持 `.json` / `.geojson` / `.jsonl` / 任意 UTF-8 文本。
- 启动时立即读一次，之后每 `intervalSeconds` 重读（默认 60 秒，下限 5 秒）。
- 适合：手工维护的数据、由外部脚本定时覆写的文件、GeoJSON 图层、配置快照。
- 单文件上限 1 MB。文件不存在会记为一次错误并继续重试。

**开发提速**：把插件目录直接放进 `data/plugins/`，改完数据文件点「立即刷新」，
无需重新打包。

---

## 2. `http` · 定时轮询（全平台）

```json
"transport": {
  "type": "http",
  "url": "https://api.example.com/v1/data?city=${config.city}&t=${now}",
  "method": "GET",
  "headers": { "X-Api-Key": "${config.apiKey}" },
  "intervalSeconds": 30,
  "timeoutSeconds": 8
}
```

| 字段 | 说明 |
| --- | --- |
| `url` | 支持模板变量；scheme 只能 `http` / `https` |
| `method` | `GET`（默认）或 `POST` |
| `headers` | 值支持模板变量 |
| `body` | `POST` 时的请求体，支持模板变量 |
| `timeoutSeconds` | 1–60，默认 8 |
| `intervalSeconds` | 下限 5 秒 |

规则：

- **主机白名单在每次请求前校验**（模板展开后的实际 URL）。未列入
  `permissions.hosts` 的主机直接拒绝，不会发请求。
- 非 2xx 记为错误，带 HTTP 状态码；响应上限 1 MB；超时记为错误。
- 错误只影响本插件，下一次间隔后自动重试。
- `mapping` 可以把任意接口结构映射成标准字段，见 [02-manifest.md](02-manifest.md#mapping字段映射)。

配套示例：[`examples/http-json/`](../examples/http-json/) 含一个纯标准库的
`server.py`，`python server.py` 后监听 `127.0.0.1:8765/data.json`。

---

## 3. `websocket` · 长连接推送（全平台）

```json
"transport": {
  "type": "websocket",
  "url": "ws://127.0.0.1:8766",
  "intervalSeconds": 5,
  "timeoutSeconds": 8
}
```

- 建立连接后，服务端**随时**可推送报文（一行一条 JSON 或单个 JSON 对象）。
- 断开或出错后 **5 秒自动重连**，重连期间状态显示 `error`，不影响其它插件。
- 每次收到的报文独立解析；推荐用 `{"type":"patch", ...}` 做增量更新。
- 同样受 `permissions.hosts` 白名单约束，支持 `ws` / `wss`。
- 报文上限 1 MB，超长报文记错并丢弃。

配套示例：[`examples/websocket/server.py`](../examples/websocket/server.py)
（`pip install websockets` 后运行）。

---

## 4. `process` · 子进程 JSONL（任意语言，仅桌面）

```json
"transport": {
  "type": "process",
  "command": "python",
  "args": ["main.py", "--city", "${config.city}"],
  "intervalSeconds": 10,
  "timeoutSeconds": 8
}
```

这是**能力最强**的通道：插件可以是一个完整程序，用 Python / Node / Go / Rust /
C# / shell 写都行，宿主只认它的 stdout。

### 协议

| 方向 | 内容 |
| --- | --- |
| 宿主 → 插件 stdin | 每 `intervalSeconds` 一行 `{"type":"tick"}`（请求新数据） |
| 插件 → 宿主 stdout | **每行一个 JSON 对象**，即一条报文 |
| 插件 → 宿主 stderr | 每行转成 `warning` 级插件日志 |
| 退出 | 非 0 退出码记为错误；宿主停用插件时会 `kill` 进程 |

要点：

- 工作目录（`cwd`）自动设为插件解包目录，`args` 里的相对路径基于它。
- 用 `runInShell: false` 启动，**不会**经过 shell 解释，避免命令注入。
- `command` 不能包含路径穿越；建议用 PATH 里的可执行名（`python` / `python3` /
  `node` / `deno` …）或写清绝对路径。
- 必须 `permissions.process: true`，否则清单校验直接失败。
- **移动端（Android/iOS）一律拒绝**该通道，请改用 `http` / `websocket`。
- 记得 `flush`：Python 用 `print(..., flush=True)` 或 `sys.stdout.flush()`，
  Node 用 `process.stdout.write(... + "\n")`，否则输出被缓冲，宿主收不到。

### 最小实现（Python）

```python
import json, sys

print(json.dumps({"type": "snapshot", "cards": [
    {"id": "hello", "title": "来自子进程"}
]}), flush=True)

for line in sys.stdin:
    print(json.dumps({"type": "patch", "metrics": [
        {"id": "v", "label": "当前值", "value": 42}
    ]}), flush=True)
```

完整示例见 [`examples/process-jsonl/main.py`](../examples/process-jsonl/main.py)：
带趋势历史、运行状态卡与心跳通知。

### 什么时候用哪种

| 需求 | 推荐通道 |
| --- | --- |
| 手工维护的小数据、图层、配置 | `file` |
| 已有 REST 接口 / 云端数据 | `http` |
| 需要秒级实时推送 | `websocket` |
| 需要本地计算、读串口/文件/硬件、用现成库 | `process` |
| 移动端也要跑 | `file` / `http` / `websocket` |

---

## 通用限制

| 项 | 值 |
| --- | --- |
| 单次报文 | ≤ 1 MB |
| `.mqe` 解包后总计 | ≤ 32 MB |
| 单文件 | ≤ 8 MB |
| 包内文件数 | ≤ 512 |
| 轮询间隔 | ≥ 5 秒（低于此值运行时强制提升并给 WARN） |
| HTTP 超时 | 1–60 秒 |

这些限制是刻意的：插件不应拖慢官方 1 秒级测站轮询与预警链路。
