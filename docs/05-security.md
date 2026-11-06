# 05 · 安全模型与沙箱

插件是**用户自己安装的代码/数据**，但地震预警客户端的告警链路必须保持可信。
下面是完整的安全边界，插件作者与集成者都应当了解。

## 1. 预警与测站链路（两道闸门）

| 通道 | 插件能否触碰 |
| --- | --- |
| 紧急地震速报警报音 / 预报音 / 更新音 | ✅ 需 `alerts` |
| 全屏紧急弹窗（Android） | ✅ 需 `alerts` |
| TTS 语音播报 | ✅ 需 `alerts` |
| 系统通知 / 通知中心 | ✅ 需 `alerts`；未授权只有插件面板内通知 |
| 本地震源推算 `HypoService` | ✅ 需 `alerts` |
| 实时震度 / PGA 阈值音效 | ✅ 需 `alerts` |
| 历史回放存档 `StationReplayStore` | ✅ 需 `alerts` |
| 事件列表（展示） | ✅ 始终 |
| 地图（测站 / 叠加层） | ✅ 始终显示；叠加层需 `overlay` |
| 设置 → 插件页的卡片 / 指标 / 日志 | ✅ |
| 数据源状态面板（健康度） | ✅ |

实现方式（**两道闸门**：清单 `permissions.alerts` + 宿主 `allowPluginAlerts`）：

1. 两者同时为真时，插件报文里 `isEew: true`、`active: true`、非 `cancel` 的事件
   会并入 `activeEew`，与官方 EEW 一起走 `_playEventSounds`；
2. 共用 `AudioService` 的报号去重记忆：报号递增触发更新音、预报升警报、
   `warnRegionCount` 显著增加补播警报音，规则与官方完全一致；
3. 插件测站并入 `_allStations`，参与阈值音效、震源推算、摇晃检知与历史回放；
   `kind` 用 `插件:<id>` 命名空间，噪声基线不与官方台站混淆；
4. 所有插件数据带 `插件:<插件名>` 来源标记、`plugin:<id>:` 事件 id 前缀，
   与官方事件的去重记忆隔离，界面可一眼区分；
5. 任一闸门为假 → 只读模式：事件只进列表、测站只在地图绘制。

> **结论：插件可以正常触发预警，但必须由插件作者在清单里显式申请，
> 用户在安装时可看到该权限。** 宿主总开关 `allowPluginAlerts=false` 可一键
> 把所有插件退回只读，无需逐个改清单。

### 授权示例

`plugin.json`：

```json
{
  "capabilities": ["events", "stations"],
  "permissions": { "alerts": true, "hosts": [], "process": false,
                   "sound": false, "overlay": false }
}
```

数据报文：

```json
{
  "type": "snapshot",
  "events": [{
    "eventId": "eew-001", "reportNum": 1, "title": "自定义速报", "isEew": true,
    "eewKind": "警報", "reportNum": 1, "active": true,
    "latitude": 35.6, "longitude": 139.7, "depth": 10,
    "magnitude": 6.8, "shindo": "5-", "maxEstimatedIntensity": 4.8,
    "place": "示例震源", "warnRegionCount": 7
  }],
  "stations": [{
    "code": "S1", "name": "自采集台站", "lat": 35.6, "lon": 139.7,
    "shindo": 4.2, "pga": 120
  }]
}
```

## 2. 权限（默认全关）

| 权限 | 默认 | 影响 |
| --- | --- | --- |
| `hosts: []` | 禁网 | HTTP / WS / Webhook 全部拒绝 |
| `process: false` | 禁止 | 子进程通道不可用 |
| `alerts: false` | 禁止 | 且宿主侧仍拒绝 |
| `sound: false` | 禁止 | `sounds` 分区被忽略 |
| `overlay: false` | 禁止 | `overlays` 分区被忽略 |

- 清单里**未声明**的能力，其数据分区在解析时直接丢弃（不是显示后再隐藏）。
- 主机白名单在**每次请求前**对模板展开后的实际 URL 校验，防止用
  `${config.url}` 绕过加载期检查。
- 白名单支持 `*.example.com` 后缀匹配；不匹配 `example.com.evil.com` 这类绕过。

## 3. `.mqe` 包安全

解包前/解包时的检查：

| 风险 | 防护 |
| --- | --- |
| Zip Slip 路径穿越 | 拒绝绝对路径、`..`、`C:` 盘符、反斜杠穿越、空路径段 |
| Zip 炸弹 | 解压总量 ≤ 32 MB，单文件 ≤ 8 MB，条目 ≤ 512 |
| 清单注入 | 清单在落盘**之前**校验；不合格不写任何文件 |
| 半包状态 | 先写 `.staging` 临时目录，全部成功后原子重命名 |
| 插件 id 冲突 | 同一 id 只加载第一个，后续跳过 |
| 重复安装 | 覆盖同名目录，状态与配置按 id 保留 |

清单校验还会拒绝：非法 id、未知能力/通道、缺失必需字段、未知设置类型、
空/重复 settings key、不安全的 `file` / `command` 路径、未授权主机、
`process` 未授权。

## 4. 运行时隔离

- **一个插件一个 worker**：独立 `http.Client`、独立定时器/订阅、独立 try/catch。
  插件超时、崩溃、输出垃圾都不会影响官方数据源或其它插件。
- **错误不终止**：单次失败记 `lastError`、错误计数与日志，下个周期继续重试。
- **WS 重连**：断开 5 秒后自动重连，避免忙循环。
- **能力二次过滤**：worker 合并数据按 `capabilities` 过滤一次，
  生成 `PluginSnapshot` 时再按 `permissions` 过滤一次。
- **命名空间**：所有数据 id 加 `<pluginId>:` 前缀，插件之间无法互相覆盖。
- **无任意代码执行**：`rules` 是声明式比较，不支持表达式求值、不支持 `eval`、
  不支持反射调用宿主 API。

## 5. 资源上限

| 项 | 限制 |
| --- | --- |
| 单次报文 | 1 MB |
| 静态数据文件 | 1 MB |
| `.mqe` 解包总量 | 32 MB |
| 单文件 | 8 MB |
| 包内文件数 | 512 |
| 轮询间隔 | ≥ 5 秒 |
| HTTP 超时 | 1–60 秒 |
| 日志条数 | 每插件环形保留 100 条 |

## 6. 给插件作者的合规建议

1. **只申请需要的权限**：能 `file` 就别 `http`，能本地就别联网。
2. **不要把密钥写进 `plugin.json`**：用 `${env.MY_TOKEN}` 从环境变量读，
   或用 `settings` 让用户在应用里填（值存在本地 `plugins_state.json`）。
3. **HTTPS / WSS**：生产接口务必用 TLS；`http://` 只适合本机调试。
4. **校验自己的输入**：插件若读取外部数据，自己做范围检查；宿主的宽容解析
   是为了不崩，不是数据可信保证。
5. **子进程别用 `shell=True`**：宿主已用 `runInShell: false` 启动，
   插件内部也不要拼接用户输入的 shell 命令。
6. **明确标注数据来源**：用 `description` / `name` 让用户知道这不是官方数据。

## 7. 给分发者的建议

- 分发前跑 `python tools/mqe.py validate <dir>`，并核对 `permissions.hosts`
  只包含你确实需要的域名。
- 在 README 里写清插件会访问哪些地址、是否启动子进程、是否持久化数据。
- 建议附上 `homepage` 与 `license`，方便用户追溯。
