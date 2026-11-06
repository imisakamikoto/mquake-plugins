# 09 · 速查表

## 能力 × 权限 × 数据键

| 能力 | 数据键 | 需要权限 | 展示位置 |
| --- | --- | --- | --- |
| `events` | `events` | — | 事件列表（不告警） |
| `stations` | `stations` | — | 地图测站（不参与音效/推算） |
| `overlay` | `overlays` | `permissions.overlay` | 地图叠加层 |
| `cards` | `cards` | — | 设置→插件 数据预览 |
| `metrics` | `metrics` | — | 设置→插件 数据预览 + 迷你图 |
| `tiles` | `tiles` | `permissions.hosts` | 自定义底图注册 |
| `sounds` | `sounds` | `permissions.sound` | 音效覆盖 |
| `theme` | `theme` | — | 配色覆盖 |
| `actions` | `actions` | — | 快捷动作 |
| `rules` | `rules` | — | 插件自身数据过滤/派生 |
| `webhook` | — | `permissions.hosts` | 事件回调 |
| `notifications` | `notifications` | — | 插件面板内通知 |

## 通道速查

| `type` | 必需 | 平台 | 典型间隔 |
| --- | --- | --- | --- |
| `file` | `file` | 全平台 | 60s |
| `http` | `url` + `hosts` | 全平台 | 30s |
| `websocket` | `url`(ws/wss) + `hosts` | 全平台 | 推送 |
| `process` | `command` + `process:true` | 桌面 | 10s |

## 报文顶层键

```
type        snapshot | patch
events[] stations[] overlays[] cards[] metrics[]
tiles[]   actions[] notifications[] rules[] logs[]
sounds{}  theme{}
```

## 字段别名（写哪个都认）

| 标准字段 | 别名 |
| --- | --- |
| `id` | `eventId` / `code` |
| `title` | `name` / `hypoCenter` |
| `time` | `originTime` / `timestamp` / `observedAt` |
| `latitude` | `lat` |
| `longitude` | `lon` / `lng` |
| `depth` | `depthKm` |
| `magnitude` | `mag` |
| `description` | `body` / `text` / `tooltip` |
| `url` | `link` |
| `points` | `coordinates` |
| `color` | `stroke` |
| `fillColor` | `fill` |
| `strokeWidth` | `width` |
| `cancel` | `cancelled` |
| `level`(日志) | `warn` → `warning` |

## 形状枚举

| `shape` 值 | 别名 | 最少点数 |
| --- | --- | --- |
| `marker`（默认） | — | 1 |
| `circle` | — | 1 |
| `polyline` | `line` | 2 |
| `polygon` | `area` | 3 |
| `text` | `label` | 1 |

## 颜色

`#RRGGBB` / `#AARRGGBB` / `RRGGBB` / 英文色名 / 0xAARRGGBB 整数。
色名：`red green blue yellow orange purple white black grey gray transparent`。

## 模板变量

`${config.<key>}` `${env.NAME}` `${plugin.dir}` `${now}` `${now.iso}`
可用于 `url` / `headers` / `body` / `command` / `args`。

## 规则

| 字段 | 值 |
| --- | --- |
| `target` | `metrics` / `events` |
| `op` | `keep` / `color` / `derive` |
| `comparator` | `>=` `>` `<` `<=` `==` `!=` |
| `threshold` | 数值 |
| `set` / `text` / `color` | 规则参数 |

## 限制一览

| 项 | 值 |
| --- | --- |
| 清单 schema | `1` |
| 报文 / 数据文件 | 1 MB |
| 解包总量 | 32 MB |
| 单文件 | 8 MB |
| 包内条目 | 512 |
| 轮询间隔下限 | 5 s |
| HTTP 超时 | 1–60 s |
| 日志保留 | 100 条/插件 |

## 校验错误码（CLI 退出码）

| 码 | 含义 |
| --- | --- |
| `0` | 成功 |
| `1` | 清单/数据校验未通过 |
| `2` | 参数错误、文件不存在、坏 ZIP、IO 失败 |

## 文件位置

| 内容 | 路径 |
| --- | --- |
| 插件根目录 | `<data>/plugins/` |
| 解包目录 | `<data>/plugins/<pluginId>/` |
| 清单 | `<data>/plugins/<pluginId>/plugin.json` |
| 状态/配置 | `<data>/plugins/plugins_state.json` |
| 分发包 | `<data>/plugins/<pluginId>.mqe` |
