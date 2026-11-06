# 07 · 示例插件逐讲

五个示例覆盖全部通道与主要能力。每个目录都能直接
`python tools/mqe.py validate <dir>` 通过。

---

## 1. `hello-static` — 静态数据，一次演示 8 类能力

**通道**：`file` → `data.json`
**能力**：`events` `stations` `overlay` `cards` `metrics` `actions` `rules` `notifications`

打开 `data.json` 可以看到一条报文里同时塞了 8 个分区：

- `cards`：两张卡，一张带 `rows` 键值行与 `priority`，一张带 `url`；
- `metrics`：一个带 `history` 的指标（设置页会画迷你趋势图），一个纯数值；
- `events`：一条演示事件，经纬度指向东京湾 — 会出现在事件列表，
  但**不会**响任何声音；
- `stations`：一个自定义测站，画在地图上；
- `overlays`：marker / circle / polyline / polygon 四种形状各一；
- `notifications`：一条 `info` 级应用内通知；
- `actions`：一个「查看开发文档」按钮；
- `rules`：一条 `color`（指标 ≥ 40 变红）、一条 `derive`（派生高值卡片）。

清单里 `permissions.overlay: true`，否则地图部分会被忽略。
`settings` 演示了 text / number / toggle 三种表单控件。

**适合**：想快速看「插件到底能在界面上做什么」，直接用它。

> 这个示例**没有**授予 `permissions.alerts`，所以它的事件只展示、测站只在地图绘制，
> 不会触发任何预警。想看预警链路见下面第 6 个示例。

---

## 2. `http-json` — HTTP 轮询 + 白名单 + 模板 + 字段映射

**通道**：`http`（本机 8765）
**能力**：`events` `metrics` `cards`

要点：

```json
"url": "http://127.0.0.1:8765/data.json?city=${config.city}&t=${now}",
"headers": { "X-Api-Key": "${config.apiKey}" },
"permissions": { "hosts": ["127.0.0.1", "localhost", "api.example.com"] },
"settings": [
  { "key": "city", "type": "select", "options": ["tokyo","osaka","sendai"] }
],
"mapping": {
  "events": { "path": "data.items",
    "fields": { "id": "event_id", "title": "name", "latitude": "lat" } }
}
```

`server.py` 返回的正是 `{"data":{"items":[{...}]}}` 这种非标准结构，
`mapping` 把它映射成标准 `events`。**不用写一行转换代码**。

试跑：

```bash
python examples/http-json/server.py          # 终端 1
python tools/mqe.py pack examples/http-json  # 终端 2
# 应用里安装生成的 .mqe 并启用
```

改 `settings` 里的城市后点「保存并重启」，URL 里的 `${config.city}` 立即变化。

---

## 3. `process-jsonl` — 用 Python 写真正的逻辑

**通道**：`process`（`python main.py`）
**能力**：`metrics` `cards` `notifications` `overlay`
**权限**：`process: true`

`main.py` 演示了子进程协议的全部要点：

1. 启动时先输出一条 `snapshot` 建立初始卡片；
2. 每次收到宿主的 `{"type":"tick"}` 就计算一个正弦波数值；
3. 用 `patch` 增量更新 `metrics`（带滚动 `history`）与运行状态卡；
4. 每 12 个周期发一条心跳通知；
5. 所有输出 `sys.stdout.flush()`，否则缓冲会让宿主收不到。

Windows 上如果 `python` 不在 PATH，把 `transport.command` 改成 `python3`
或写绝对路径（绝对路径不允许 `..`，但可以是 `C:/Python311/python.exe`）。

> 把 `main.py` 换成 Node / Go / Rust 程序同样可行，只要 stdout 每行一条 JSON。

---

## 4. `geojson-overlay` — 裸 GeoJSON 直接当数据文件

**通道**：`file` → `features.geojson`
**能力**：`overlay` `cards`

数据文件就是一个标准 `FeatureCollection`，宿主自动识别：

| GeoJSON 几何 | 转成 |
| --- | --- |
| `Point` | marker |
| `LineString` | polyline |
| `Polygon` / `MultiPolygon` | polygon |

`properties` 里的 `name` / `color` / `fill` / `strokeWidth` / `radius` /
`description` 会读成样式。GeoJSON 的 `[lon, lat]` 顺序宿主自动翻转。

**适合**：已有 GIS 数据、行政区划、自定义观测区，零转换成本。

---

## 5. `websocket` — 秒级实时推送

**通道**：`websocket`（`ws://127.0.0.1:8766`）
**能力**：`metrics` `cards` `overlay`

`server.py` 每 2 秒推一条 `patch` 报文。宿主断线 5 秒后自动重连，
可以在插件管理页观察 `error → ok` 的状态变化。

试跑：

```bash
pip install websockets
python examples/websocket/server.py
```

---

## 组合建议

| 想做的事 | 抄哪个 | 需要改 |
| --- | --- | --- |
| 展示自己的传感器数值 | `process-jsonl` | `main.py` 的取值逻辑 |
| 接入公司/学校 REST 接口 | `http-json` | `url`、`hosts`、`mapping` |
| 画自定义区域 / 路线 | `geojson-overlay` | `features.geojson` |
| 做一块信息看板 | `hello-static` | `cards` / `metrics` |
| 实时行情/遥测 | `websocket` | `server.py` 推送内容 |
| 自定义预警 / 台站参与推算 | `alert-eew` | `data.json` 的事件与测站字段 |


---

## 6. `alert-eew` — 预警授权（会真的出声）

**通道**：`file` → `data.json`　**能力**：`events` `stations` `cards`　**权限**：`alerts: true`

> ⚠️ 启用这个插件会真的播放紧急地震速报警报音、发通知、弹全屏并 TTS 播报。
> 请确认后再打开开关。

关键点在 `plugin.json`：

```json
"permissions": { "alerts": true, "hosts": [], "process": false }
```

以及 `data.json`：

```json
{
  "type": "snapshot",
  "events": [{
    "id": "eew-001", "isEew": true, "active": true,
    "eewKind": "警報", "reportNum": 1,
    "shindo": "5-", "maxEstimatedIntensity": 4.8,
    "warnRegionCount": 7, "place": "东京湾"
  }],
  "stations": [{ "code": "PLG-S1", "shindo": 4.2, "pga": 120 }]
}
```

- `isEew` + `active` + 清单授权三者齐备才会进入 `activeEew`；
- `eewKind: "警報"` 或 `shindo` ≥ 5 弱 → 警报音；否则预报音；
- `reportNum` 递增 → 更新音；`warnRegionCount` 增加 ≥ 3 → 补播警报音；
- 测站并入 `_allStations`，参与阈值音效、震源推算、摇晃检知与历史回放；
- `active: false` 可让事件只展示、不进预警链路。

停用插件立刻停止。宿主总开关 `allowPluginAlerts=false` 可一键让全部插件退回只读。
