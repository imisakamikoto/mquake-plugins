# 02 · 清单规范 `plugin.json`

完整机器可读定义见 [`schema/plugin.schema.json`](../schema/plugin.schema.json)。  
把它配到编辑器可获得自动补全与即时校验（VS Code 只需在文件头加  
`"$schema": "<URL to schema>"`，或装 JSON Schema 扩展按路径绑定）。

## 顶层字段

| 字段                     | 类型       | 必需 | 说明                                                 |
| ---------------------- | -------- | -- | -------------------------------------------------- |
| `schema`               | int      | ✅  | 固定 `1`。其它值一律拒绝加载。                                  |
| `id`                   | string   | ✅  | `^[a-z0-9][a-z0-9._-]{1,63}$`，全局唯一，决定解包目录名与数据命名空间。 |
| `name`                 | string   | ✅  | 设置页显示名。                                            |
| `version`              | string   | ✅  | 建议 `x.y.z`。                                        |
| `author`               | string   |    | 作者。                                                |
| `description`          | string   |    | 插件卡里的说明。                                           |
| `homepage` / `license` | string   |    | 元信息。                                               |
| `minAppVersion`        | string   |    | 最低宿主版本，留空不限制。                                      |
| `icon`                 | string   |    | 包内图标相对路径。                                          |
| `capabilities`         | string[] | ✅  | 见下表。未声明的分区数据会被丢弃。                                  |
| `permissions`          | object   |    | 默认全关，见「权限」。                                        |
| `transport`            | object   | ✅  | 数据通道，见 [04](04-transports.md)。                     |
| `settings`             | object[] |    | 用户可配置项，宿主自动生成表单。                                   |
| `mapping`              | object   |    | 任意 JSON → 标准字段的字段映射。                               |

## capabilities

| 值               | 权限依赖                  | 数据键             | 说明             |
| --------------- | --------------------- | --------------- | -------------- |
| `events`        | 触发预警需 `alerts`   | `events`        | 自定义事件；授权且 `isEew` 时进预警链路 |
| `stations`      | 参与活动需 `alerts`   | `stations`      | 自定义测站；授权后并入主测站流 |
| `overlay`       | `permissions.overlay` | `overlays`      | 点/圆/线/面/文字     |
| `cards`         | —                     | `cards`         | 信息卡            |
| `metrics`       | —                     | `metrics`       | 指标 + 趋势        |
| `tiles`         | `permissions.hosts`   | `tiles`         | 自定义瓦片模板        |
| `sounds`        | `permissions.sound`   | `sounds`        | 音效覆盖映射         |
| `theme`         | —                     | `theme`         | 配色键覆盖          |
| `actions`       | —                     | `actions`       | 快捷动作           |
| `rules`         | —                     | `rules`         | 声明式过滤/上色/派生    |
| `webhook`       | `permissions.hosts`   | —               | 事件触发回调         |
| `notifications` | —                     | `notifications` | 应用内通知（不触发系统通知） |

> 写错的能力名会被 `mqe validate` 报 `[ERROR] 未知能力`，宿主也会忽略它。

## permissions

```json
{
  "permissions": {
    "hosts": ["127.0.0.1", "localhost", "api.example.com", "*.example.org"],
    "process": false,
    "alerts": false,
    "sound": false,
    "overlay": true
  }
}
```

| 字段        | 默认      | 说明                                                             |
| --------- | ------- | -------------------------------------------------------------- |
| `hosts`   | `[]`    | HTTP/WS/Webhook 允许访问的主机名。精确匹配或 `*.` 后缀匹配，不区分大小写。**为空 = 完全禁网**。 |
| `process` | `false` | 允许 `process` 通道；仅 Windows/macOS/Linux 桌面端。                     |
| `alerts`  | `false` | 授予后插件 EEW 正常触发预警（音效/通知/全屏/TTS），插件测站参与阈值音效、震源推算与回放。宿主总开关 `allowPluginAlerts` 默认开。见 [05](05-security.md)。 |
| `sound`   | `false` | 允许 `sounds` 能力生效。                                              |
| `overlay` | `false` | 允许地图叠加生效。                                                      |

注意：`hosts` 校验发生在**每次请求前**（模板展开后的实际 URL），不是只在加载时。  
所以 `${config.url}` 这类模板也不能绕过白名单。

## transport

见 [04-transports.md](04-transports.md)。速查：

| `type`      | 必需字段                        | 平台  |
| ----------- | --------------------------- | --- |
| `file`      | `file`                      | 全平台 |
| `http`      | `url` + `hosts` 白名单         | 全平台 |
| `websocket` | `url`（ws/wss）+ `hosts`      | 全平台 |
| `process`   | `command` + `process: true` | 仅桌面 |

公共字段：`intervalSeconds`（默认 60，**下限 5**）、`timeoutSeconds`（默认 8，  
HTTP 上限 60）。

## settings（自动生成表单）

```json
{
  "settings": [
    { "key": "city",     "label": "城市",   "type": "text",   "default": "东京",
      "description": "用于查询参数" },
    { "key": "refresh",  "label": "刷新间隔", "type": "number", "default": 30 },
    { "key": "debug",    "label": "调试",   "type": "toggle", "default": false },
    { "key": "region",   "label": "区域",   "type": "select",
      "options": ["kanto", "kansai", "tohoku"], "default": "kanto" }
  ]
}
```

| 字段            | 说明                                       |
| ------------- | ---------------------------------------- |
| `key`         | 唯一、非空；模板里用 `${config.<key>}` 引用。         |
| `label`       | 表单标签。                                    |
| `type`        | `text` / `number` / `toggle` / `select`。 |
| `default`     | 默认值，类型应与 `type` 一致。                      |
| `options`     | `select` 必填。                             |
| `description` | 输入框下方的帮助文字。                              |

用户在设置页改完点「保存并重启」，运行时会**重启该插件 worker**，让 URL / headers /  
命令行参数里的模板变量立刻生效。配置存于 `plugins_state.json`。

## 模板变量

可用于 `transport.url` / `headers` / `body` / `command` / `args`：

| 变量                | 展开为                   |
| ----------------- | --------------------- |
| `${config.<key>}` | 用户配置值（未设置取 `default`） |
| `${env.NAME}`     | 进程环境变量                |
| `${plugin.dir}`   | 插件解包后的绝对目录            |
| `${now}`          | UTC 毫秒时间戳             |
| `${now.iso}`      | UTC ISO-8601 字符串      |

示例：

```json
{
  "url": "https://api.example.com/v1/data?city=${config.city}&t=${now}",
  "headers": { "Authorization": "Bearer ${env.MY_TOKEN}" }
}
```

未知变量展开为空字符串，不会报错，也不会把 `${...}` 原样发出去。

## mapping（字段映射）

当你的接口返回的不是标准结构时，用 `mapping` 免写转换代码：

```json
{
  "mapping": {
    "events": {
      "path": "data.items",
      "fields": {
        "id": "event_id",
        "title": "name",
        "latitude": "lat",
        "longitude": "lon",
        "magnitude": "mag",
        "time": "occurred_at"
      }
    }
  }
}
```

- `path`：点路径，支持 `a.b[0].c` 与 `$` 前缀；省略时依次尝试顶层同名数组、  
  `data.<section>`。
- `fields`：**目标字段名 → 源数据点路径**。值也可以是常量。
- 键名就是能力对应的数据键（`events` / `stations` / `overlays` / …）。

> 提示：映射是可选的。如果接口直接返回标准报文（顶层 `events` / `cards` / …），  
> 完全不用写 `mapping`。

## 完整示例

见 [`examples/http-json/plugin.json`](../examples/http-json/plugin.json)，  
它同时用了白名单、模板变量、select 配置和字段映射。

