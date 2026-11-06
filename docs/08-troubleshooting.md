# 08 · 排错与 FAQ

## 排错顺序

1. **本地校验**：`python tools/mqe.py validate <插件目录>`，先把 `[ERROR]` 清零。
2. **看包内容**：`python tools/mqe.py info <包>.mqe`，确认 `plugin.json` 在根目录、  
   数据文件都在。
3. **看插件状态**：设置 → 插件 → 展开插件卡，看健康色、`message` 与 `lastError`，  
   再看「最近日志」。
4. **看数据源状态**：设置 → 数据源状态 → 「插件」分组，每个插件一行。
5. **手动触发**：插件卡里点「立即刷新」，排除轮询间隔等待。
6. **重载**：点右上角刷新图标（重新扫描并重载全部插件），清单改完必做。

---

## 常见错误

| 现象 / 错误信息                                      | 原因                      | 解决                                                         |
| ---------------------------------------------- | ----------------------- | ---------------------------------------------------------- |
| `包根目录缺少 plugin.json`                           | ZIP 里多包了一层目录            | 打包时把 `plugin.json` 放在 ZIP 根                                |
| `schema 必须是 1`                                 | 清单版本不对或漏写               | `"schema": 1`                                              |
| `id 非法`                                        | 用了大写、空格、中文或下划线开头        | 改成像 `com.example.myplugin`                                 |
| `未知能力 xxx`                                     | 拼错能力名                   | 对照 [09](09-api-matrix.md) 的 12 个值                          |
| `主机 xxx 不在 permissions.hosts 白名单内`             | URL 域名没授权               | 把域名加进 `permissions.hosts`                                  |
| `目标主机不在白名单内`（运行时）                              | 模板展开后 URL 变了            | 检查 `${config.*}` 的默认值                                      |
| `使用 process 通道必须显式设置 permissions.process=true` | 少写权限                    | 补 `"process": true`                                        |
| `process 通道仅在 Windows / macOS / Linux 桌面端可用`   | 在手机上装了子进程插件             | 改用 `http` / `websocket` / `file`                           |
| `transport.file 路径不安全`                         | 含 `..`、绝对路径、盘符          | 改成包内相对路径                                                   |
| `找不到数据文件`                                      | `file` 与实际文件名不一致/文件没打包  | 核对 `info` 输出的文件列表                                          |
| `响应超过 1 MB 上限`                                 | 接口返回太大                  | 分页或裁剪字段                                                    |
| `HTTP 404 / 500`                               | 接口问题                    | 先用浏览器/curl 单独验证接口                                          |
| `找不到 transport.command` / 子进程立刻退出              | PATH 里没有该命令             | 用 `python3` 或绝对路径                                          |
| 子进程「没数据」                                       | 输出被缓冲                   | Python 加 `flush=True`，Node 用 `process.stdout.write` + `\n` |
| 数据发出来了但界面没变化                                   | 没声明对应 `capabilities`    | 补上能力名并重载                                                   |
| 地图不画叠加层                                        | 缺 `permissions.overlay` | `"overlay": true`                                          |
| 音效没替换                                          | 缺 `permissions.sound`   | `"sound": true`                                            |
| 插件事件不响警报音                                      | **设计如此**                | 见 [05](05-security.md)，不是 bug                              |
| 状态一直 `idle` / `starting`                       | WS 还没推第一条、或 process 没输出 | 点「立即刷新」/ 检查 stdout                                         |
| 配置改了没生效                                        | 没点「保存并重启」               | 保存会重启 worker 并展开模板                                         |



---

## FAQ

**Q：为什么我的插件安装后是关闭的？**  
A：默认全部关闭，需要用户在设置页手动启用。这是安全设计，避免装上新包立刻联网。

**Q：改了 `data.json` 要重新打包吗？**  
A：用「安装 .mqe」装的包，解包目录才是运行时读的文件。直接改 `data/plugins/<id>/data.json`  
再点「立即刷新」即可；想让改动回到 `.mqe` 里，用「导出 .mqe」重新导出。

**Q：一个插件能同时用多个通道吗？**  
A：一个插件一个 `transport`。需要多路数据就装多个插件，或用 `process` / HTTP 服务  
在插件内部聚合后一次性输出。

**Q：插件之间会互相覆盖数据吗？**  
A：不会。所有 id 都加了 `<pluginId>:` 前缀，命名空间隔离。

**Q：能读取主程序里的官方事件吗？**  
A：不能直接读。`rules` 只作用于插件自己的数据。需要关联官方数据请在你自己的  
服务端做，再通过 HTTP 通道返回。

**Q：能触发系统通知 / 警报音吗？**  
A：不能，且这是刻意的。见 [05-security.md](05-security.md)。用 `notifications`  
能力在插件面板里呈现信息即可。

**Q：`.mqe` 能放二进制资源（wav/png）吗？**  
A：可以，`archive` 按字节解包。单个文件 ≤ 8 MB、整包 ≤ 32 MB。  
音效覆盖用 `sounds` 映射指向包内 wav。

**Q：Android / iOS 上哪些能力不可用？**  
A：只有 `process` 通道不可用；其余能力与 `file` / `http` / `websocket` 都可用。

**Q：数据目录在哪？**  
A：绿色版 = exe 同级 `data/`；MSI 安装版 = `%APPDATA%\Mquake\data`；  
Android = 应用支持目录。插件都在其下的 `plugins/`。

**Q：卸载会删用户配置吗？**  
A：会。卸载会删目录、`.mqe` 包与 `plugins_state.json` 里该插件的记录。

**Q：清单校验通过但应用仍不加载？**  
A：检查 `schema` 是否为 1、id 是否与目录名/其它插件冲突、以及是否点了  
「扫描目录」。设置页的日志会写明具体原因。

---

## 调试技巧

- 用 `file` 通道 + 一个手写 `data.json` 先跑通全链路，再换 HTTP / WS / process。
- 子进程先看 stderr 日志，十有八九是 `flush` 或 PATH 问题。
- `logs` 分区可以在报文里主动上报调试信息，会出现在插件卡的「最近日志」。
- 每次只加一个能力，逐项验证，避免一次引入多个变量。
