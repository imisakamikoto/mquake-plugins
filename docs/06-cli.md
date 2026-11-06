# 06 · `mqe.py` 命令行工具

位置：`tools/mqe.py`。**仅依赖 Python 3.9+ 标准库**，无需 pip install。

```bash
python tools/mqe.py --help
```

| 命令 | 作用 |
| --- | --- |
| `new <id> [目录]` | 生成插件脚手架 |
| `validate <目录或.mqe>` | 校验清单 + 数据文件 / 包结构 |
| `pack <目录> [输出.mqe]` | 打包成 `.mqe` |
| `unpack <包.mqe> [目录]` | 解包到目录 |
| `info <包.mqe>` | 打印清单摘要与文件列表 |

退出码：`0` 成功 / `1` 校验未通过 / `2` 参数或 IO 错误。

---

## `new`

```bash
python tools/mqe.py new com.example.myplugin
python tools/mqe.py new com.example.myplugin ./my-plugin
```

生成 `plugin.json`（`cards` + `metrics` 能力、`file` 通道、一个 text 设置项）、
`data.json`、`README.md`。id 必须符合 `^[a-z0-9][a-z0-9._-]{1,63}$`。

## `validate`

```bash
python tools/mqe.py validate examples/hello-static
python tools/mqe.py validate dist/myplugin.mqe
```

对目录：校验清单，并检查 `transport.file` 指向的文件存在且是合法 JSON。
对 `.mqe`：先做包结构检查（路径穿越、体积、条目数、根目录 `plugin.json`），
再校验清单。

输出所有错误与警告，例如：

```
[WARN] version 建议用语义化版本 x.y.z
[ERROR] 主机 api.evil.com 不在 permissions.hosts 白名单内
[FAIL] 校验未通过
```

`[WARN]` 不阻止打包，`[ERROR]` 会。

## `pack`

```bash
python tools/mqe.py pack examples/hello-static
# → examples/hello-static.mqe  （默认输出到目录的同级）
python tools/mqe.py pack examples/hello-static dist/hello.mqe
```

- 打包前自动 `validate`，**不通过就拒绝打包**。
- 自动跳过隐藏文件、`.git`、`__pycache__`、`node_modules`、已有 `.mqe`。
- 用 ZIP_DEFLATED（level 6），文件名统一 `/` 分隔。

## `unpack` / `info`

```bash
python tools/mqe.py info dist/hello.mqe
python tools/mqe.py unpack dist/hello.mqe ./inspect
```

`info` 输出 id / name / version / schema / capabilities / transport / 文件列表。
`unpack` 会先做路径安全检查再解包。

---

## CI 集成

仓库自带 [`.github/workflows/validate.yml`](../.github/workflows/validate.yml)，
对每个 `examples/*/` 与 `templates/*/` 跑 `validate`。你自己的插件仓库可以直接复用：

```yaml
name: validate
on: [push, pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: python tools/mqe.py validate my-plugin
      - run: python tools/mqe.py pack my-plugin
```

## 用 JSON Schema 做编辑器补全

[`schema/plugin.schema.json`](../schema/plugin.schema.json) 是 draft 2020-12。
VS Code 可以在 `settings.json` 里绑定：

```json
"json.schemas": [
  { "fileMatch": ["**/plugin.json"], "url": "./schema/plugin.schema.json" }
]
```

## 与宿主校验的关系

`mqe.py` 的校验规则与宿主 `PluginManifest.validate()` **保持一致**
（同一套字段、同一套错误文案口径），所以本地通过 = 应用能加载。
但仍要注意平台差异：`process` 通道在桌面端才可用，CLI 不会替你判断运行平台。
