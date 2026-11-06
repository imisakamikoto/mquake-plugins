# 01 · 快速开始：从零到第一个 `.mqe`

全程不需要 Flutter / Dart，只要 Python 3.9+ 和一份文本编辑器。

## 步骤 1 · 生成脚手架

```bash
git clone https://github.com/imisakamikoto/mquake-plugins.git
cd mquake-plugins
python tools/mqe.py new com.example.myplugin
```

生成：

```
com.example.myplugin/
├── plugin.json     清单
├── data.json       数据
└── README.md
```

## 步骤 2 · 看懂清单

打开 `plugin.json`，脚手架默认给了两张信息卡和两个指标：

```json
{
  "schema": 1,
  "id": "com.example.myplugin",
  "name": "com.example.myplugin",
  "version": "1.0.0",
  "capabilities": ["cards", "metrics"],
  "permissions": {
    "hosts": [], "process": false, "alerts": false,
    "sound": false, "overlay": false
  },
  "transport": {
    "type": "file",
    "file": "data.json",
    "intervalSeconds": 60
  },
  "settings": [
    { "key": "city", "label": "城市", "type": "text", "default": "Tokyo" }
  ]
}
```

三个必记规则：

- `capabilities` 里没写的分区，数据会被**静默丢弃**（比如没写 `overlay` 就不画地图）；
- `permissions.hosts` 为空 = 不能联网；
- `transport.file` 只能是包内相对路径，不能 `../` 或绝对路径。

## 步骤 3 · 编辑数据

`data.json`：

```json
{
  "type": "snapshot",
  "cards": [
    { "id": "hello", "title": "Hello, Mquake!", "body": "第一条插件数据",
      "rows": [{"label": "城市", "value": "东京"}] }
  ],
  "metrics": [
    { "id": "demo", "label": "示例指标", "value": 42, "unit": "",
      "history": [38, 39, 41, 40, 42] }
  ]
}
```

`type: "snapshot"` 表示整包替换；想按 id 增量更新用 `"patch"`。

## 步骤 4 · 校验

```bash
python tools/mqe.py validate com.example.myplugin
# [OK] 校验通过
```

校验会同时检查 `plugin.json` 与 `transport.file` 指向的数据文件能否解析。
有 `[ERROR]` 必须修，`[WARN]` 建议修。

## 步骤 5 · 打包

```bash
python tools/mqe.py pack com.example.myplugin
# [OK] 已打包 com.example.myplugin.mqe（xxx 字节）
```

想指定输出路径：`python tools/mqe.py pack com.example.myplugin dist/my.mqe`。
反过来看包内容：`python tools/mqe.py info com.example.myplugin.mqe`。

## 步骤 6 · 安装到应用

两种方式，任选：

**A. 应用内安装（推荐）**
设置 → 插件 → 「安装 .mqe」→ 填写 `.mqe` 完整路径 → 安装。
包会被解到 `data/plugins/<id>/` 并自动启用。

**B. 直接放目录**
把 `.mqe` 复制到应用数据目录的 `plugins/` 下（或把解开的文件夹放进去），
然后在设置 → 插件点「扫描目录」。

> 数据目录位置：绿色版是 exe 同级的 `data/`；MSI 安装版是
> `%APPDATA%\Mquake\data`。设置页底部会显示实际路径。

## 步骤 7 · 启用与查看

- 在插件列表里打开开关；状态变成绿色 `ok` 且显示条数即成功；
- 设置 → 插件 底部「插件数据」能看到卡片与指标；
- 地图叠加、事件列表、测站会在主界面出现（需要对应能力与权限）；
- 设置 → 数据源状态 里每个插件占一行「插件」分组，显示健康度与错误原因。

## 步骤 8 · 迭代

改完 `plugin.json` 要**重新打包并重新安装**（或点「重新扫描并重载」）；
只改 `data.json` 的话，点插件卡里的「立即刷新」即可。

> 开发提速技巧：把插件**目录**直接放进 `data/plugins/`，编辑数据文件后点
> 「立即刷新」，完全跳过打包步骤。

## 下一步

- 想联网？看 [04-transports.md](04-transports.md) 的 HTTP 章节与 `examples/http-json/`。
- 想画地图？看 `examples/geojson-overlay/` 与 [03-protocol.md](03-protocol.md#overlays)。
- 想用自己的语言写逻辑？看 `examples/process-jsonl/`。
- 全部字段速查：[09-api-matrix.md](09-api-matrix.md)。
