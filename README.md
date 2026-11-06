# Mquake 插件开发套件（.mqe SDK）

用 **`.mqe`** 扩展「御坂防灾」的数据与界面：自定义事件、测站、地图叠加、信息卡、
指标曲线、瓦片底图、音效、主题配色、快捷动作、数据规则、Webhook 与应用内通知。

这是**独立、公开**的开发仓库：文档、JSON Schema、命令行工具、示例插件、模板都在这里，
不依赖主程序的私有代码，也不需要 Flutter / Dart 环境。

> 主程序仓库：[imisakamikoto/mquake2](https://github.com/imisakamikoto/mquake2)（私有）
> 插件文档仓库：本仓库（公开）

---

## 30 秒上手

```bash
# 1. 生成脚手架
python tools/mqe.py new com.example.myplugin

# 2. 编辑 com.example.myplugin/plugin.json 与 data.json
#    （改完可以直接看 examples/hello-static/）

# 3. 校验 + 打包
python tools/mqe.py validate com.example.myplugin
python tools/mqe.py pack com.example.myplugin        # → com.example.myplugin.mqe

# 4. 在应用里：设置 → 插件 → 安装 .mqe（或把文件放进 data/plugins/ 后点「扫描目录」）
```

`mqe.py` 只依赖 Python 3.9+ 标准库，Windows / macOS / Linux 都能跑。

---

## 为什么是「数据 + 声明」，不是「加载代码」

主程序是 Flutter AOT 编译的，**运行时无法动态加载 Dart 代码**（iOS / Android 也禁止
动态执行代码）。因此 `.mqe` 不装代码进主程序，而是：

| 你提供 | 宿主负责 |
| --- | --- |
| `plugin.json` 清单：能力、权限、通道、配置表单 | 解释清单、生成设置界面 |
| 数据：JSON / JSONL / GeoJSON | 解析、校验、限流、聚合、渲染 |
| 可选：独立脚本（Python/Node/Go/…） | 通过 **stdout JSONL 子进程** 或 HTTP/WS 与之通信 |

好处：插件**可以用任何语言写**、崩溃不会拖垮主程序、无需签名与审核即可本地使用；
代价：插件不能改主程序的 Widget 树，只能在约定的 12 类能力里发挥。

---

## 能力一览（12 类）

| 能力 | 作用 | 数据键 |
| --- | --- | --- |
| `events` | 自定义地震 / 情报事件；授权后可正常触发预警 | `events` |
| `stations` | 自定义测站；授权后可参与阈值音效与震源推算 | `stations` |
| `overlay` | 点 / 圆 / 线 / 面 / 文字标注（含裸 GeoJSON） | `overlays` |
| `cards` | 侧栏信息卡：标题、正文、键值行、链接、优先级 | `cards` |
| `metrics` | 数值指标 + 迷你趋势图 | `metrics` |
| `tiles` | 自定义瓦片底图模板 | `tiles` |
| `sounds` | 覆盖内置提示音（需 `permissions.sound`） | `sounds` |
| `theme` | 覆盖配色键 | `theme` |
| `actions` | 快捷动作按钮 | `actions` |
| `rules` | 声明式过滤 / 上色 / 派生规则 | `rules` |
| `webhook` | 事件触发时向白名单主机发 HTTP 回调 | — |
| `notifications` | 应用内通知（**不**触发系统通知/全屏/警报音） | `notifications` |

四种通道：`file`（静态文件）、`http`（轮询）、`websocket`（长连接推送）、
`process`（桌面端子进程 JSONL，任意语言）。

---

## 文档目录

| 文档 | 内容 |
| --- | --- |
| [docs/00-overview.md](docs/00-overview.md) | 架构、生命周期、数据流、设计取舍 |
| [docs/01-quickstart.md](docs/01-quickstart.md) | 从零到第一个 `.mqe`，含逐步截图说明 |
| [docs/02-manifest.md](docs/02-manifest.md) | `plugin.json` 全字段规范、settings、模板变量、mapping |
| [docs/03-protocol.md](docs/03-protocol.md) | 数据报文协议、12 类能力字段表、snapshot/patch、GeoJSON |
| [docs/04-transports.md](docs/04-transports.md) | 四种通道详解、子进程协议、重连与限流 |
| [docs/05-security.md](docs/05-security.md) | 沙箱、权限、路径穿越防护、告警隔离、资源上限 |
| [docs/06-cli.md](docs/06-cli.md) | `mqe.py` 命令参考、CI 集成 |
| [docs/07-examples.md](docs/07-examples.md) | 五个示例逐行讲解 |
| [docs/08-troubleshooting.md](docs/08-troubleshooting.md) | 排错清单、常见错误码、FAQ |
| [docs/09-api-matrix.md](docs/09-api-matrix.md) | 字段速查表与能力×权限矩阵 |
| [schema/plugin.schema.json](schema/plugin.schema.json) | JSON Schema（编辑器自动补全 / CI 校验） |

---

## 目录结构

```
.
├── README.md                  本文件
├── LICENSE                    MIT
├── docs/                      完整开发文档
├── schema/plugin.schema.json  清单 JSON Schema
├── tools/mqe.py               打包 / 校验 / 脚手架 CLI
├── templates/minimal/         最小可用模板
├── examples/
│   ├── hello-static/          静态数据，一次演示 8 类能力
│   ├── http-json/             HTTP 轮询 + 字段映射 + 配置模板（附 server.py）
│   ├── process-jsonl/         Python 子进程 stdout JSONL
│   ├── geojson-overlay/       裸 GeoJSON → 地图叠加
│   └── websocket/             WS 推送（附 server.py）
└── .github/workflows/validate.yml   CI 自动校验全部示例
```

## 重要约束（务必先读）

1. **预警能力按清单显式授权。** 默认未授权时插件事件只进列表、测站只参与地图显示；
   在 `plugin.json` 里设 `permissions.alerts: true` 后，插件 EEW 会**正常触发**
   提示音 / 通知 / 全屏 / TTS，插件测站会**完整参与**阈值音效、震源推算与历史回放。
   所有插件数据仍带 `插件:<名称>` 来源标记，界面可区分。
2. **网络访问必须白名单。** `permissions.hosts` 为空 = 完全不能联网；
   未列出的主机在运行时直接拒绝。
3. **进程通道仅桌面端**，且必须显式 `permissions.process: true`；移动端会被拒绝。
4. 单个报文 ≤ 1 MB、解包后总计 ≤ 32 MB、轮询间隔 ≥ 5 秒、文件数 ≤ 512。
5. 插件 id 会作为命名空间前缀加到所有数据 id 上，不同插件不会互相覆盖。

## 许可

MIT，见 [LICENSE](LICENSE)。示例插件可自由复制修改。
