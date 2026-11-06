# 03 · 数据报文协议

所有通道产出的都是**同一套 JSON 报文**。这一页是完整字段参考。

## 报文外壳

```json
{
  "type": "snapshot",
  "events": [], "stations": [], "overlays": [], "cards": [],
  "metrics": [], "tiles": [], "actions": [], "notifications": [],
  "rules": [], "logs": [], "sounds": {}, "theme": {}
}
```

- 所有顶层键**可选**、默认空。未声明对应 `capability` 的键会被忽略。
- `type`：`"snapshot"`（默认）或 `"patch"`。
  - `snapshot`：本次报文中**出现过的分区**先清空再写入；没出现的分区保留。
    这样插件可以分多条报文分别推送不同能力。
  - `patch`：按 `id`（`stations` 按 `code`）增量合并，不存在的追加、存在的替换。
- 也支持：
  - **顶层数组** → 当作多条 snapshot；
  - **JSONL** → 每行一条报文（子进程/WS 常用）；
  - **裸 GeoJSON FeatureCollection** → 自动转成 `overlays`；
  - `#` / `//` 开头的行在 JSONL 里视为注释跳过。
- 宽容解析：缺字段用默认值、数字可以是 `"12.3"` 这样的字符串、多字段忽略、
  单条坏数据只跳过该条并写一条插件日志。**不会**因为一条坏数据让整个插件失败。

---

## `events` · 自定义事件

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `id` | string | `""` | 必填语义上；会加 `<pluginId>:` 前缀 |
| `title` / `name` / `hypoCenter` | string | `未命名事件` | 标题 |
| `time` / `originTime` / `timestamp` | ISO8601 或毫秒 | null | 发生时刻 |
| `latitude` / `lat` | number | null | 纬度 |
| `longitude` / `lon` / `lng` | number | null | 经度 |
| `depth` / `depthKm` | number | null | 深度 km |
| `magnitude` / `mag` | number | null | 震级 |
| `shindo` | string | null | 震度文本，如 `"4"` / `"5-"` |
| `place` | string | `""` | 地名 |
| `description` / `body` | string | `""` | 说明 |
| `color` | 颜色 | null | 见「颜色」 |
| `url` / `link` | string | `""` | 链接 |
| `cancel` / `cancelled` | bool | false | 取消标记 |
| `isEew` | bool | false | **宿主强制为 false**，见安全说明 |

> ⚠️ 事件只会出现在列表里，**不会**触发提示音/全屏/TTS/系统通知。

## `stations` · 自定义测站

| 字段 | 类型 | 默认 |
| --- | --- | --- |
| `code` / `id` | string | `""`（会加命名空间前缀） |
| `name` | string | `自定义测站` |
| `latitude` / `lat` | number | `0` |
| `longitude` / `lon` / `lng` | number | `0` |
| `kind` | string | 自动填 `插件:<id>` |
| `pga` | number | null |
| `shindo` / `intensity` | number | null |
| `observedAt` / `time` | ISO8601 或毫秒 | null |
| `color` | 颜色 | null |

> 测站只参与地图绘制，不进入音效阈值判断与本地震源推算。

## `overlays` · 地图叠加

| 字段 | 类型 | 默认 | 说明 |
| --- | --- | --- | --- |
| `id` | string | 自动生成 | 唯一 |
| `shape` / `type` | string | `marker` | `marker` / `circle` / `polyline`(或`line`) / `polygon`(或`area`) / `text`(或`label`) |
| `points` / `coordinates` | array | `[]` | `[[lat,lon], …]` 或 `[{"lat":..,"lon":..}]` 或 `"lat,lon;lat,lon"` |
| `label` / `title` | string | `""` | 标注文字 |
| `color` | 颜色 | `#4488FF` | 描边/主色 |
| `fillColor` / `fill` | 颜色 | 半透明主色 | 填充色 |
| `strokeWidth` / `width` | number | `2` | 线宽 |
| `radius` | number | `8` | 圆/点半径（像素） |
| `tooltip` / `description` | string | `""` | 悬停提示 |

**GeoJSON 快捷方式**：直接把 `FeatureCollection` 作为数据文件（或报文）即可，
`Point` → marker、`LineString` → polyline、`Polygon` / `MultiPolygon` → polygon。
`properties` 里的 `name` / `color` / `stroke` / `fill` / `strokeWidth` / `radius` /
`description` 会被读成对应样式。注意 GeoJSON 坐标顺序是 `[lon, lat]`，宿主会自动翻转。

需要 `capabilities: ["overlay"]` **且** `permissions.overlay: true`。

## `cards` · 信息卡

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` / `title` | string | 必填语义上 |
| `subtitle` / `body` / `text` | string | 文本 |
| `rows` | array 或 object | `[{"label":"A","value":"1"}]` 或 `{"A":"1"}` |
| `color` | 颜色 | 强调色 |
| `icon` | int | 图标 codePoint（可选） |
| `url` / `link` | string | 「复制链接」按钮 |
| `priority` | int | 越大越靠前，默认 0 |

## `metrics` · 指标

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` / `label` | string | 标识 / 名称 |
| `value` | number | 当前值 |
| `unit` | string | 单位后缀 |
| `min` / `max` | number | 参考范围 |
| `history` | number[] | 迷你趋势图数据点 |
| `color` | 颜色 | 数值颜色 |
| `description` | string | 说明 |

## `tiles` · 自定义底图

| 字段 | 说明 |
| --- | --- |
| `id` / `name` | 标识 / 显示名 |
| `urlTemplate` / `url` | 含 `{z}` `{x}` `{y}` `{s}` 的模板 |
| `attribution` | 版权文字 |
| `maxZoom` | 默认 18 |
| `subdomains` | `{s}` 候选数组 |

## `actions` · 快捷动作

| 字段 | 说明 |
| --- | --- |
| `id` / `label` | 标识 / 按钮文字 |
| `kind` / `type` | `openUrl`（默认）/ `refresh` / `copy` / `custom` |
| `value` / `url` / `text` | 动作参数 |
| `icon` | 图标 codePoint |

## `notifications` · 应用内通知

| 字段 | 说明 |
| --- | --- |
| `id` / `title` | 标识 / 标题 |
| `body` / `text` | 正文 |
| `level` | `info`（默认）/ `warning` / `error` |
| `at` / `time` | 时间 |

> 只是插件面板里的日志型通知，**不会**弹系统通知、不会响铃、不会全屏。

## `rules` · 声明式规则

纯声明、不执行任意代码，只作用于插件自己的 `metrics` / `events`：

```json
{ "id": "hot", "target": "metrics", "op": "color",
  "field": "value", "comparator": ">=", "threshold": 40, "set": "#FF4444" }
```

| 字段 | 说明 |
| --- | --- |
| `target` | `metrics` / `events` |
| `op` | `keep`（按阈值过滤）/ `color`（命中上色）/ `derive`（命中指标派生一张卡片） |
| `field` | 字段名（当前用 `value` / `magnitude`） |
| `comparator` | `>=` `>` `<` `<=` `==` `!=` |
| `threshold` / `value` | 比较值 |
| `set` / `text` / `color` | 规则参数（颜色或派生卡片标题） |

## `logs` · 插件日志

```json
{ "level": "info", "message": "定时任务执行完成", "at": "2026-01-01T00:00:00Z" }
```

`level`：`debug` / `info` / `warning`(或`warn`) / `error`。最多保留 100 条，
只显示在插件管理页，不进 Sentry。子进程的 stderr 也会自动变成 `warning` 日志。

## `sounds` · 音效覆盖

```json
"sounds": { "quake_info": "assets/info.wav", "eew_alert": "assets/alert.wav" }
```

键为内置音效 id，值为**包内相对路径**。需要 `capabilities: ["sounds"]` +
`permissions.sound: true`。宿主会解析成解包目录下的绝对路径。

## `theme` · 配色覆盖

```json
"theme": { "accent": "#FF9933", "shindo.5-": "#FF6644" }
```

键为配色名，值为颜色字符串。需要 `capabilities: ["theme"]`。

## 颜色格式

| 写法 | 示例 |
| --- | --- |
| 6 位 hex | `"#FF9933"`（自动补不透明 alpha） |
| 8 位 hex | `"#80FF9933"`（AARRGGBB） |
| 不带 `#` | `"FF9933"` |
| 英文色名 | `red` `green` `blue` `yellow` `orange` `purple` `white` `black` `grey` `transparent` |
| 整数 | `4294946611`（0xAARRGGBB） |

## `webhook`

Webhook 由宿主在事件触发时向 `permissions.hosts` 白名单内的地址发 HTTP 回调。
声明 `capabilities: ["webhook"]` 只是启用该能力的标记，**目标主机必须在白名单内**，
否则运行时拒绝。详细行为见 [05-security.md](05-security.md)。

## 完整示例

[`examples/hello-static/data.json`](../examples/hello-static/data.json) 一条报文里
同时包含 8 个分区，可以直接复制改。
